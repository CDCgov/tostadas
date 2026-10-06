# Troubleshooting

If you encounter issues while using the TOSTADAS pipeline, refer to the following troubleshooting steps to resolve common problems:

## Common Issues and Solutions

### Outdated Cached Container Image

**Issue:** Nextflow is using an outdated cached image.

**Solution:** Locate the image (e.g., `$HOME/.singularity/staphb-tostadas-latest.img`) and delete it. This will force Nextflow to pull the latest version.

### Spaces in FASTA Headers Cause Missing Source Modifiers

**Issue:** Spaces in FASTA header lines cause table2asn to truncate the sequence ID at the first space. Everything after the space is treated as a description, not part of the identifier. This prevents table2asn from matching the sequence to its corresponding row in the source modifier file (source.src), resulting in missing source modifiers (no BioProject, BioSample, country, etc.) in the SQN file.

**Solution:** Ensure FASTA headers do not contain spaces. Replace any spaces with underscores in both the FASTA header and the corresponding `Sequence_ID` or `Strain` field in the metadata. The `geo_loc_name` field may retain spaces as NCBI expects them in that format (e.g., `USA:South Dakota`).

### Pipeline Hangs Indefinitely

**Issue:** This may be caused by duplicate sample IDs in the FASTA file (e.g., a multicontig FASTA). This is only a problem for submissions to GenBank using `table2asn`.

**Solution:** Review the sequence headers in the sample FASTA files and ensure that each header is unique.

### NCBI FTP Login Fails

**Issue:** The credentials in your submission config are rejected by the configured FTP/SFTP endpoint.

**Solution:** Verify that `NCBI_username` and `NCBI_password` contain the credentials issued for that submission endpoint, and that the host matches the selected `--submission_mode`. A portal login alone does not establish access to the file-transfer endpoint. See [NCBI Center Account](general_NCBI_submission_guide.md#ncbi-center-account) for account setup guidance.

### Resuming an Interrupted Submission

Keep the original Nextflow cache and work directories and use `-resume`. Upload and report-polling tasks work on separate copies of the batch directory so their logs and reports do not invalidate upstream task inputs.

If an upload task executes again, any nonempty remote submission directory stops with a collision error, including directories containing successful reports. Current XML and matching identifiers cannot prove that an older report processed that exact payload. Directory-listing failures also stop the upload.

An interrupted task may have finished one database upload before failing on another. In that case, resume stops for manual reconciliation of the existing remote submissions; it does not automatically re-upload or assume completion.
Inspect the existing reports before retrying. Do not rename the metadata file or remote directory to bypass a collision: that can create another submission attempt for the same samples. Updating the pipeline does not repair reports from earlier duplicate attempts. The `fetch_accessions` workflow downloads the current remote reports; preserve historical successful reports separately for reconciliation.

### Combining BioSample and SRA Accessions

Report aggregation uses `ncbi-spuid` and `ncbi-spuid-sra` from `validated_metadata_all_samples.tsv` to associate results with samples. Keep this validated metadata with the original submission outputs. Row order and metadata filenames do not determine accession mappings.

Existing accessions are retained when a report supplies none. Conflicting accessions or report identifiers without a unique metadata match stop aggregation for reconciliation. This reporting error does not mean the original NCBI submission failed; inspect the original reports before retrying any uploads.

For samples with multiple SRA runs, the final Excel workbook keeps one metadata row per sample and lists distinct SRA accessions separated by semicolons. The combined CSV retains individual report records.

### VADR Model Download Fails

**Issue:** The pipeline cannot download the VADR covariance model file specified by `vadr_cm_url`. This can happen when compute nodes lack outbound network access or when the URL is incorrect.

**Solution:** Confirm that `vadr_cm_url` in your config points to a valid, accessible URL. If your compute environment restricts internet access from worker nodes, download the model files ahead of time and provide a local path. You can test connectivity from a compute node with `curl -I <vadr_cm_url>`.

### Missing batch_summary.json

**Issue:** The `update_submission` entry point needs the original batch-to-sample mapping, `batch_summary.json`, produced during metadata validation. It looks under `<original_submission_outdir>/../<validation_outdir>/batched_tsvs/`; this file records batch membership, not NCBI submission status.

**Solution:** An update requires an initial submission and its original outputs. If that submission already ran, check `--original_submission_outdir` and `--validation_outdir`, then locate or restore the original validation files from that run. Do not repeat uploads to recreate a missing local mapping. Preserve the original batch membership when recovering those files.

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

Nextflow can reuse completed tasks when their inputs and cached outputs remain valid.

To resume, re-run the original command with `-resume`, preserving its workflow, profiles, configuration, metadata, output paths, protocol, and production/test setting. For example, if these were the original settings for a production run:

```bash
nextflow run main.nf -resume -profile singularity,mpox \
    --workflow full_submission \
    --meta_path /path/to/original_metadata.xlsx \
    --outdir /path/to/original_results \
    --submission_config /path/to/original_submission_config.yaml \
    --submission_mode ftp \
    --prod_submission true
```

Retain any additional original options, including batch size. For an original Test submission, use `--prod_submission false`; retain `--submission_mode sftp` if that was the original protocol. Changed inputs or missing cached outputs can cause completed tasks to execute again. See [Resuming an Interrupted Submission](#resuming-an-interrupted-submission) for the collision checks that apply to upload tasks.

!!! warning
    If the `work/` directory has been deleted or moved, resume is not possible. Nextflow requires the cached intermediate files to determine which tasks completed.

### Common scenarios where resume is useful

- **FTP timeout during submission upload.** Resume may execute the batch upload task again. If any files reached its remote directory, the collision check stops for reconciliation instead of continuing the transfer automatically.
- **VADR failure on a subset of samples.** After investigating and correcting input data, resume reuses completed tasks whose inputs and cached outputs remain valid.
- **Container pull failure.** A registry timeout prevented the Singularity or Docker image from downloading. Resuming retries the image pull without repeating completed tasks.
- **Scheduler-killed processes.** On HPC systems, a job may be killed due to walltime or memory limits. Adjusting resource requests and resuming avoids re-running successful processes.

!!! tip
    Check `.nextflow.log` for details on which cached tasks were reused and which were re-executed.

## Polling Timeout Recovery

During `full_submission`, the pipeline polls for BioSample and SRA reports using exponential backoff. The default polling budget is 30 minutes. The deadline is checked between network operations, so a blocking connection or transfer can extend elapsed time beyond that budget. When the polling loop reaches its deadline, it logs a warning and saves any reports collected; downstream steps may still lack required accessions.

!!! note
    A polling timeout does not mean the submission failed. The data was already sent to NCBI -- only the automated report retrieval timed out.

To fetch BioSample/SRA reports after a timeout, run `fetch_accessions` with the original output directory, metadata basename, configuration, and production/test setting. The metadata basename determines the remote directory prefix. For a production submission, replace these paths with the original values:

```bash
nextflow run main.nf -profile singularity,mpox \
    --workflow fetch_accessions \
    --meta_path /path/to/original_metadata.xlsx \
    --outdir /path/to/original_results \
    --submission_config /path/to/original_submission_config.yaml \
    --submission_mode ftp \
    --prod_submission true
```

For a Test submission, use `--prod_submission false`. Preserve the original profiles and additional configuration files, use `sftp` if that was the original protocol, and keep any custom submission or validation directory settings. Keep `validated_metadata_all_samples.tsv` with the original outputs for accession matching.

To allow a longer polling budget, add `--poll_timeout 3600` to the fetch command above, or to a future submission command. This sets the budget to one hour without requiring another upload to retrieve existing reports.

### Expected NCBI processing times

NCBI processing time varies by submission type:

| Submission Type | Typical Processing Time |
|-----------------|-------------------------|
| BioSample       | Minutes to hours        |
| SRA             | Minutes to hours        |
| GenBank (virus via BankIt) | Minutes to days |
| GenBank (WGS bacteria/eukaryote) | Days to weeks |

The current `fetch_accessions` workflow polls BioSample and SRA only; it skips GenBank. For GenBank status and accessions, inspect the submission's FTP reports or the Submission Portal as appropriate to its submission route. Increasing `--poll_timeout` does not enable GenBank polling.

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
