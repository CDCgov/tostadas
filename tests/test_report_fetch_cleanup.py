"""Connection lifetime and current-report selection, without network access."""
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

import submission_helper as helper


@pytest.mark.parametrize('outcome', ['success', 'timeout', 'connect', 'change_dir', 'download'])
@pytest.mark.parametrize('close_fails', [False, True])
def test_legacy_fetch_always_closes_without_masking_errors(tmp_path, monkeypatch, outcome, close_fails):
    client = Mock()
    fetch = Mock(return_value=str(tmp_path / 'report.xml'))
    original_error = OSError('original transfer failure')
    if outcome in ('connect', 'change_dir'):
        getattr(client, outcome).side_effect = original_error
    elif outcome == 'download':
        fetch.side_effect = original_error
    elif outcome == 'timeout':
        fetch.return_value = False
    if close_fails:
        client.close.side_effect = OSError('close failed')
    monkeypatch.setattr(helper, 'Submission', Mock(return_value=types.SimpleNamespace(client=client, fetch_report=fetch)))
    # Preserve the existing total budget; one unsuccessful attempt exhausts it.
    times = iter([0, 0, 61])
    monkeypatch.setattr(helper.time, 'time', lambda: next(times, 61))
    monkeypatch.setattr(helper.time, 'sleep', Mock())

    def run():
        return helper.fetch_all_reports(['biosample'], str(tmp_path), {}, {},
                                        'Production', 'ftp', 'demo', 'batch_1', timeout=60)

    if outcome in ('connect', 'change_dir', 'download'):
        with pytest.raises(OSError) as exc:
            run()
        assert exc.value is original_error
    else:
        result = run()
        assert result == {'biosample': [str(tmp_path / 'report.xml')] if outcome == 'success' else []}
    client.close.assert_called_once_with()
    if outcome in ('connect', 'change_dir'):
        fetch.assert_not_called()
    else:
        fetch.assert_called_once()


@pytest.mark.parametrize('local_exists', [False, True])
def test_current_report_is_downloaded_even_if_local_copy_exists(tmp_path, local_exists):
    local = tmp_path / 'report.xml'
    if local_exists:
        local.write_text('old report')
    client = Mock()
    client.file_exists.return_value = True
    client.download_file.side_effect = lambda remote, dest: Path(dest).write_text('current report')
    submission = object.__new__(helper.Submission)
    submission.client = client
    assert submission.fetch_report('remote', str(local)) == str(local)
    client.download_file.assert_called_once_with('report.xml', str(local))
    assert local.read_text() == 'current report'


def test_no_current_report_does_not_select_history_or_local_copy(tmp_path):
    local = tmp_path / 'report.xml'
    local.write_text('previous local report')
    client = Mock()
    client.file_exists.return_value = False
    client.list_dir.return_value = ['report.1.xml', 'report.2.xml']
    submission = object.__new__(helper.Submission)
    submission.client = client
    assert submission.fetch_report('remote', str(local)) is False
    client.file_exists.assert_called_once_with('report.xml')
    client.list_dir.assert_not_called()
    client.download_file.assert_not_called()
    assert local.read_text() == 'previous local report'
