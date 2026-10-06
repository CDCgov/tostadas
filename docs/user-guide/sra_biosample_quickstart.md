# SRA + BioSample Quickstart (creating new BioSamples)

A start-to-finish path for submitting paired-end reads to SRA and registering new BioSamples in one run, for samples going into an **existing BioProject**. Running example: clinical *Streptococcus pneumoniae* isolates.

Use this branch: `feature/sra-biosample-primaryid`.

**Use this path when:**

- Your BioSamples do **not** exist yet (the pipeline creates them), and
- You are adding to an **existing** BioProject.

If your BioSamples already exist, put their `SAMN` in the `biosample_accession` column and the pipeline will link the SRA to them and skip creating duplicates.

---

## 1. Install

Follow [installation.md](installation.md): install mamba/conda, Nextflow, and a container engine (Docker or Singularity), then clone this branch.

```bash
git clone -b feature/sra-biosample-primaryid https://github.com/jforstedt/tostadas.git
cd tostadas
```

Confirm the environment works by running the bundled test once (see installation.md).

## 2. Build the metadata sheet

Start from the template `assets/sample_metadata/bacteria_test_metadata.xlsx` (it already has a worked *C. diphtheriae* example row). Use Excel or `.csv`, with one row per sample. The Python reader supports `.tsv` and `.src`, but workflow parameter validation currently rejects those extensions; convert them to CSV or Excel first.

- Delete the `test_field_*` columns.
- For SRA + BioSample only (no genome assembly), you can ignore the Assembly columns (`fasta_path`, `gff_path`, `assembly_*`).

Fill these columns per sample:

**Identity and linkage**

| Column | What to put |
|---|---|
| `sample_name` | your sample id (no periods) |
| `ncbi-spuid` | a unique BioSample SPUID for the sample |
| `ncbi-spuid-sra` | a unique SRA SPUID for the sample; check uniqueness before submitting |
| `ncbi-bioproject` | your existing BioProject accession (e.g. `PRJNA######`) |
| `biosample_accession` | **leave blank** so the pipeline creates the BioSample |

**BioSample fields (Pathogen.cl clinical package)**

`organism` (e.g. `Streptococcus pneumoniae`), `isolate` and/or `strain`, `collection_date`, `country`, `state`, `host` (e.g. `Homo sapiens`), `isolation_source`, `host_disease`, `collected_by`, `sample_type`, `source_type`, `purpose_of_sampling`, `lat_lon`, plus the submission/contact fields `title`, `description`, `authors`, `submitting_lab`, `submitting_lab_division`, `submitting_lab_address`, `publication_status`.

- Unknown values can be `Not provided` where the package allows (the example row uses this for `collected_by`, `sample_type`, `lat_lon`).
- `collection_date` in ISO 8601 (`YYYY-MM-DD` or `YYYY-MM`) or `Mon-YYYY`.

**SRA fields (Illumina paired-end)**

| Column | Example |
|---|---|
| `illumina_sequencing_instrument` | `Illumina MiSeq` |
| `illumina_library_strategy` | `WGS` |
| `illumina_library_source` | `GENOMIC` |
| `illumina_library_selection` | `RANDOM` |
| `illumina_library_layout` | `PAIRED` |
| `illumina_library_name`, `illumina_library_protocol` | your values |
| `file_location` | `local` |
| `illumina_sra_file_path_1` | path to the R1 fastq |
| `illumina_sra_file_path_2` | path to the R2 fastq |

**Gotchas**

- No periods (`.`) in fastq file names or sample names.
- `ncbi-spuid` and `ncbi-spuid-sra` must each be unique across the whole sheet and must differ within each row. Check SRA SPUID uniqueness before uploading; report aggregation checks it later, after submission.
- The tested path is paired-end reads.

## 3. Configure the submission

Edit `conf/submission_config.yaml`:

- `NCBI_username`, `NCBI_password` — the submission-account credentials for the configured FTP/SFTP endpoint.
- `NCBI_ftp_host` for FTP, or `NCBI_sftp_host` when using `--submission_mode sftp` — the endpoint configured for those credentials.
- `BioSample_package: "Pathogen.cl.1.0"` — the clinical bacterial package, already the default. Change only if your BioProject registered its samples under a different package.
- `Submitting_Org`, `Submitter`, `Submission_Title` — your org and contact.

## 4. Test run (NCBI test server)

Validate the metadata and submit to NCBI's **test** server first:

```bash
nextflow run main.nf -profile test,singularity,bacteria \
  --workflow biosample_and_sra --dry_run false \
  --submission_config conf/submission_config.yaml \
  --meta_path path/to/your_metadata.xlsx \
  --outdir results/test_submission --prod_submission false \
  --batch_size 100
```

- `-profile test` with `--dry_run false` submits to the test server (without `--dry_run false` it only prepares files).
- `--workflow biosample_and_sra` registers the BioSamples and submits the SRA together.
- Fix any validation errors reported, then rerun. The validation step is the authoritative list of which required fields are missing.

## 5. Fetch the assigned accessions

Pull the current BioSample and SRA reports into an updated metadata file. Use the same metadata path, output directory, and production/test setting as the submission:

```bash
nextflow run main.nf -profile test,singularity,bacteria \
  --workflow fetch_accessions --dry_run false \
  --submission_config conf/submission_config.yaml \
  --meta_path path/to/your_metadata.xlsx \
  --outdir results/test_submission --prod_submission false
```

Keep `validation/validated_metadata_all_samples.tsv` in that output directory: it supplies the BioSample/SRA identifier mapping. The updated workbook keeps one row per sample and separates multiple SRA accessions with semicolons. For a production run, fetch with its original output directory and `--prod_submission true`. This workflow downloads current reports; replacing local reports with older successful copies is not an offline recovery method. See [troubleshooting.md](troubleshooting.md#combining-biosample-and-sra-accessions) for reconciliation guidance.

## 6. Production and batching

Once a test batch goes through cleanly, submit to production following the **Submitting to Production** section of [submission_guide.md](submission_guide.md). Start with a modest `--batch_size` (100 to 500) and scale toward 1000 while watching that read-file transfer completes and NCBI accepts each batch. For ~10k samples that is roughly 10 to 20 batches.

## Reference

- [installation.md](installation.md) — environment setup
- [submission_guide.md](submission_guide.md) — full workflow and parameters, Running SRA Submission Only, Submitting to Production, SFTP mode
- [parameters.md](parameters.md) — every parameter
