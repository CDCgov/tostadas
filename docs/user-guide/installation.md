# Installation

## Table of Contents

- [Environment Setup](#environment-setup)
  - [Dependencies](#dependencies)
  - [(1) Clone the repository to your local machine](#1-clone-the-repository-to-your-local-machine)
  - [(2) Install mamba and add it to your PATH](#2-install-mamba-and-add-it-to-your-path)
  - [(3) Install Nextflow using mamba and the bioconda Channel](#3-install-nextflow-using-mamba-and-the-bioconda-channel)
- [Run a test submission](#run-a-test-submission)
  - [(1) Update the default submissions config file with your NCBI username and password](#1-update-the-default-submissions-config-file-with-your-ncbi-username-and-password)
  - [(2) Run the workflow with default parameters and the local run environment](#2-run-the-workflow-with-default-parameters-and-the-local-run-environment)
- [Start submitting your own data](#start-submitting-your-own-data)
)

## Environment Setup

### Dependencies:

*   Nextflow v. 21.10.3 or newer
*   Compute environment (docker, singularity or conda)

❗ Note: If you are a CDC user, please follow the set-up instructions found on this page: [CDC User Guide](../user-guide/cdc-user-guide.md)

### (1) Clone the repository to your local machine:

*   `git clone https://github.com/CDCgov/tostadas.git`

❗ Note: If you already have Nextflow installed in your local environment, skip ahead to step 5.

### (2) Install mamba and add it to your PATH

2a. Install mamba

❗ Note: If you have mamba installed in your local environment, skip ahead to step 3 ([Create and activate a conda environment](#3-create-and-activate-a-conda-environment))

`curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh`

`bash Mambaforge-$(uname)-$(uname -m).sh -b -p $HOME/mambaforge`

2b. Add mamba to PATH:

`export PATH="$HOME/mambaforge/bin:$PATH"`

### (3) Install Nextflow using mamba and the bioconda Channel

`mamba install -c bioconda nextflow`

## Run a test submission

### (1) Update the default submissions config file with your NCBI username and password

`# update this config file (you don't have to use vim)`

`vim conf/submission_config.yaml`

### (2) Run the workflow with default parameters and the local run environment

`# test command for virus reads`

`nextflow run main.nf -profile mpox,test,<singularity|docker|conda> --workflow biosample_and_sra`

The pipeline outputs appear in `tostadas/results`

## Start submitting your own data

Create an NCBI Center Account. See [NCBI Center Account](general_NCBI_submission_guide.md#ncbi-center-account)

Choose a workflow and specify your profile or (optionally, for annotation and GenBank submission) an `organism_Type` and `virus_subtype`.  See: [Putting together the Nextflow command](submission_guide.md#putting-together-the-nextflow-command)




