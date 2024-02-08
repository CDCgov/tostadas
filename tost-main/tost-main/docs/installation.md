# Installation

## Environment Setup
❗ Note: If you are a CDC user, please follow the set-up instructions found on Page X - CDC User Guide

(1) Clone the repository to your local machine:
* `git clone https://github.com/CDCgov/tostadas.git`
❗ Note: If you have mamba or nextflow installed in your local environment, you may skip steps 2, 3 (mamba installation) and 6 (nextflow installation) accordingly.

(2) Install Mamba:
* `curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh`
* `bash Mambaforge-$(uname)-$(uname -m).sh -b -p $HOME/mambaforge`
(3) Add mamba to PATH:
* `export PATH="$HOME/mambaforge/bin:$PATH"`
(4) Create the conda environment:
If you want to create the full-conda environment needed to run the pipeline outside of Nextflow (this enables you to run individual python scripts), then proceed with step 4a.

If you want to run the pipeline using nextflow only (this will be most users), proceed with step 4b. Nextflow will handle environment creation and you would only need to install the nextflow package locally vs the entire environment.

       (4a) Create the conda environment and install the dependencies set in your environment.yml:

* `cd tostadas`
* `mamba env create -n tostadas -f environment.yml`   
       (4b) Create an empty conda environment:

* `conda create --name tostadas`
(5) Activate the environment.
* `conda activate tostadas`
Verify which environment is active by running the following conda command: * `conda env list` . The active environment will be denoted with an asterisk *

(6) Install Nextflow using Use Mamba and the Bioconda Channel:
* `mamba install -c bioconda nextflow`
❗ Optionally, you may install nextflow without mamba by following the instructions found in the Nextflow Installation Documentaion Page: 

## Nextflow Install

(7) Ensure Nextflow was installed successfully by running nextflow -v
Expected Output:

* `nextflow version <CURRENT VERSION>`
The exact version of Nextflow returned will differ from installation to installation. It is important that the command execute successfully, and a version number is returned.

(8) Run one of the following nextflow commands to execute the scripts with default parameters and the local run environment:
### For Virus Reads
* `nextflow run main.nf -profile test,<singularity/docker/conda> --virus`
### For Bacterial Reads
* `nextflow run main.nf -profile test,<singularity/docker/conda> --bacteria` 
The outputs of the pipeline will appear in the test_output folder within the project directory. You can specify an output directory in the config file or by supplying a path to the --output_dir flag in your nextflow run command.