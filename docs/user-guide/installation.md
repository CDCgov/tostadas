# Installation

## Environment Setup

### Dependencies

- Nextflow v. 24.04.0 or newer (see [Nextflow Version Compatibility](#nextflow-version-compatibility) below)
- Compute environment (docker, singularity or conda)

### Nextflow Version Compatibility

This pipeline uses the **nf-schema@2.3.0** plugin for parameter validation, which requires **Nextflow 23.10.0 or later**. The minimum supported version for TOSTADAS is **24.04.0**.

| Nextflow Version | Status                   |
|------------------|--------------------------|
| 25.10.4          | Tested on HPC            |
| latest-edge      | Tested in CI             |
| 24.04.0+         | Minimum supported version|
| < 24.04.0        | Not supported            |

!!! note "nf-schema plugin"
    Users running Nextflow v24 or later may see a warning that the nf-schema plugin must be installed. To resolve this, install the plugin manually by following the [Nextflow offline plugin usage instructions](https://www.nextflow.io/docs/latest/plugins.html#offline-usage).

!!! note
    If you are a CDC user, please follow the set-up instructions found on this page: [CDC User Guide](../user-guide/cdc-user-guide.md)

### Clone the Repository

```bash
git clone https://github.com/CDCgov/tostadas.git
```

!!! note
    If you already have Nextflow installed in your local environment, proceed to the [Run a test submission](#run-a-test-submission) section below.

### Install Mamba

**Install mamba:**

!!! note
    If you have mamba installed in your local environment, proceed to the [Install Nextflow](#install-nextflow) section below.

```bash
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh
```

```bash
bash Mambaforge-$(uname)-$(uname -m).sh -b -p $HOME/mambaforge
```

**Add mamba to PATH:**

```bash
export PATH="$HOME/mambaforge/bin:$PATH"
```

### Install Nextflow

```bash
mamba install -c bioconda nextflow
```

## Run a test submission

### Update the Submission Config

```bash
# update this config file (you don't have to use vim)
vim conf/submission_config.yaml
```

### Run the Test Workflow

```bash
# test command for virus reads
nextflow run main.nf -profile mpox,test,<singularity|docker|conda> --workflow biosample_and_sra
```

The pipeline outputs appear in `tostadas/results`

## Start submitting your own data

Create an NCBI Center Account. See [NCBI Center Account](general_NCBI_submission_guide.md#ncbi-center-account)

Choose a workflow and specify your profile or (optionally, for annotation and GenBank submission) an `organism_Type` and `virus_subtype`. See: [Putting together the Nextflow command](submission_guide.md#putting-together-the-nextflow-command)

**Please read** the [Submission Guide](submission_guide.md) for important details about parameters you need to specify. Please especially note the following:

- `--prod_submission` -- true/false (for submitting to Test vs. Production server). See [Other customizations](submission_guide.md#other-customizations)
- `--batch_size` -- for submitting large datasets in chunks. We **highly** recommend you submit using batches. See [Other customizations](submission_guide.md#other-customizations)
- `--workflow` -- read how to use TOSTADAS for different types of submissions. See [Submitting to Production](submission_guide.md#submitting-to-production)
- Profiles -- read about profile shortcuts in [Using specific profiles](submission_guide.md#using-specific-profiles)
