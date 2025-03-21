# Installation

## Environment Setup

### Dependencies:

*   Nextflow v. 21.10.3 or newer
*   Compute environment (docker, singularity or conda)

❗ Note: If you are a CDC user, please follow the set-up instructions found on this page: [CDC User Guide](https://github.com/CDCgov/tostadas/wiki/CDC-User-Guide)

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

`nextflow run main.nf -profile test,<singularity|docker|conda> --virus`

The pipeline outputs appear in `tostadas/test_output`

### (6) Start running your own analysis

**Annotate and submit viral reads**

`nextflow run main.nf -profile <docker|singularity> --species virus --submission --annotation --genbank true --sra true --biosample true --output_dir <path/to/output/dir/> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml>`

**Annotate and submit bacterial reads**

`nextflow run main.nf -profile <docker|singularity> --species bacteria --submission --annotation --genbank true --sra true --biosample true --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --download_bakta_db --bakta_db_type <light|full> --output_dir <path/to/output/dir/>`

Refer to the wiki for more information on input parameters and use cases

### (7) Custom metadata validation and custom BioSample package

TOSTADAS defaults to Pathogen.cl.1.0 (Pathogen: clinical or host-associated; version 1.0) NCBI BioSample package for submissions to the BioSample repository. You can submit using a different BioSample package by doing the following:

1.  Change the package name in the `conf/submission_config.yaml`. Choose one of the available [NCBI BioSample packages](https://www.ncbi.nlm.nih.gov/biosample/docs/packages/).
2.  Add the necessary fields for your BioSample package to your input Excel file.
3.  Add those fields as keys to the JSON file (`assets/custom_meta_fields/example_custom_fields.json`) and provide key info as needed.

replace\_empty\_with: TOSTADAS will replace any empty cells with this value (Example application: NCBI expects some value for any mandatory field, so if empty you may want to change it to "Not Provided".)

new\_field\_name: TOSTADAS will replace the field name in your metadata Excel file with this value. (Example application: you get weekly metadata Excel files and they specify 'animal\_environment' but NCBI expects 'animal\_env'; you can specify this once in the JSON file and it will be changed on every run.)

**Submit to a custom BioSample package**

`nextflow run main.nf -profile <docker|singularity> --species virus --submission --annotation --genbank true --sra true --biosample true --output_dir <path/to/output/dir/> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --custom_fields_file <path/to/metadata_custom_fields.json>`
