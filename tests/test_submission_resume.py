"""Offline submission recovery and collision checks."""
import errno
import ftplib
import sys
import types
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'bin'))
try:
    import nameparser
except ImportError:
    stub = types.ModuleType('nameparser')
    stub.HumanName = object
    sys.modules['nameparser'] = stub

import submission
from submission_helper import FTPClient, SFTPClient

XML = '''<Submission><Action><AddData target_db="BioSample">
<Data><XmlContent><BioSample><Attributes><Attribute attribute_name="isolate">001</Attribute>
</Attributes></BioSample></XmlContent></Data>
<Identifier><SPUID spuid_namespace="test">001</SPUID></Identifier>
</AddData></Action></Submission>'''
REPORT = '''<SubmissionStatus status="processed-ok"><Action target_db="BioSample" status="processed-ok">
<Response><Object spuid_namespace="test" spuid="001" accession="SAMN123"/></Response>
</Action></SubmissionStatus>'''
REMOTE = 'submit/Production/demo_batch_1_biosample'


class FakeClient:
    def __init__(self, remote=None, listing_error=False):
        self.remote = remote or {}
        self.uploads = []
        self.closed = 0
        self.listing_error = listing_error

    def connect(self):
        pass

    def close(self):
        self.closed += 1

    def dir_exists(self, path):
        return path in self.remote

    def list_dir(self, path):
        if self.listing_error:
            raise ftplib.error_perm('550 Listing denied')
        return list(self.remote[path])

    def download_file(self, remote, local):
        folder, name = remote.rsplit('/', 1)
        Path(local).write_text(self.remote[folder][name])

    def make_dir(self, path):
        self.remote.setdefault(path, {})

    def change_dir(self, path):
        self.cwd = path

    def upload_file(self, path, name):
        self.uploads.append((self.cwd, name))
        self.remote[self.cwd][name] = Path(path).read_text()


@pytest.fixture
def batch(tmp_path):
    folder = tmp_path / 'batch_1' / 'biosample'
    folder.mkdir(parents=True)
    (folder / 'submission.xml').write_text(XML)
    (folder / 'submit.ready').touch()
    return folder.parent


def run_upload(batch, client, extra_args=()):
    args = ['submission.py', '--submission_folder', str(batch), '--submission_name', 'batch_1',
            '--identifier', 'demo', '--config_file', 'unused', *extra_args]
    with patch.object(sys, 'argv', args), patch.object(submission, 'setup_logging'), \
         patch.object(submission, 'FTPClient', return_value=client), \
         patch.object(submission.SubmissionConfigParser, 'load_config', return_value={}):
        submission.main_submit()


def test_new_submission_uploads_trigger_last(batch):
    client = FakeClient()
    run_upload(batch, client)
    assert client.uploads == [(REMOTE, 'submission.xml'), (REMOTE, 'submit.ready')]
    assert client.closed == 1


def test_successful_biosample_requires_manual_reconciliation(batch):
    client = FakeClient({REMOTE: {'submission.xml': XML, 'report.xml': REPORT}})
    with pytest.raises(SystemExit):
        run_upload(batch, client)
    assert client.uploads == []
    assert client.closed == 1


@pytest.mark.parametrize('report', [
    REPORT.replace('processed-ok', 'processed-error'),
    REPORT.replace('processed-ok', 'processing'),
    REPORT.replace('spuid="001"', 'spuid="002"'),
    REPORT.replace('spuid_namespace="test"', 'spuid_namespace="other"'),
    REPORT.replace('accession="SAMN123"', 'accession=""'),
    '<SubmissionStatus status="processed-ok"/>',
    '<broken',
])
def test_unverified_report_blocks_upload(batch, report):
    client = FakeClient({REMOTE: {'submission.xml': XML, 'report.xml': report}})
    with pytest.raises(SystemExit):
        run_upload(batch, client)
    assert client.uploads == []
    assert client.closed == 1


def test_changed_metadata_blocks_upload(batch):
    client = FakeClient({REMOTE: {'submission.xml': XML.replace('>001<', '>002<'), 'report.xml': REPORT}})
    with pytest.raises(SystemExit):
        run_upload(batch, client)
    assert not client.uploads


def test_partial_upload_without_report_blocks_upload(batch):
    client = FakeClient({REMOTE: {'submission.xml': XML}})
    with pytest.raises(SystemExit):
        run_upload(batch, client)
    assert not client.uploads


def test_listing_failure_blocks_upload(batch):
    client = FakeClient({REMOTE: {'submission.xml': XML}}, listing_error=True)
    with pytest.raises(ftplib.error_perm):
        run_upload(batch, client)
    assert not client.uploads
    assert client.closed == 1


def test_existing_sra_is_not_assumed_identical(batch):
    sra = batch / 'sra'
    sra.mkdir()
    (sra / 'submission.xml').write_text(XML)
    (sra / 'submit.ready').touch()
    (batch / 'biosample/submission.xml').unlink()
    (batch / 'biosample/submit.ready').unlink()
    client = FakeClient({'submit/Production/demo_batch_1_sra': {'submission.xml': XML, 'report.xml': REPORT}})
    with pytest.raises(SystemExit):
        run_upload(batch, client)
    assert not client.uploads


def test_ftp_listing_errors_are_not_empty_directories():
    client = object.__new__(FTPClient)
    client.ftp = Mock()
    client.ftp.nlst.side_effect = ftplib.error_perm('550 Listing denied')
    with pytest.raises(ftplib.error_perm):
        client.dir_exists(REMOTE)
    with pytest.raises(ftplib.error_perm):
        client.list_dir(REMOTE)


def test_ftp_detects_existing_and_absent_directories():
    client = object.__new__(FTPClient)
    client.ftp = Mock()
    client.ftp.nlst.return_value = [REMOTE]
    assert client.dir_exists(REMOTE)
    assert not client.dir_exists(REMOTE + '_other')


def test_sftp_only_treats_missing_path_as_absent():
    client = object.__new__(SFTPClient)
    client.sftp = Mock()
    client.sftp.stat.side_effect = OSError(errno.ENOENT, 'Missing')
    assert not client.dir_exists(REMOTE)
    client.sftp.stat.side_effect = OSError(errno.EACCES, 'Denied')
    with pytest.raises(OSError):
        client.dir_exists(REMOTE)
    client.sftp.listdir.side_effect = OSError(errno.EACCES, 'Denied')
    with pytest.raises(OSError):
        client.list_dir(REMOTE)


def test_incomplete_report_does_not_skip_multiple_samples(batch):
    action = XML[XML.index('<Action>'):XML.index('</Action>') + len('</Action>')]
    xml = XML.replace('</Submission>', action.replace('001', '002') + '</Submission>')
    (batch / 'biosample/submission.xml').write_text(xml)
    client = FakeClient({REMOTE: {'submission.xml': xml, 'report.xml': REPORT}})
    with pytest.raises(SystemExit):
        run_upload(batch, client)
    assert not client.uploads


def test_stale_success_cannot_confirm_overwritten_xml(batch):
    # An older attempt succeeded for the same SPUID, but an interrupted legacy
    # uploader replaced submission.xml with changed attributes before retriggering.
    changed = XML.replace('>001</Attribute>', '>changed-isolate</Attribute>')
    (batch / 'biosample/submission.xml').write_text(changed)
    client = FakeClient({REMOTE: {'submission.xml': changed, 'report.xml': REPORT}})
    client.download_file = Mock(side_effect=AssertionError('Do not infer payload provenance'))
    with pytest.raises(SystemExit):
        run_upload(batch, client)
    assert not client.uploads
    assert client.closed == 1


def test_explicit_collision_override_still_uploads_trigger_last(batch):
    client = FakeClient({REMOTE: {'submission.xml': XML, 'report.xml': REPORT}})
    run_upload(batch, client, ['--allow_dir_collision'])
    assert client.uploads == [(REMOTE, 'submission.xml'), (REMOTE, 'submit.ready')]
    assert client.closed == 1


def test_empty_remote_directory_can_be_used(batch):
    client = FakeClient({REMOTE: {}})
    run_upload(batch, client)
    assert client.uploads == [(REMOTE, 'submission.xml'), (REMOTE, 'submit.ready')]


def test_upload_error_closes_connection(batch):
    client = FakeClient()
    client.upload_file = Mock(side_effect=OSError('Connection lost'))
    with pytest.raises(OSError, match='Connection lost'):
        run_upload(batch, client)
    assert client.closed == 1
