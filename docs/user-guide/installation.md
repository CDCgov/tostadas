# Installation

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

### (4) Update the default submissions config file with your NCBI username and password

`# update this config file (you don't have to use vim)`

`vim conf/submission_config.yaml`

### (5) Run the workflow with default parameters and the local run environment

`# test command for virus reads`

`nextflow run main.nf -profile mpox,test,<singularity|docker|conda> --workflow biosample_and_sra`

The pipeline outputs appear in `tostadas/results`

### (6) Start running your own analysis

**Submit viral reads **



