"""Exercise real reporting modules without containers or NCBI access."""
import os
from pathlib import Path
import shutil
import subprocess

import pandas as pd
import pytest


@pytest.mark.skipif(os.environ.get('RUN_NEXTFLOW_TESTS') != '1', reason='Set RUN_NEXTFLOW_TESTS=1')
def test_reporting_modules_join_by_metadata_identifiers(tmp_path, install_offline_scripts):
    executable = shutil.which('nextflow')
    if not executable:
        pytest.skip('Nextflow is not installed')
    repo = Path(__file__).resolve().parents[1]
    install_offline_scripts('aggregate_reports.py', 'join_accessions_with_metadata.py')
    pd.DataFrame([
        {'sample_name': 'A', 'ncbi-spuid': 'BioA', 'ncbi-spuid-sra': 'Reads-X', 'biosample_accession': 'SAMN1'},
        {'sample_name': 'B', 'ncbi-spuid': 'BioB', 'ncbi-spuid-sra': 'Reads-Y', 'biosample_accession': ''},
    ]).to_csv(tmp_path / 'metadata.tsv', sep='\t', index=False)
    # B is the only newly created BioSample; neither SRA identifier is derived
    # from the BioSample identifier. The basename must not classify the database.
    pd.DataFrame([
        {'spuid': 'BioB', 'biosample_status': 'processed-ok', 'biosample_accession': 'SAMN2',
         'tracking_location': '/sra_metadata_batch_1_biosample'},
        {'spuid': 'Reads-Y', 'sra_status': 'processed-ok', 'sra_accession': 'SRR2',
         'tracking_location': '/sra_metadata_batch_1_sra'},
        {'spuid': 'Reads-X', 'sra_status': 'processed-ok', 'sra_accession': 'SRR3',
         'tracking_location': '/sra_metadata_batch_1_sra_nanopore'},
        {'spuid': 'Reads-X', 'sra_status': 'processed-ok', 'sra_accession': 'SRR1',
         'tracking_location': '/sra_metadata_batch_1_sra'},
    ]).fillna('').to_csv(tmp_path / 'batch_1.csv', index=False)
    (tmp_path / 'nextflow.config').write_text('''params.env_yml = 'unused'
params.metadata_basename = 'sra_metadata'
process.publishDir = [path: 'results', mode: 'copy']
''')
    (tmp_path / 'main.nf').write_text(f'''include {{ AGGREGATE_REPORTS }} from '{repo}/modules/local/aggregate_reports/main'
include {{ JOIN_ACCESSIONS_WITH_METADATA }} from '{repo}/modules/local/join_accessions_with_metadata/main'
workflow {{
 metadata = Channel.value(file('metadata.tsv'))
 AGGREGATE_REPORTS(Channel.value([file('batch_1.csv')]), metadata)
 JOIN_ACCESSIONS_WITH_METADATA(metadata, AGGREGATE_REPORTS.out.submission_report)
}}
''')
    result = subprocess.run([executable, 'run', 'main.nf', '-ansi-log', 'false'],
                            cwd=tmp_path, capture_output=True, text=True, timeout=120)
    assert result.returncode == 0, result.stdout + result.stderr
    merged = pd.read_excel(tmp_path / 'results/sra_metadata_updated.xlsx', header=1, dtype=str)
    assert len(merged) == 2
    assert merged['ncbi-spuid'].is_unique
    actual = merged.set_index('ncbi-spuid')[['biosample_accession', 'sra_accession']].to_dict('index')
    assert actual == {
        'BioA': {'biosample_accession': 'SAMN1', 'sra_accession': 'SRR1;SRR3'},
        'BioB': {'biosample_accession': 'SAMN2', 'sra_accession': 'SRR2'},
    }
