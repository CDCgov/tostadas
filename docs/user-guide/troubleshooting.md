# Troubleshooting

---

## Installation issues

### `table2asn not on PATH` / missing Python library (Singularity or Docker)

**Cause:** Nextflow is using a stale cached container image that predates the latest dependencies.

**Fix:** Delete the cached image and let Nextflow re-pull it.

```bash
# Singularity
rm -f $HOME/.singularity/staphb-tostadas-latest.img

# Docker
docker rmi staphb/tostadas:latest
```

Re-run your `nextflow run` command and the fresh image will be pulled automatically.

---

## Metadata validation errors

### `KeyError` or `Column not found` during validation

**Cause:** Your metadata Excel file is missing a column that the selected BioSample package requires, or a column name doesn't match exactly.

**Fix:**
1. Compare your Excel headers against the template for your package (`assets/sample_metadata/`)
2. Check `validation_outputs/errors/errors.txt` for the exact field name that's failing
3. If using a custom package, verify your `custom_fields_file` JSON maps all column names correctly

### `applymap` deprecation warning / pandas error

**Cause:** pandas version mismatch. The pipeline handles this automatically, but if you see it, your conda environment may have an incompatible pandas version.

**Fix:** Rebuild the conda environment: `conda env remove -n tostadas && conda env create -f environment.yml`

### Date format errors

NCBI requires dates in `YYYY-MM` or `YYYY-MM-DD` format. The `--date_format_flag` parameter controls this:
- `s` (default) — `YYYY-MM`
- `v` — `YYYY-MM-DD`
- `o` — leave unchanged

If your source dates are in a different format, use `--date_format_flag o` and pre-format them in your Excel file.

---

## Submission issues

### Pipeline hangs indefinitely during submission / "duplicate BioSeq ID" error

**Cause:** Duplicate sequence headers in a multicontig FASTA file. This affects `table2asn`-based GenBank submissions.

**Fix:** Review your FASTA files and ensure every `>header` line is unique within a file and across samples in the same batch.

### FTP connection times out or upload fails

**Cause:** Network instability, NCBI server load, or a VPN interrupting the connection.

**Fix:** The pipeline automatically retries FTP/SFTP operations up to 3 times with exponential backoff. If all retries fail:
1. Check that `NCBI_ftp_host` and `NCBI_sftp_host` in your submission config are correct
2. Verify your credentials work by manually connecting: `ftp <NCBI_ftp_host>`
3. Try switching `--submission_mode sftp` if you're on `ftp` (or vice versa)
4. Run with `--dry_run true` first to confirm the file paths look correct before uploading

### "Duplicate submission" error from NCBI

**Cause:** NCBI rejects re-uploads of samples that were already submitted with the same SPUID/namespace.

**Fix:** Use `--workflow update_submission` to update an existing submission rather than re-submitting. If you genuinely need to resubmit from scratch, contact NCBI to have the original submission withdrawn first.

### Credentials not found / authentication failure

**Cause:** `NCBI_username` or `NCBI_password` is blank in your submission config.

**Fix:** TOSTADAS reads credentials in this order:
1. `submission_config.yaml` values (if non-empty)
2. `.env` file (`NCBI_USERNAME`, `NCBI_PASSWORD`)
3. Nextflow Secrets (`NCBI_USERNAME`, `NCBI_PASSWORD`)

Check all three. See [Installation](installation.md#3-add-ncbi-credentials) for setup instructions.

---

## Accession / report issues

### `fetch_accessions` returns empty accessions

**Cause:** NCBI hasn't finished processing your submission yet. Processing typically takes minutes to hours.

**Fix:**
- Wait and re-run `--workflow fetch_accessions`
- Adjust `--submission_wait_time` (in seconds) to have the pipeline wait longer automatically. `calc` (default) waits 30s × `batch_size`
- Log in to the [NCBI Submission Portal](https://submit.ncbi.nlm.nih.gov/) to check submission status manually

### Updated Excel file missing accession columns

**Cause:** The `fetch_accessions` workflow looks for `report.xml` files in `--submission_outdir`. If the path doesn't match the original run's output, the update step won't find the reports.

**Fix:** Make sure `--submission_outdir` points to the same directory used in the original submission run (default: `submission_outputs` under `--outdir`).

---

## GenBank-specific issues

### GenBank submission via email not triggered

The GenBank email notification only fires when:
1. `--workflow` includes GenBank submission
2. `genbank_submission_type` is `table2asn`
3. `send_submission_email true`
4. `notif_email_recipient` is set in `conf/submission_config.yaml`

All four must be true. Check each condition.

### VADR annotation fails

**Cause:** Either the VADR models aren't installed for your virus, or the sequence diverges significantly from the reference.

**Fix:**
1. Check `vadr_clean_outputs/errors/` for the specific error
2. Verify `--vadr_models_dir` points to the correct model directory for your virus subtype
3. Sequences that fail VADR can be submitted without annotation — contact GenBank to discuss

---

## Nextflow / pipeline errors

### `Process terminated with error exit status 1` with no further message

**Fix:** Check the `.nextflow.log` file and the `work/` directory for the failed task. Each task has a `work/<hash>/` directory containing `.command.err` and `.command.out` with the full error output.

```bash
# Find the most recent failed task
grep -n "FAILED" .nextflow.log | tail -20

# Read the error output from a failed work directory
cat work/ab/cdef1234/.command.err
```

### Out of memory / process killed

**Fix:** Increase memory for the failing process in `conf/modules.config`, or use a machine/node with more RAM. The annotation steps (especially RepeatMasker) can be memory-intensive for large genomes.

### Pipeline works in test but fails on real data

Common causes:
- Sample IDs in your Excel file don't match the FASTA header names
- Excel file has hidden rows, merged cells, or non-standard formatting
- FASTA files contain ambiguous bases (`N`) that exceed NCBI's tolerance thresholds

---

## Getting help

If you can't resolve an issue with the steps above:

1. Enable verbose Nextflow logging: add `-with-trace -with-report -with-timeline` to your command
2. Check existing [GitHub Issues](https://github.com/CDCgov/tostadas/issues) — someone may have hit the same problem
3. [Open a new issue](https://github.com/CDCgov/tostadas/issues/new/choose) with:
   - Your `nextflow run` command (redact credentials)
   - The relevant section of `.nextflow.log`
   - The `.command.err` from the failing work directory
