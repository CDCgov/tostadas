"""Offline checks for report retrieval from flat and mixed-platform batches."""
import sys
import types
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bin'))
try:
    import nameparser
except ImportError:
    stub = types.ModuleType('nameparser')
    stub.HumanName = object
    sys.modules['nameparser'] = stub

import fetch_submission
import poll_and_fetch_reports as polling
import submission_helper
from submission_layout import discover_databases, sra_platforms


LAYOUTS = [
    ([None], []),
    (['illumina', 'nanopore'], []),
    (['illumina'], ['nanopore']),
    (['nanopore'], ['illumina']),
    ([None], ['illumina', 'nanopore']),
]


@pytest.fixture(params=LAYOUTS)
def batch(request, tmp_path):
    platforms, empty_platforms = request.param
    biosample = tmp_path / 'biosample'
    biosample.mkdir()
    (biosample / 'submission.xml').write_text('<Submission/>')
    for platform in platforms:
        folder = tmp_path / 'sra'
        if platform:
            folder /= platform
        folder.mkdir(parents=True, exist_ok=True)
        (folder / 'submission.xml').write_text('<Submission/>')
    for platform in empty_platforms:
        (tmp_path / 'sra' / platform).mkdir(parents=True, exist_ok=True)
    return tmp_path, platforms


def expected_reports(root, platforms):
    return {
        'biosample': [str(root / 'biosample' / 'report.xml')],
        'sra': [str(root / 'sra' / (platform or '') / 'report.xml')
                for platform in platforms],
    }


def fake_submission_factory(visited):
    class FakeSubmission:
        def __init__(self, **kwargs):
            self.client = Mock()
            self.client.change_dir.side_effect = visited.append

        def fetch_report(self, remote, local):
            Path(local).write_text('<SubmissionStatus status="processed-ok"/>')
            return local

    return FakeSubmission


def expected_remote_dirs(platforms):
    return ['submit/Production/demo_batch_1_biosample'] + [
        'submit/Production/demo_batch_1_sra' + (f'_{platform}' if platform else '')
        for platform in platforms
    ]


def test_discovery_follows_xml_files(batch):
    root, platforms = batch
    assert discover_databases(root) == ['biosample', 'sra']
    assert sra_platforms(root) == platforms
    assert polling.resolve_db_targets(discover_databases(root), root) == [
        ('biosample', None, str(root / 'biosample')),
        *[('sra', platform, str(root / 'sra' / (platform or '')))
          for platform in platforms],
    ]


def test_poll_fetches_each_xml_destination(batch, monkeypatch):
    root, platforms = batch
    visited = []
    saved = Mock()
    monkeypatch.setattr(polling, 'Submission', fake_submission_factory(visited))
    monkeypatch.setattr(polling.time, 'sleep', lambda _: None)
    monkeypatch.setattr(polling, 'parse_and_save_reports', saved)
    polling.poll_and_fetch({
        'submission_folder': str(root), 'test': False,
        'identifier': 'demo', 'batch_id': 'batch_1', 'submission_mode': 'ftp',
        'initial_interval': 1, 'max_interval': 2, 'timeout': 30,
    }, {})
    assert visited == expected_remote_dirs(platforms)
    saved.assert_called_once_with(expected_reports(root, platforms), str(root), 'batch_1')


def test_fetch_entrypoint_fetches_each_xml_destination(batch, monkeypatch):
    root, platforms = batch
    visited = []
    saved = Mock()
    monkeypatch.setattr(submission_helper, 'Submission', fake_submission_factory(visited))
    monkeypatch.setattr(fetch_submission, 'setup_logging', Mock())
    monkeypatch.setattr(fetch_submission.SubmissionConfigParser, 'load_config', lambda _: {})
    monkeypatch.setattr(fetch_submission, 'parse_and_save_reports', saved)
    monkeypatch.setattr(sys, 'argv', [
        'fetch_submission.py', '--submission_folder', str(root),
        '--config_file', 'unused', '--identifier', 'demo', '--batch_id', 'batch_1',
    ])
    fetch_submission.main_fetch()
    assert visited == expected_remote_dirs(platforms)
    saved.assert_called_once_with(expected_reports(root, platforms), str(root), 'batch_1')


def test_empty_and_unrecognized_sra_directories_are_not_submissions(tmp_path):
    for platform in ('illumina', 'nanopore', 'other'):
        (tmp_path / 'sra' / platform).mkdir(parents=True)
    (tmp_path / 'sra' / 'other' / 'submission.xml').write_text('<Submission/>')
    assert discover_databases(tmp_path) == []
    assert polling.resolve_db_targets(['sra'], tmp_path) == []


@pytest.mark.parametrize('relative', ['genbank', 'genbank/sample_1'])
def test_genbank_discovery_is_preserved(tmp_path, relative):
    folder = tmp_path / relative
    folder.mkdir(parents=True)
    (folder / 'submission.xml').write_text('<Submission/>')
    assert discover_databases(tmp_path) == ['genbank']
