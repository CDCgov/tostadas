# Running nf-tests Locally

This repository uses [nf-test](https://code.askimed.com/nf-test/) to test our
Nextflow pipeline. These tests are automatically run in our
[GitHub Actions](https://docs.github.com/en/actions) CI workflow
on every push and pull request.

If CI tests are failing, it's usually because snapshots are out of date
or the pipeline output has changed. This guide shows how to run them locally
and update snapshots if needed.

---

## Install nf-test

Install nf-test globally (only needed once):

```bash
curl -fsSL https://code.askimed.com/install/nf-test | bash
```

Make sure it's available in your PATH:

```bash
nf-test version
```

## Run Tests

The nf-test configuration in `tests/nextflow.config` enables Singularity and uses the TOSTADAS container. Install Singularity before running these tests. The Python regression tests below do not require a container engine.

Run all tests in the tests/ folder:

```bash
nf-test test
```

Run a specific test file:

```bash
nf-test test tests/<name_of_test>.nf.test
```

## Update Snapshots

If the test output has intentionally changed, you'll need to update the saved
snapshots so the tests will pass again:

```bash
nf-test test --update-snapshot
```

Commit and push the updated .snap files.

## Match the CI Environment

The CI workflow at [`.github/workflows/CI_main.yml`](../.github/workflows/CI_main.yml) selects the floating `latest-edge` Nextflow channel. To use that channel locally:

```bash
export NXF_VER=latest-edge
```

To reproduce a particular CI run, read its resolved Nextflow version from the run log and set `NXF_VER` to that exact version instead.

## Offline submission regression tests

The portable tests use temporary files and simulated FTP/SFTP clients. They cover report parsing through Excel export, connection cleanup, collision handling, and platform preparation. No NCBI credentials are needed:

```bash
python3 -m pytest -q tests --ignore=tests/test_completeness.py
```

`tests/test_completeness.py` additionally uses an external `vadr_runs_bundle/` directory beside the repository, including `vadr_qc_20260422/batch1` and `staging_20260507/vadr_qc`. That bundle is not included in a normal clone. When it is available, run `python3 -m pytest -q tests/test_completeness.py` separately.

The optional Nextflow tests run actual local preparation, upload, polling, aggregation, and metadata-join modules. Python network connections are blocked. They check Nanopore preparation, task caching on resume, and accession mappings in the final workbook. They require Nextflow and the scripts' Python dependencies, but no containers or NCBI credentials.

```bash
RUN_NEXTFLOW_TESTS=1 python3 -m pytest -q tests/test_submission_resume_workflow.py tests/test_accession_reporting_workflow.py tests/test_sra_platform_preparation.py
```

For an offline Nextflow installation, set `NXF_VER` to the installed version and `NXF_OFFLINE=true`.
