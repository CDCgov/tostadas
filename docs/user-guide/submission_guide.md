# Submission Guide

## Quick command template

```bash
nextflow run main.nf \
  -profile <mpox|rsv|bacteria|virus|nwss|pulsenet>,<docker|singularity|conda> \
  --workflow <biosample_and_sra|genbank|full_submission|fetch_accessions|update_submission> \
  --submission_config conf/my_submission_config.yaml \
  --meta_path path/to/metadata.xlsx \
  --prod_submission false   # change to true when ready for production
```

---

## Choosing a workflow

| `--workflow` | When to use it |
|---|---|
| `biosample_and_sra` | First submission: registers samples and uploads reads |
| `genbank` | Submit assembled genomes (requires BioSample accessions) |
| `fetch_accessions` | Pull NCBI reports after submission and update the metadata Excel file |
| `full_submission` | Runs BioSample+SRA, waits, fetches accessions, then runs GenBank — all in one shot |
| `update_submission` | Re-submit updated BioSample metadata |

**GenBank note:** NCBI requires a BioSample accession before accepting a GenBank submission. Run `biosample_and_sra` first, fetch the accessions, add them to your metadata Excel file, then run `genbank`.

---

## Profiles

Use `-profile` to pick your container runtime and optionally a pre-configured organism/program preset:

**Container runtime (pick one):**
- `docker` — Docker Desktop
- `singularity` — Singularity/Apptainer (HPC environments)
- `conda` — conda/mamba (fallback when containers aren't available)

**Organism / program presets (optional, pick one):**

| Profile | BioSample package | Annotator |
|---|---|---|
| `mpox` | Pathogen.cl.1.0 | RepeatMasker + Liftoff |
| `rsv` | Pathogen.cl.1.0 | VADR |
| `bacteria` | Pathogen.cl.1.0 | Bakta |
| `virus` | Pathogen.cl.1.0 | RepeatMasker + Liftoff |
| `nwss` | SARS-CoV-2.wwsurv.1.0 | — |
| `pulsenet` | OneHealthEnteric.1.0 | — |
| `test` | — | Uses bundled test data; dry-run by default |

Profiles stack — separate with commas: `-profile test,mpox,singularity`

---

## Submission config

Copy and fill out `conf/submission_config.yaml`:

```bash
cp conf/submission_config.yaml conf/my_submission_config.yaml
```

Required fields:

| Field | Description |
|---|---|
| `NCBI_username` / `NCBI_password` | Your NCBI Center Account credentials |
| `NCBI_ftp_host` / `NCBI_sftp_host` | NCBI server hostnames |
| `NCBI_Namespace` | Unique submitter SPUID — coordinate with NCBI |
| `BioSample_package` | e.g. `Pathogen.cl.1.0`, `SARS-CoV-2.wwsurv.1.0` |
| `Submitting_Org`, address fields | Organization information |
| `Email` / `First` / `Last` | Contact info |

**Credential alternatives:** Instead of storing credentials in the YAML file, you can use a `.env` file or Nextflow Secrets. See [Installation](installation.md#3-add-ncbi-credentials) for details.

---

## Key parameters

### Batch size

```bash
--batch_size 50
```

Splits large metadata files into chunks of N samples per submission file. We strongly recommend batching — NCBI prefers it. Maximum recommended: 50.

### Test vs. Production

```bash
--prod_submission false   # default — submits to NCBI test server
--prod_submission true    # submits to NCBI production
```

Always test first. The test server validates your credentials and file format without publishing anything.

### Dry run

```bash
--dry_run true    # prepare files, print FTP paths, but don't upload
--dry_run false   # actually upload (default outside of test profile)
```

The `test` profile defaults to `dry_run true`. Add `--dry_run false` to actually connect to the test server.

---

## LLM-assisted features (optional)

With `--use_llm true`, the pipeline calls OpenAI to:

1. **Explain validation errors** in plain English and suggest fixes (`error_llm_suggestions.txt` in validation outputs)
2. **Interpret NCBI report.xml** results and summarize action items (`<batch_id>_llm_interpretation.txt` in submission outputs)

The API key is read from (in priority order): Nextflow Secret `OPENAI_API_KEY` → `.env` file → environment variable.

```bash
# Enable LLM features
nextflow run main.nf ... --use_llm true --llm_model gpt-4o-mini
```

The pipeline runs identically without this flag — it's purely additive.

---

## Custom BioSample packages

TOSTADAS defaults to `Pathogen.cl.1.0`. To use a different package:

1. Set `BioSample_package` in your submission config YAML
2. Add the required fields to your metadata Excel file
3. Create a custom fields JSON (see `assets/custom_meta_fields/example_custom_fields.json`)
4. Pass `--custom_fields_file path/to/fields.json --validate_custom_fields`

The JSON keys control how TOSTADAS validates and renames fields:
- `replace_empty_with` — fill empty cells with this value (e.g., `"Not Provided"`)
- `new_field_name` — rename a column before submission

---

## Walkthrough: full mpox submission

**Step 1 — BioSample and SRA:**

```bash
nextflow run main.nf \
  -profile test,singularity,mpox \
  --workflow biosample_and_sra \
  --dry_run false \
  --submission_config conf/my_submission_config.yaml \
  --batch_size 50
```

**Step 2 — Fetch accessions:**

```bash
nextflow run main.nf \
  -profile test,singularity,mpox \
  --workflow fetch_accessions \
  --dry_run false \
  --submission_config conf/my_submission_config.yaml
```

Open the updated Excel file in `results/<sample_name>/final_submission_outputs/` and verify BioSample accessions were populated.

**Step 3 — GenBank (using the updated Excel with accessions):**

```bash
nextflow run main.nf \
  -profile test,singularity,mpox \
  --workflow genbank \
  --dry_run false \
  --submission_config conf/my_submission_config.yaml \
  --meta_path results/<sample_name>/final_submission_outputs/<sample_name>_updated.xlsx
```

**Step 4 — Switch to Production:**

Once testing is complete, add `--prod_submission true` to any of the above commands.

---

## Walkthrough: bacteria (with Bakta annotation)

```bash
# 1. BioSample + SRA
nextflow run main.nf \
  -profile test,singularity,bacteria \
  --workflow biosample_and_sra \
  --dry_run false \
  --submission_config conf/my_submission_config.yaml

# 2. Open updated Excel and add BioSample accessions, then GenBank:
nextflow run main.nf \
  -profile test,singularity,bacteria \
  --workflow genbank \
  --dry_run false \
  --submission_config conf/my_submission_config.yaml \
  --meta_path results/<sample_name>/final_submission_outputs/<sample_name>_updated.xlsx \
  --download_bakta_db \
  --bakta_db_type light
```

---

## Full parameter reference

See [Parameters](parameters.md) for all available parameters and their defaults.
