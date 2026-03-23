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

## Get in Touch

If you need to report a bug, suggest new features, or just say "thanks", [open an issue](https://github.com/CDCgov/tostadas/issues/new/choose) and we'll try to get back to you as soon as possible!
