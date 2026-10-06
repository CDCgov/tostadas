# Measles Submission Guide

## Overview

This guide covers the process of submitting measles (MeV) consensus sequences to NCBI GenBank using TOSTADAS. The measles profile automates VADR annotation, SQN file generation, and packaging for GenBank submission.

GenBank submission for measles is handled via email rather than FTP. By default, TOSTADAS prepares files for manual submission. The optional `--send_submission_email` flag sends individual `.sqn` attachments when email is configured; see [email submission settings](parameters.md#submission).

## Prerequisites

### VADR Measles Models

The measles profile uses VADR covariance models maintained by the [Greninger Lab](https://github.com/greninger-lab/vadr-models-mev). The pipeline downloads the model file automatically using the URL configured in `vadr_cm_url`. If your compute environment lacks outbound internet access, download the models ahead of time and provide a local path via `--vadr_models_dir`.

### Submission Template (.sbt)

A submission template file is required for table2asn to generate SQN files. There are two options:

- **Provide a pre-existing .sbt file** using `--sbt <path/to/template.sbt>`. This file can be generated from [NCBI's template tool](https://submit.ncbi.nlm.nih.gov/genbank/template/submit/).
- **Let TOSTADAS generate one** from the fields in `submission_config.yaml` (the default behavior when `--sbt` is not set).

## Measles Profile Settings

The `measles` profile (`conf/measles.config`) sets the following parameters:

```groovy
params {
    organism_type       = 'virus'
    virus_subtype       = 'mev'
    mol_type            = 'viral cRNA'
    strip_pub_block     = true
    date_format_flag    = 'n'
    vadr                = true
    completeness_min_coverage = 0.99
}
```

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `virus_subtype` | `mev` | Selects the measles VADR model set |
| `mol_type` | `viral cRNA` | Declares molecule type as complementary RNA (measles is a negative-sense RNA virus) |
| `strip_pub_block` | `true` | Removes publication citation and DBLink blocks from the SQN file, as preferred by NCBI for measles submissions |
| `date_format_flag` | `n` | Formats collection dates in NCBI short month format (`Mon.YY`, e.g., `Jan.25`) |

The profile also sets `completeness_min_coverage = 0.99`. When the metadata completeness field is blank, the pipeline marks a genome complete if VADR model coverage meets this threshold and no truncation is reported. An explicit metadata completeness value takes precedence; set `--completeness_min_coverage 0` to disable inference.

## Metadata Format

Provide metadata as CSV or the supplied Excel template (`.xlsx`) via `--meta_path`. The Python metadata parser also reads TSV/SRC files, but the current Nextflow parameter schema rejects those extensions in normal workflow runs. Convert those inputs to CSV while preserving sample identifiers. The following columns are expected:

| Column | Description | Example |
|--------|-------------|---------|
| `SeqId` | Sequence identifier matching the FASTA header | `MeV_sample_001` |
| `Strain` | WHO-format strain name | `MVs/California.USA/Jan.24` |
| `Country` | Collection country, optionally with state (e.g., `USA:California`) | `USA:California` |
| `Collection_date` | Date of sample collection | `Jan-2024` |
| `organism` | Organism name | `Measles morbillivirus` |
| `Isolate` | Isolate identifier | `MeV/California.USA/Jan.24` |
| `Host` | Host organism | `Homo sapiens` |
| `note` | Free-text notes (optional) | `Genotype D8` |

### NCBI Column Aliasing

TOSTADAS maps the following NCBI source-modifier column names to internal fields. These names can be retained when converting a `.src` file to CSV:

| Source Modifier Column | TOSTADAS Field |
|------------------------|----------------|
| `SeqId` / `SeqID` | `sample_name` |
| `Strain` | `strain` |
| `Collection_date` | `collection_date` |
| `Host` | `host` |
| `Isolate` | `isolate` |

The `Country` field, when provided in `USA:State` format, is automatically split into its component parts.

### WHO Strain Naming Convention

Measles strain names follow the WHO convention: `MVs/State.USA/Mon.YY` (or the equivalent format for other countries). For example:

- `MVs/California.USA/Jan.24`
- `MVs/NewYork.USA/Mar.24`
- `MVs/London.GBR/Feb.24`

The format uses forward slashes as delimiters and abbreviated month-year notation. Ensure strain names in the metadata follow this convention for consistency with GenBank records.

!!! warning "Spaces in Strain Names"
    FASTA headers must not contain spaces. table2asn truncates the sequence ID at the first space, which prevents source modifiers from being applied to the SQN file. Replace spaces with underscores in both the strain name and the FASTA header. For example, use `MVs/South_Dakota.USA/Dec.25/1276` instead of `MVs/South Dakota.USA/Dec.25/1276`. The `geo_loc_name` field should retain the space (e.g., `USA:South Dakota`) as NCBI expects it in that format.

## Running the Pipeline

Measles submissions typically use the GenBank-only workflow because BioSample/SRA registration is handled separately or is not required.

### Basic Command

```bash
nextflow run main.nf \
    -profile measles,singularity \
    --workflow genbank \
    --genbank_only \
    --fasta_dir /path/to/fasta/directory \
    --meta_path /path/to/metadata.csv \
    --sbt /path/to/template.sbt \
    --submission_config conf/submission_config.yaml \
    --dry_run true
```

!!! tip
    Start with `--dry_run true` to verify that all files are generated correctly before preparing a real submission.

### Parameter Notes

- `--genbank_only` skips BioSample/SRA-specific validation (SPUID, authors, isolation_source checks), which is appropriate when generating SQN files without registering BioSamples.
- `--fasta_dir` points to a directory containing FASTA files. The pipeline matches each file to the corresponding `sample_name` in the metadata by filename (without extension).
- `--sbt` provides the submission template. If omitted, TOSTADAS generates one from `submission_config.yaml`.

## GenBank Submission

For manual submission with `--send_submission_email false`:

1. Run the pipeline to generate submission files.
2. Locate the zip archives in `results/submission/genbank/batch_*/genbank/<sample>/`.
3. Email the zip file(s) to **gb-sub@ncbi.nlm.nih.gov**.
4. NCBI will process the submission and reply with accession numbers.

!!! note
    NCBI does not support FTP-based GenBank submission for most viruses (excluding SARS-CoV-2 and influenza). Email is the required submission method for measles.

### Batch Size Considerations

`--batch_size` controls how metadata is grouped for pipeline tasks. The measles preparation code still creates a separate directory and archive for each sample; increasing the batch size does not combine those archives into one submission package.

## Expected Output Files

After a successful run, the following files are produced:

| Directory | Files | Description |
|-----------|-------|-------------|
| `results/validation/` | `batched_tsvs/batch_*.tsv`, `error.txt` | Validated metadata and any validation errors |
| `results/annotation/vadr/` | `batch_pass_fail.tsv`, `batch_alerts.tsv` | VADR annotation summary |
| `results/annotation/vadr/<sample>/gffs/` | `*.gff` | Annotation files per sample |
| `results/annotation/vadr/<sample>/tbl/` | `*.tbl` | Feature tables per sample |
| `results/submission/genbank/batch_*/genbank/<sample>/` | `*.sqn`, `*.zip` | SQN files and submission zip archives |
