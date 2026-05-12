# Wastewater Surveillance Submission Guide

TOSTADAS supports submission of wastewater surveillance sequencing data to NCBI BioSample and SRA. This guide covers the setup and step-by-step submission process.

---

## Overview

A wastewater submission requires three things:
1. An NCBI Center Account with a linked BioProject
2. An Excel metadata file using the wastewater template
3. FASTQ files for each sample

The pipeline handles metadata validation, BioSample registration, and SRA upload automatically.

---

## Prerequisites

- [Nextflow installed](installation.md)
- [NCBI Center Account](general_NCBI_submission_guide.md#ncbi-center-account)
- A BioProject — create one at [NCBI BioProject](https://submit.ncbi.nlm.nih.gov/subs/bioproject/)
- FASTQ files for your samples (paired-end or single-end)

> **For NWSS (SARS-CoV-2 wastewater surveillance):** Link your BioProject to the NWSS umbrella BioProject `PRJNA747181` when you create it.

---

## Step 1 — Set up your metadata

Download the wastewater metadata template:

```bash
# SARS-CoV-2 wastewater
wget https://github.com/CDCgov/tostadas/raw/master/assets/sample_metadata/wastewater_biosample_template.xlsx
```

Fill out the template following the examples in the sheet. Required fields include:
- Sample identifiers and collection dates
- Geographic location (lat/lon optional but encouraged)
- Wastewater treatment plant / collection site information
- Concentration method and target gene(s)

Save your completed file with a descriptive name — this becomes the root name for all output directories.

---

## Step 2 — Configure submission credentials

```bash
cp conf/submission_config.yaml conf/my_wastewater_config.yaml
```

Key fields for wastewater:

```yaml
BioSample_package: SARS-CoV-2.wwsurv.1.0  # or your pathogen-specific package
NCBI_username: your_username
NCBI_password: your_password
NCBI_Namespace: YOUR_NAMESPACE   # coordinate with NCBI
```

See [Installation](installation.md#3-add-ncbi-credentials) for credential alternatives (`.env` file, Nextflow Secrets).

---

## Step 3 — Test your setup

Run against the bundled test data to confirm your environment and credentials work:

```bash
nextflow run main.nf \
  -profile nwss,test,singularity
```

This uses the included wastewater test data and prepares submission files without uploading. If it completes without errors, you're ready for the next step.

---

## Step 4 — Test with a small batch of real samples

Submit 2–5 of your actual samples to the NCBI test server:

```bash
nextflow run main.nf \
  -profile nwss,singularity \
  --workflow biosample_and_sra \
  --meta_path path/to/your_metadata.xlsx \
  --submission_config conf/my_wastewater_config.yaml \
  --batch_size 5 \
  --outdir results/test_run \
  --dry_run false
```

Log in to the [NCBI Submission Portal](https://submit.ncbi.nlm.nih.gov/) to verify the test submission was received and processed correctly.

---

## Step 5 — Submit to production

Once the test run looks good, submit your full dataset to the production server:

```bash
nextflow run main.nf \
  -profile nwss,singularity \
  --workflow biosample_and_sra \
  --meta_path path/to/your_metadata.xlsx \
  --submission_config conf/my_wastewater_config.yaml \
  --batch_size 50 \
  --outdir results/production_run \
  --prod_submission true \
  --dry_run false
```

> **Tip:** Use `--batch_size 50` or less. NCBI prefers batched submissions and large single batches can time out.

---

## Step 6 — Fetch accession IDs

After NCBI processes the submission (typically within a few hours):

```bash
nextflow run main.nf \
  -profile nwss,singularity \
  --workflow fetch_accessions \
  --submission_config conf/my_wastewater_config.yaml \
  --outdir results/production_run \
  --prod_submission true \
  --dry_run false
```

This creates an updated Excel file with BioSample and SRA accession IDs filled in, plus a `submission_report.csv` summary.

---

## Using a different BioSample package

The `nwss` profile defaults to `SARS-CoV-2.wwsurv.1.0`. For other pathogens (e.g., measles, influenza, polio):

1. Find your package at [NCBI BioSample Packages](https://www.ncbi.nlm.nih.gov/biosample/docs/packages/)
2. Set `BioSample_package` in your submission config
3. Download the appropriate template or adapt the wastewater template with required fields
4. If your package needs custom fields, create a custom fields JSON and use `--custom_fields_file` + `--validate_custom_fields`
5. Use the `-profile singularity` (or `docker`) without the `nwss` preset, and specify `--meta_path` directly

Example for a non-SARS-CoV-2 wastewater submission:

```bash
nextflow run main.nf \
  -profile singularity \
  --workflow biosample_and_sra \
  --meta_path path/to/your_metadata.xlsx \
  --submission_config conf/my_config.yaml \
  --custom_fields_file assets/custom_meta_fields/my_package_fields.json \
  --validate_custom_fields \
  --prod_submission true \
  --dry_run false
```

---

## LLM-assisted validation (optional)

For large or complex metadata files, enable LLM-powered validation hints:

```bash
nextflow run main.nf \
  -profile nwss,singularity \
  ... \
  --use_llm true
```

The pipeline will write plain-English suggestions for any validation errors to `validation_outputs/errors/error_llm_suggestions.txt`. Requires `OPENAI_API_KEY` set in `.env` or as a Nextflow Secret.

---

## Troubleshooting

See [Troubleshooting](troubleshooting.md) for common issues. Wastewater-specific tips:

- **Missing required fields:** Cross-reference your Excel against the NCBI package spec. The `wwsurv.1.0` package requires fields like `env_broad_scale`, `env_local_scale`, `env_medium` — check that all are present and correctly spelled
- **Submission hangs:** Check network connectivity to NCBI FTP/SFTP hosts. If on a VPN, some organizations block outbound FTP — try `--submission_mode sftp`
- **Accessions not returned:** NCBI processes wastewater batches in queues; allow several hours before running `fetch_accessions`
