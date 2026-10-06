"""Offline preparation regressions: staged reads must match each platform's XML."""
import socket
import os
import shutil
import subprocess
import sys
import types
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bin'))
try:
    import nameparser
except ImportError:
    stub = types.ModuleType('nameparser')
    stub.HumanName = object
    sys.modules['nameparser'] = stub

import submission_prep


CONFIG = {
    'NCBI_ftp_host': 'unused', 'NCBI_username': 'unused', 'NCBI_password': 'unused',
    'NCBI_Namespace': 'test', 'Role': 'owner', 'Type': 'institute',
    'Submitting_Org': 'Test lab', 'Email': 'test@example.invalid',
    'Submitter': {'Name': {'First': 'Test', 'Last': 'User'}},
}


@pytest.mark.parametrize('platforms', [('illumina',), ('nanopore',), ('illumina', 'nanopore')])
def test_preparation_matches_platform_reads_and_metadata(tmp_path, platforms):
    # Both metadata sets are deliberately present even for one-platform inputs.
    # Read selection must not accidentally select the first metadata platform.
    metadata = pd.DataFrame([{
        'sample_name': '001', 'ncbi-spuid': 'bio001', 'ncbi-spuid-sra': 'sra001',
        'ncbi-bioproject': 'PRJNA123', 'illumina_sequencing_instrument': 'MiSeq',
        'illumina_library_layout': 'paired', 'nanopore_sequencing_instrument': 'MinION',
        'nanopore_library_layout': 'single',
    }])
    metadata_file = tmp_path / 'batch_1.tsv'
    metadata.to_csv(metadata_file, sep='\t', index=False)
    args = ['sample_id=001']
    expected = {}
    for platform in platforms:
        source_keys = [('fq1', 'R1'), ('fq2', 'R2')] if platform == 'illumina' else [('nanopore', 'nanopore')]
        expected[platform] = {}
        for key, label in source_keys:
            source = tmp_path / (key + '.fastq.gz')
            source.write_bytes(key.encode())
            args.append(f'{key}={source}')
            expected[platform][f'001_{label}.fastq.gz'] = source
    params = {
        'outdir': str(tmp_path / 'batch_1'), 'metadata_file': str(metadata_file),
        'identifier': 'test', 'test': True, 'sample': [','.join(args)],
        'species': 'bacteria', 'biosample': False, 'sra': True, 'genbank': False,
        'submission_mode': 'ftp',
    }
    with patch.object(submission_prep, 'GetParams') as get_params, \
         patch.object(submission_prep.SubmissionConfigParser, 'load_config', return_value=CONFIG), \
         patch.object(submission_prep, 'setup_logging'), \
         patch.object(socket.socket, 'connect', side_effect=AssertionError('Network prohibited')):
        get_params.return_value.parameters = params
        submission_prep.main_prepare()
    for platform in platforms:
        folder = Path(params['outdir']) / 'sra'
        if len(platforms) > 1:
            folder /= platform
        root = ET.parse(folder / 'submission.xml').getroot()
        actions = root.findall('Action/AddFiles')
        assert len(actions) == 1
        action = actions[0]
        assert [f.get('file_path') for f in action.findall('File')] == list(expected[platform])
        assert action.find("Attribute[@name='instrument_model']").text == ('MiSeq' if platform == 'illumina' else 'MinION')
        assert action.find("Attribute[@name='library_layout']").text == ('paired' if platform == 'illumina' else 'single')
        assert action.find('Identifier/SPUID').text == 'sra001'
        assert (folder / 'submit.ready').exists()
        staged_reads = {path.name for path in folder.glob('*.fastq.gz')}
        assert staged_reads == set(expected[platform])
        for name, source in expected[platform].items():
            staged = folder / name
            assert staged.is_symlink()
            assert staged.resolve() == source
            assert staged.read_bytes() == source.read_bytes()


def test_sra_without_reads_fails_before_writing_trigger(tmp_path):
    metadata_file = tmp_path / 'batch_1.tsv'
    metadata_file.write_text('sample_name\n001\n')
    params = {
        'outdir': str(tmp_path / 'batch_1'), 'metadata_file': str(metadata_file),
        'identifier': 'test', 'test': True, 'sample': ['sample_id=001'],
        'species': 'bacteria', 'biosample': False, 'sra': True, 'genbank': False,
        'submission_mode': 'ftp',
    }
    with patch.object(submission_prep, 'GetParams') as get_params, \
         patch.object(submission_prep.SubmissionConfigParser, 'load_config', return_value=CONFIG), \
         patch.object(submission_prep, 'setup_logging'):
        get_params.return_value.parameters = params
        with pytest.raises(ValueError, match='no paired Illumina or Nanopore reads'):
            submission_prep.main_prepare()
    assert not list(tmp_path.rglob('submit.ready'))


@pytest.mark.skipif(os.environ.get('RUN_NEXTFLOW_TESTS') != '1', reason='Set RUN_NEXTFLOW_TESTS=1')
def test_nextflow_prep_passes_nanopore_reads(tmp_path, install_offline_scripts):
    executable = shutil.which('nextflow')
    if not executable:
        pytest.skip('Nextflow is not installed')
    repo = Path(__file__).resolve().parents[1]
    install_offline_scripts('submission_prep.py')
    (tmp_path / 'config.yaml').write_text(yaml.safe_dump(CONFIG))
    (tmp_path / 'reads.fastq.gz').write_bytes(b'local nanopore fixture')
    pd.DataFrame([{'sample_name': '001', 'ncbi-spuid': 'bio001', 'ncbi-spuid-sra': 'sra001',
                   'ncbi-bioproject': 'PRJNA123', 'nanopore_sequencing_instrument': 'MinION',
                   'nanopore_library_layout': 'single'}]).to_csv(tmp_path / 'batch_1.tsv', sep='\t', index=False)
    (tmp_path / 'nextflow.config').write_text('''params {
 env_yml = 'unused'
 prod_submission = false
 send_submission_email = false
 dry_run = true
 biosample_pkg = null
 strip_pub_block = false
 sbt = null
 completeness_min_coverage = null
 metadata_basename = 'demo'
 organism_type = 'bacteria'
 mol_type = 'genomic'
 submission_mode = 'ftp'
 genome_representation = 'Full'
 expected_final_version = 'Yes'
}
''')
    (tmp_path / 'main.nf').write_text('''include { PREP_SUBMISSION } from '@ROOT@/modules/local/prep_submission/main'
workflow {
 PREP_SUBMISSION(Channel.of(tuple([batch_id: 'batch_1'], [[meta: [sample_id: '001'], nanopore: file('reads.fastq.gz')]], ['sra'])), file('batch_1.tsv'), file('config.yaml'))
}
'''.replace('@ROOT@', str(repo)))
    result = subprocess.run([executable, 'run', 'main.nf', '-ansi-log', 'false'], cwd=tmp_path,
                            capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    xml_paths = list((tmp_path / 'work').glob('*/*/batch_1/sra/submission.xml'))
    assert len(xml_paths) == 1
    action = ET.parse(xml_paths[0]).getroot().find('Action/AddFiles')
    assert [el.get('file_path') for el in action.findall('File')] == ['001_nanopore.fastq.gz']
    assert action.find("Attribute[@name='instrument_model']").text == 'MinION'
    assert (xml_paths[0].parent / '001_nanopore.fastq.gz').read_bytes() == b'local nanopore fixture'
