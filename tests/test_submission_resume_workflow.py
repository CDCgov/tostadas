"""Run with RUN_NEXTFLOW_TESTS=1 to verify task caching without NCBI access."""
import csv
import os
from pathlib import Path
import shutil
import subprocess

import pytest


@pytest.mark.skipif(os.environ.get('RUN_NEXTFLOW_TESTS') != '1', reason='Set RUN_NEXTFLOW_TESTS=1')
def test_upload_and_poll_resume_without_modifying_inputs(tmp_path, install_offline_scripts):
    executable = shutil.which('nextflow')
    if not executable:
        pytest.skip('Nextflow is not installed')
    repo = Path(__file__).resolve().parents[1]
    install_offline_scripts('submission.py', 'poll_and_fetch_reports.py')
    (tmp_path / 'config.yaml').write_text('NCBI_ftp_host: unused\nNCBI_username: unused\nNCBI_password: unused\n')
    (tmp_path / 'nextflow.config').write_text('''params {
 env_yml = 'unused'
 prod_submission = false
 send_submission_email = false
 dry_run = true
 metadata_basename = 'demo'
 submission_mode = 'ftp'
 poll_initial_interval = 1
 poll_max_interval = 1
 poll_timeout = 1
}
''')
    workflow = '''include { SUBMIT_SUBMISSION } from '@ROOT@/modules/local/submit_submission/main'
include { POLL_AND_FETCH_REPORTS } from '@ROOT@/modules/local/poll_and_fetch_reports/main'
process PREP {
 output:
 path 'batch_1'
 script:
 """
 mkdir -p batch_1/biosample batch_1/sra
 echo '<Submission/>' > batch_1/biosample/submission.xml
 echo '<Submission/>' > batch_1/sra/submission.xml
 touch batch_1/biosample/submit.ready batch_1/sra/submit.ready
 """
}
workflow {
 SUBMIT_SUBMISSION(PREP().map { tuple([batch_id: 'batch_1'], it) }, file('config.yaml'))
 POLL_AND_FETCH_REPORTS(SUBMIT_SUBMISSION.out.submission_batch_folder, file('config.yaml'))
}
'''
    (tmp_path / 'main.nf').write_text(workflow.replace('@ROOT@', str(repo)))
    for attempt in ['initial', 'resume']:
        command = [executable, '-log', attempt + '.log', 'run', 'main.nf', '-ansi-log', 'false',
                   '-with-trace', attempt + '.tsv']
        if attempt == 'resume':
            command.append('-resume')
        result = subprocess.run(command, cwd=tmp_path, capture_output=True, text=True, timeout=120)
        assert result.returncode == 0, result.stdout + result.stderr
    with (tmp_path / 'resume.tsv').open() as handle:
        rows = list(csv.DictReader(handle, delimiter='\t'))
    assert len(rows) == 3
    assert all(row['status'] == 'CACHED' for row in rows), rows
    with (tmp_path / 'initial.tsv').open() as handle:
        original = {row['name'].split(' (')[0]: row for row in csv.DictReader(handle, delimiter='\t')}
    def output_dir(name):
        task_hash = original[name]['hash']
        return next((tmp_path / 'work' / task_hash[:2]).glob(task_hash[3:] + '*')) / 'batch_1'
    prepared = output_dir('PREP')
    uploaded = output_dir('SUBMIT_SUBMISSION')
    assert not (prepared / 'submission.log').exists()
    assert not (prepared / 'fetch_submission.log').exists()
    assert (uploaded / 'submission.log').exists()
    assert not (uploaded / 'fetch_submission.log').exists()
