"""Exercise the report XML-to-Excel boundary without any remote service."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import types
import xml.etree.ElementTree as ET

import pandas as pd
import pytest

BIN = Path(__file__).resolve().parents[1] / 'bin'


@pytest.fixture
def helper(monkeypatch):
    monkeypatch.syspath_prepend(str(BIN))
    # Report parsing does not use author-name parsing. Keep this integration
    # test usable in the same minimal environment as the existing offline tests.
    try:
        import nameparser  # noqa: F401
    except ImportError:
        unused = types.ModuleType('nameparser')

        def unexpected_author_parse(*args, **kwargs):
            raise AssertionError('Report parsing must not invoke author-name parsing')

        unused.HumanName = unexpected_author_parse
        monkeypatch.setitem(sys.modules, 'nameparser', unused)
    spec = importlib.util.spec_from_file_location('report_export_helper', BIN / 'submission_helper.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def no_connection(*args, **kwargs):
        raise AssertionError('XML export tests must not connect to NCBI')

    monkeypatch.setattr(module.FTPClient, 'connect', no_connection)
    monkeypatch.setattr(module.SFTPClient, 'connect', no_connection)
    return module


def write_report(path, database, records):
    """Records contain submission SPUID, accession, and optional message text."""
    root = ET.Element('SubmissionStatus', status='processed-ok', submission_id=f'SUB_{database}')
    tracking = ET.SubElement(root, 'Tracking')
    ET.SubElement(tracking, 'SubmissionLocation').text = (
        f'submit/Production/sra_biosample_metadata_batch_1_{database.lower()}'
    )
    for index, (spuid, accession, message) in enumerate(records, start=1):
        action = ET.SubElement(root, 'Action', action_id=str(index),
                               target_db=database, status='processed-ok')
        response = ET.SubElement(action, 'Response')
        ET.SubElement(response, 'Message').text = message
        ET.SubElement(response, 'Object', spuid=spuid, accession=accession,
                      spuid_namespace='test-lab', object_id=str(index))
    ET.ElementTree(root).write(path, encoding='utf-8', xml_declaration=True)
    return path


@pytest.mark.parametrize('message,expected', [(None, ''), ('   Accepted sample   ', 'Accepted sample')])
def test_real_parser_handles_empty_and_normal_message(helper, tmp_path, message, expected):
    xml = write_report(tmp_path / 'report.xml', 'BioSample', [('001', 'SAMN1001', message)])
    if message is None:
        assert '<Message />' in xml.read_text()
    parsed = helper.parse_report_xml_to_df(xml)
    assert parsed.iloc[0]['biosample_message'] == expected
    assert parsed.iloc[0]['spuid'] == '001'
    assert parsed.iloc[0]['biosample_accession'] == 'SAMN1001'


def test_xml_reports_export_one_metadata_row_per_sample(helper, tmp_path):
    meta = pd.DataFrame([
        {'sample_name': '0001', 'ncbi-spuid': '001', 'ncbi-spuid-sra': 'library-red',
         'biosample_accession': 'SAMN1001'},
        {'sample_name': '0002', 'ncbi-spuid': '002', 'ncbi-spuid-sra': 'run-blue',
         'biosample_accession': ''},
        {'sample_name': 'CaseThird', 'ncbi-spuid': 'CaseID', 'ncbi-spuid-sra': 'third-read',
         'biosample_accession': ''},
    ])
    metadata_path = tmp_path / 'metadata.tsv'
    meta.to_csv(metadata_path, sep='\t', index=False)
    # BioSample intentionally omits an existing accession, SRA omits one sample,
    # and report order differs from metadata. Two SRA runs share one SPUID.
    biosample = write_report(tmp_path / 'biosample.xml', 'BioSample', [
        ('CaseID', 'SAMN1003', ' Accepted third sample '),
        ('002', 'SAMN1002', None),
    ])
    sra = write_report(tmp_path / 'sra.xml', 'SRA', [
        ('run-blue', 'SRR2002', 'Accepted blue reads'),
        ('library-red', 'SRR2003', None),
        ('library-red', 'SRR2001', 'Accepted red reads'),
    ])
    helper.parse_and_save_reports({'biosample': [biosample], 'sra': [sra]}, tmp_path, 'batch_1')
    batch_path = tmp_path / 'batch_1.csv'
    parsed = pd.read_csv(batch_path, dtype=str, keep_default_na=False)
    assert len(parsed) == 5
    assert 'target_db' not in parsed.columns  # Preserve the established CSV contract.
    assert parsed.loc[parsed.spuid == '002', 'biosample_message'].tolist() == ['']
    assert parsed.loc[parsed.spuid == 'CaseID', 'biosample_message'].tolist() == ['Accepted third sample']

    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    subprocess.run([sys.executable, str(BIN / 'aggregate_reports.py'), '--metadata_tsv',
                    str(metadata_path), str(batch_path)], cwd=tmp_path, env=env, check=True)
    detailed_path = tmp_path / 'submission_report.csv'
    detailed = pd.read_csv(detailed_path, dtype=str, keep_default_na=False)
    assert detailed.loc[detailed.spuid == '002', 'sra_accession'].tolist() == ['SRR2002']
    assert detailed.loc[detailed.spuid == '001', 'sra_accession'].tolist() == ['SRR2003', 'SRR2001']
    assert detailed.loc[detailed.spuid == 'CaseID', 'sra_accession'].tolist() == ['']

    output = tmp_path / 'accessions.xlsx'
    subprocess.run([sys.executable, str(BIN / 'join_accessions_with_metadata.py'), '--metadata_tsv',
                    str(metadata_path), '--submission_report', str(detailed_path),
                    '--output', str(output)], cwd=tmp_path, env=env, check=True)
    workbook = pd.read_excel(output, header=1, dtype=str, keep_default_na=False)
    assert workbook['sample_name'].tolist() == ['0001', '0002', 'CaseThird']
    assert workbook['ncbi-spuid'].tolist() == ['001', '002', 'CaseID']
    assert workbook['ncbi-spuid'].is_unique
    assert workbook['biosample_accession'].tolist() == ['SAMN1001', 'SAMN1002', 'SAMN1003']
    assert workbook['sra_accession'].tolist() == ['SRR2001;SRR2003', 'SRR2002', '']
    assert not any(column.endswith(('_x', '_y', '_reported')) for column in workbook.columns)
