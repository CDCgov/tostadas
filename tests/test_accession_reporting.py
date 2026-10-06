"""Offline regression tests for identifier-based accession reporting."""
import importlib.util
from pathlib import Path
import subprocess
import sys

import pandas as pd
import pytest

BIN = Path(__file__).resolve().parents[1] / 'bin'


def load(name):
    spec = importlib.util.spec_from_file_location(name, BIN / f'{name}.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


aggregate = load('aggregate_reports')
join = load('join_accessions_with_metadata')


def metadata():
    return pd.DataFrame([
        {'sample_name': 'first', 'ncbi-spuid': '001', 'ncbi-spuid-sra': 'arbitrary-read-id'},
        {'sample_name': 'second', 'ncbi-spuid': 'MixedCase', 'ncbi-spuid-sra': 'other-library'},
    ])


def report(db, spuid, accession, path='sra_biosample_metadata_batch_1'):
    return {'spuid': spuid, f'{db}_status': 'processed-ok', f'{db}_accession': accession,
            'submission_id': 'SUB123', 'tracking_location': f'{path}_{db}'}


def combine(tmp_path, rows, meta=None):
    path = tmp_path / 'batch_1.csv'
    pd.DataFrame(rows).to_csv(path, index=False)
    return aggregate.aggregate_reports([path], metadata() if meta is None else meta)


def test_reordered_reports_map_arbitrary_sra_identifiers(tmp_path):
    result = combine(tmp_path, [report('biosample', '001', 'SAMN1'),
                               report('biosample', 'MixedCase', 'SAMN2'),
                               report('sra', 'other-library', 'SRR2'),
                               report('sra', 'arbitrary-read-id', 'SRR1')])
    assert result[['spuid', 'biosample_accession', 'sra_accession']].values.tolist() == [
        ['001', 'SAMN1', 'SRR1'], ['MixedCase', 'SAMN2', 'SRR2']]


def test_existing_biosample_does_not_shift_sra_pairing(tmp_path):
    meta = metadata()
    meta['biosample_accession'] = ['SAMN1', '']
    result = combine(tmp_path, [report('biosample', 'MixedCase', 'SAMN2'),
                               report('sra', 'arbitrary-read-id', 'SRR1'),
                               report('sra', 'other-library', 'SRR2')], meta)
    merged = join.merge_accessions(meta, result)
    assert merged[['sample_name', 'biosample_accession', 'sra_accession']].values.tolist() == [
        ['first', 'SAMN1', 'SRR1'], ['second', 'SAMN2', 'SRR2']]
    assert not any(col.endswith(('_x', '_y', '_reported')) for col in merged)


def test_filename_database_words_do_not_classify_rows(tmp_path):
    result = combine(tmp_path, [report('biosample', '001', 'SAMN1'),
                               report('sra', 'arbitrary-read-id', 'SRR1')])
    assert len(result) == 1
    assert result.iloc[0]['sra_accession'] == 'SRR1'


def test_multiple_sra_runs_preserved(tmp_path):
    result = combine(tmp_path, [report('biosample', '001', 'SAMN1'),
                               report('sra', 'arbitrary-read-id', 'SRR1'),
                               report('sra', 'arbitrary-read-id', 'SRR2')])
    merged = join.merge_accessions(metadata(), result)
    assert merged[merged.sample_name == 'first']['sra_accession'].tolist() == ['SRR1;SRR2']
    assert merged['ncbi-spuid'].is_unique
    assert len(merged) == len(metadata())
    assert len(result) == 2
    assert len(merged[merged.sample_name == 'second']) == 1


@pytest.mark.parametrize('spuid', ['', 'unknown', 'ARBITRARY-READ-ID'])
def test_missing_unknown_or_case_mismatched_identifier_is_not_guessed(tmp_path, spuid):
    row = report('sra', spuid, '')
    row['sra_status'] = 'processed-error'
    with pytest.raises(ValueError, match='no unique metadata match'):
        combine(tmp_path, [row])


def test_duplicate_metadata_sra_identifier_rejected(tmp_path):
    meta = metadata()
    meta['ncbi-spuid-sra'] = 'same'
    with pytest.raises(ValueError, match='Duplicate SRA identifier'):
        combine(tmp_path, [report('sra', 'same', 'SRR1')], meta)


def test_existing_accessions_survive_missing_report():
    meta = metadata()
    meta['biosample_accession'] = ['SAMN1', 'SAMN2']
    meta['sra_accession'] = ['SRR1', '']
    empty = aggregate.aggregate_reports([], meta)
    merged = join.merge_accessions(meta, empty)
    pd.testing.assert_frame_equal(merged, meta)


@pytest.mark.parametrize('column,existing,reported', [
    ('biosample_accession', 'SAMN1', 'SAMN2'), ('sra_accession', 'SRR1', 'SRR2')])
def test_existing_conflicting_accession_is_not_overwritten(column, existing, reported):
    meta = metadata()
    meta[column] = [existing, '']
    row = {'spuid': '001', 'biosample_accession': '', 'sra_accession': ''}
    row[column] = reported
    with pytest.raises(ValueError, match='conflicts with report'):
        join.merge_accessions(meta, pd.DataFrame([row]))


def test_identical_existing_accession_and_original_case_preserved():
    meta = metadata()
    meta['biosample_accession'] = ['', 'SAMN2']
    rows = pd.DataFrame([{'spuid': 'MixedCase', 'biosample_accession': 'SAMN2', 'sra_accession': 'SRR2'}])
    merged = join.merge_accessions(meta, rows)
    assert merged['ncbi-spuid'].tolist() == ['001', 'MixedCase']
    assert merged['biosample_accession'].tolist() == ['', 'SAMN2']


def test_conflicting_biosample_report_accessions_rejected():
    rows = pd.DataFrame([{'spuid': '001', 'biosample_accession': acc, 'sra_accession': ''}
                         for acc in ('SAMN1', 'SAMN2')])
    with pytest.raises(ValueError, match='Conflicting BioSample accessions'):
        join.merge_accessions(metadata(), rows)


def test_command_line_exports_existing_samn_and_sra(tmp_path):
    meta = metadata()
    meta['biosample_accession'] = ['SAMN1', '']
    metadata_path = tmp_path / 'metadata.tsv'
    meta.to_csv(metadata_path, sep='\t', index=False)
    report_path = tmp_path / 'batch_1.csv'
    pd.DataFrame([report('sra', 'arbitrary-read-id', 'SRR1')]).to_csv(report_path, index=False)
    subprocess.run([sys.executable, str(BIN / 'aggregate_reports.py'), '--metadata_tsv',
                    str(metadata_path), str(report_path)], cwd=tmp_path, check=True)
    output = tmp_path / 'accessions.xlsx'
    subprocess.run([sys.executable, str(BIN / 'join_accessions_with_metadata.py'), '--metadata_tsv',
                    str(metadata_path), '--submission_report', str(tmp_path / 'submission_report.csv'),
                    '--output', str(output)], cwd=tmp_path, check=True)
    exported = pd.read_excel(output, header=1, dtype=str, keep_default_na=False)
    assert exported['ncbi-spuid'].tolist() == ['001', 'MixedCase']
    assert exported['biosample_accession'].tolist() == ['SAMN1', '']
    assert exported['sra_accession'].tolist() == ['SRR1', '']


def test_generated_genbank_identifiers_map_to_metadata(tmp_path):
    result = combine(tmp_path, [report('genbank', 'MixedCase-GB', 'PQ123456')])
    assert result.iloc[0]['spuid'] == 'MixedCase'
    assert result.iloc[0]['genbank_accession'] == 'PQ123456'


def test_conflicting_biosample_accessions_across_batches_rejected(tmp_path):
    paths = []
    for batch, accession in ((1, 'SAMN1'), (2, 'SAMN2')):
        path = tmp_path / f'batch_{batch}.csv'
        pd.DataFrame([report('biosample', '001', accession)]).to_csv(path, index=False)
        paths.append(path)
    result = aggregate.aggregate_reports(paths, metadata())
    with pytest.raises(ValueError, match='Conflicting BioSample accessions'):
        join.merge_accessions(metadata(), result)


@pytest.mark.parametrize('existing,reported,expected', [
    ('SRR2;SRR1', ['SRR2', 'SRR1'], 'SRR1;SRR2'),
    ('SRR1', ['SRR2', 'SRR1'], 'SRR1;SRR2'),
    ('SRR1;SRR2', [''], 'SRR1;SRR2'),
])
def test_existing_sra_set_roundtrip(existing, reported, expected):
    meta = metadata()
    meta['sra_accession'] = [existing, '']
    rows = pd.DataFrame([{'spuid': '001', 'biosample_accession': '', 'sra_accession': accession}
                         for accession in reported])
    merged = join.merge_accessions(meta, rows)
    assert merged['sra_accession'].tolist() == [expected, '']
    assert merged['ncbi-spuid'].is_unique


def test_report_cannot_silently_drop_one_existing_sra_accession():
    meta = metadata()
    meta['sra_accession'] = ['SRR1;SRR2', '']
    rows = pd.DataFrame([{'spuid': '001', 'biosample_accession': '', 'sra_accession': 'SRR1'}])
    with pytest.raises(ValueError, match='Existing sra_accession conflicts'):
        join.merge_accessions(meta, rows)


def test_multiple_sra_accessions_are_valid_for_missing_accession_logging():
    from unittest.mock import Mock
    logger = Mock()
    frame = pd.DataFrame([{'ncbi-spuid': '001', 'biosample_accession': 'SAMN1',
                           'sra_accession': 'SRR1;SRR2'}])
    join.log_missing_accessions(frame, logger)
    logger.info.assert_not_called()
