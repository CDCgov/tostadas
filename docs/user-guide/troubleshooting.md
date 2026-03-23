# Troubleshooting

If you encounter issues while using the TOSTADAS pipeline, refer to the following troubleshooting steps to resolve common problems:

## Common Issues and Solutions

### table2asn Not on PATH

**Issue:** Nextflow is using an outdated cached image.

**Solution:** Locate the image (e.g., `$HOME/.singularity/staphb-tostadas-latest.img`) and delete it. This will force Nextflow to pull the latest version.

### Pipeline Hangs Indefinitely

**Issue:** This may be caused by duplicate sample IDs in the FASTA file (e.g., a multicontig FASTA). This is only a problem for submissions to GenBank using `table2asn`.

**Solution:** Review the sequence headers in the sample FASTA files and ensure that each header is unique.

### NCBI FTP Login Fails

**Issue:** The FTP credentials in your submission config are rejected by NCBI. This usually means you are using a personal NCBI account instead of the center-level account required for FTP submissions.

**Solution:** NCBI FTP submission requires a dedicated center account, not a regular NCBI login. See the [NCBI Center Account](general_NCBI_submission_guide.md#ncbi-center-account) section for instructions on requesting one. Verify that your `submission_config.yaml` contains the center account username and password, not your personal credentials.

### VADR Model Download Fails

**Issue:** The pipeline cannot download the VADR covariance model file specified by `vadr_cm_url`. This can happen when compute nodes lack outbound network access or when the URL is incorrect.

**Solution:** Confirm that `vadr_cm_url` in your config points to a valid, accessible URL. If your compute environment restricts internet access from worker nodes, download the model files ahead of time and provide a local path. You can test connectivity from a compute node with `curl -I <vadr_cm_url>`.

### Missing batch_summary.json

**Issue:** The `update_submission` entry point expects output files from a prior `biosample_and_sra` submission run. If those files are missing or the output directory does not contain `batch_summary.json`, the process will fail.

**Solution:** Run the initial submission pipeline first to generate the required output, then point `update_submission` at the same output directory. The `batch_summary.json` file is produced during the BioSample/SRA submission step and is required for tracking submission status.

### Metadata Validation Errors

**Issue:** Validation fails because the metadata spreadsheet is missing columns required by the selected BioSample package (e.g., `SARS-CoV-2.wwsurv.1.0` expects wastewater-specific fields).

**Solution:** Ensure your metadata file includes all columns required by the BioSample package specified in `submission_config.yaml`. If you are only submitting to GenBank and do not need BioSample/SRA, use the `--genbank_only` flag to bypass BioSample-specific validation requirements.

### Singularity Image Pull Fails

**Issue:** Pulling the container image fails with permission errors, disk space errors, or timeouts.

**Solution:** Check two things:

- The Singularity cache directory (controlled by `SINGULARITY_CACHEDIR` or `NXF_SINGULARITY_CACHEDIR`) has sufficient disk space and write permissions.
- Your environment can reach the container registry. On shared HPC systems, the default cache location in your home directory may be on a quota-limited filesystem. Set `NXF_SINGULARITY_CACHEDIR` to a path on a larger volume.

### Pipeline Retry Behavior

**Issue:** Processes fail and you are unsure whether they will be retried automatically.

**Solution:** Retry behavior differs by process type. Submission processes (BioSample, SRA, GenBank) only retry on OOM errors or signal-based kills (e.g., SIGKILL from a scheduler), not on general failures. Fetch and download processes (such as retrieving submission status or downloading model files) retry unconditionally on any failure. Check `.nextflow.log` or the process work directory's `.command.log` for the specific exit code to determine whether a retry was attempted.

## Resuming a Failed Run

Nextflow supports resuming a pipeline from the point of failure. When a run fails partway through, completed tasks do not need to be re-executed.

To resume, re-run the same command with the `-resume` flag:

```bash
nextflow run main.nf -resume -profile singularity,mpox --workflow full_submission --submission_config conf/submission_config.yaml
```

All other parameters should match the original run. Nextflow uses the `work/` directory to cache completed task outputs and will only re-execute processes that did not finish successfully.

!!! warning
    If the `work/` directory has been deleted or moved, resume is not possible. Nextflow requires the cached intermediate files to determine which tasks completed.

### Common scenarios where resume is useful

- **FTP timeout during submission upload.** A transient network interruption caused the FTP transfer to fail. Resuming retries only the failed upload step.
- **VADR failure on a subset of samples.** One or more samples failed annotation. After investigating and correcting input data, resuming skips samples that already passed.
- **Container pull failure.** A registry timeout prevented the Singularity or Docker image from downloading. Resuming retries the image pull without repeating completed tasks.
- **Scheduler-killed processes.** On HPC systems, a job may be killed due to walltime or memory limits. Adjusting resource requests and resuming avoids re-running successful processes.

!!! tip
    Check `.nextflow.log` for details on which cached tasks were reused and which were re-executed.

## Polling Timeout Recovery

During `full_submission`, the pipeline polls NCBI for submission reports using exponential backoff. The default timeout is 30 minutes. If this timeout is reached, the pipeline logs a warning and continues.

!!! note
    A polling timeout does not mean the submission failed. The data was already sent to NCBI -- only the automated report retrieval timed out.

To fetch reports after a timeout, run the `fetch_accessions` workflow:

```bash
nextflow run main.nf -profile singularity,mpox --workflow fetch_accessions --submission_config conf/submission_config.yaml
```

To increase the polling timeout for future runs, use the `--poll_timeout` parameter (value in seconds):

```bash
nextflow run main.nf -profile singularity,mpox --workflow full_submission --poll_timeout 3600 --submission_config conf/submission_config.yaml
```

The example above sets the timeout to 1 hour (3600 seconds).

### Expected NCBI processing times

NCBI processing time varies by submission type:

| Submission Type | Typical Processing Time |
|-----------------|-------------------------|
| BioSample       | Minutes to hours        |
| SRA             | Minutes to hours        |
| GenBank (virus via BankIt) | Minutes to days |
| GenBank (WGS bacteria/eukaryote) | Days to weeks |

Because GenBank WGS submissions can take days or weeks, the polling timeout is expected to expire for those submissions. Use `fetch_accessions` to retrieve reports once NCBI has finished processing.

## Error Message Reference

### Validation Errors

These errors are raised during the `METADATA_VALIDATION` process and indicate problems with the input metadata.

| Error | Cause | Resolution |
|-------|-------|------------|
| Missing required column `<column_name>` | The metadata file does not contain a column that the selected BioSample package requires. | Add the missing column to the metadata file, or switch to a BioSample package that does not require it. If submitting only to GenBank, use `--genbank_only` to skip BioSample-specific checks. |
| Invalid date format in `collection_date` | The date value does not match any recognized format (ISO 8601, `Mon-YYYY`, `Mon.YY`). | Reformat dates to `YYYY-MM-DD`, `YYYY-MM`, or one of the abbreviated NCBI formats. Verify there are no typos or mixed delimiters. |
| Duplicate SPUID `<value>` | Two or more samples resolve to the same Submitter-Provided Unique ID, which NCBI requires to be unique within a namespace. | Ensure every sample has a distinct `sample_name` value. Check for accidental duplicate rows in the metadata. |
| No matching FASTA file for sample `<name>` | When `--fasta_dir` is set, no FASTA file in the directory matches the sample name. | Verify that FASTA file names (without extension) match the `sample_name` values in the metadata exactly, including case. |

### NCBI Rejection Errors

These errors appear in `report.xml` files returned by NCBI after submission.

| Error | Cause | Resolution |
|-------|-------|------------|
| Invalid BioSample package | The `BioSample_package` value in `submission_config.yaml` does not match a valid NCBI package name. | Check the package name against the [NCBI BioSample packages list](https://www.ncbi.nlm.nih.gov/biosample/docs/packages/) and correct any typos. |
| Missing required attribute `<field>` | A field that NCBI considers mandatory for the selected BioSample package is empty or absent. | Populate the field in the metadata file with a valid value, or use `"Not Provided"` if the data is genuinely unavailable. |
| Sample already exists with accession `<SAMN...>` | A BioSample with the same attributes already exists in NCBI. This occurs when resubmitting data that was previously accepted. | Use the `update_submission` workflow instead of creating a new submission, or verify that the data has not already been submitted. |

### VADR Annotation Errors

These errors occur during the `RUN_VADR` subworkflow.

| Error | Cause | Resolution |
|-------|-------|------------|
| Sequence too short | The input sequence is shorter than the minimum length VADR requires for the selected model. | Check the FASTA file for truncated sequences. Remove or replace sequences that do not meet the minimum length. |
| No model match | VADR could not find a covariance model that matches the input sequence above the identity threshold. | Verify that `--virus_subtype` is set correctly and that the VADR models directory contains the expected model files. If the sequence is highly divergent, it may not be annotatable with VADR. |
| VADR model directory does not match virus subtype | The pre-flight check detected a mismatch between `--virus_subtype` and the model directory path. | Ensure `--vadr_models_dir` points to a directory containing models for the specified `--virus_subtype`. |

## Get in Touch

To report a bug, suggest new features, or provide feedback, [open an issue](https://github.com/CDCgov/tostadas/issues/new/choose) and the development team will respond as soon as possible.
