# Installation

## Requirements

| Requirement | Minimum version | Notes |
|---|---|---|
| Nextflow | 23.04+ | Install via `mamba install -c bioconda nextflow` |
| Container runtime | Any one of: Docker, Singularity, or conda | Singularity/Docker recommended |
| NCBI Center Account | — | [Setup instructions](general_NCBI_submission_guide.md#ncbi-center-account) |

> **CDC users:** follow the [CDC User Guide](cdc-user-guide.md) instead of these instructions.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/CDCgov/tostadas.git
cd tostadas
```

### 2. Install Nextflow (skip if already installed)

```bash
# Install mamba if you don't have it
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh
bash Mambaforge-$(uname)-$(uname -m).sh -b -p $HOME/mambaforge
export PATH="$HOME/mambaforge/bin:$PATH"

# Install Nextflow
mamba install -c bioconda nextflow
```

### 3. Add NCBI credentials

Copy the template and fill in your credentials:

```bash
cp conf/submission_config.yaml conf/my_submission_config.yaml
```

Open `conf/my_submission_config.yaml` and fill in:
- `NCBI_username` / `NCBI_password`
- `NCBI_Namespace` (coordinate with NCBI)
- `Submitting_Org`, contact info, etc.

**Alternative — use a `.env` file (local runs):**

```bash
cp .env.example .env
# Edit .env and set NCBI_USERNAME and NCBI_PASSWORD
```

The pipeline reads from `.env` automatically if `conf/submission_config.yaml` credentials are blank.

**Alternative — use Nextflow Secrets (Seqera Platform / shared environments):**

```bash
nextflow secrets set NCBI_USERNAME your_username
nextflow secrets set NCBI_PASSWORD your_password
```

### 4. (Optional) Enable LLM features

TOSTADAS can use OpenAI to explain metadata validation errors and interpret NCBI report files in plain English. This is entirely optional — the pipeline runs identically without it.

```bash
# Copy the example and set your key
cp .env.example .env
# Set OPENAI_API_KEY=sk-... in .env
```

Then enable in your run command: `--use_llm true`

See `.env.example` for all credential options including Nextflow Secrets setup for cloud runs.

---

## Run a test submission

```bash
nextflow run main.nf \
  -profile test,mpox,singularity \
  --workflow biosample_and_sra \
  --submission_config conf/my_submission_config.yaml
```

The test profile prepares all files but does not upload to NCBI (dry run). To actually submit to the NCBI test server, add `--dry_run false`.

Outputs appear in `tostadas/results/`.

---

## Start submitting your own data

1. Read the [Submission Guide](submission_guide.md) — especially `--prod_submission`, `--batch_size`, and `--workflow`
2. Fill out your metadata Excel file using one of the templates in `assets/sample_metadata/`
3. Choose your workflow and profile, then run

See [Parameters](parameters.md) for the full parameter reference.
