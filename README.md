# TOSTADAS &#8594; <span style="color:blue"><u>**T**</u></span>oolkit for <span style="color:blue"><u>**O**</u></span>pen <span style="color:blue"><u>**S**</u></span>equence <span style="color:blue"><u>**T**</u></span>riage, <span style="color:blue"><u>**A**</u></span>nnotation and <span style="color:blue"><u>**DA**</u></span>tabase <span style="color:blue"><u>**S**</u></span>ubmission :dna: :computer:

## PATHOGEN ANNOTATION AND SUBMISSION PIPELINE

<!-- [![GitHub Downloads](https://img.shields.io/github/downloads/CDCgov/tostadas/total.svg?style=social&logo=github&label=Download)](https://github.com/CDCgov/tostadas/releases) -->
[![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A521.10.3-23aa62.svg?labelColor=000000)](https://www.nextflow.io/) [![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/) [![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/) [![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)

## Overview
 TOSTADAS is designed to fulfill common sequence submission use cases. The tool runs three sub-processes: 
1. Metadata Validation – This workflow checks if metadata conforms to NCBI standards and matches the input .fasta file(s)
2. Gene Annotation – This workflow runs gene annotation on fasta-formatted genomes using one of three annotation methods: RepeatMasker and Liftoff, VADR or BAKTA
3. Submission – This workflow generates the necessary files and information for submission to NCBI and optionally and optionally submit to NCBI. 

TOSTADAS is flexible, allowing you to choose which portions of the pipeline to run and which to skip. For example, you can submit .fastq files and metadata without performing gene annotation.   

 The current distribution has been tested with Pox virus sequences as well as some bacteria. Ongoing development aims to make the pipeline pathogen agnostic.

## Environment Setup 

:exclamation: Note: If you are a CDC user, please follow the set-up instructions found here: [CDC User Guide](Link)

#### (1) Install Nextflow using Use Mamba and the Bioconda Channel:

There are several options for install if you don't already have nextflow on your system. 

```bash
mamba install -c bioconda nextflow
```
:exclamation: Optionally, you may install nextflow without mamba by following the instructions found in the Nextflow Installation Documentation Page: [Nextflow Install](https://www.nextflow.io/docs/latest/getstarted.html)

#### (1) Clone the repository to your local machine:  
```bash
git clone https://github.com/CDCgov/tostadas.git
```
:exclamation: Note: If you have mamba or nextflow installed in your local environment, you may skip steps 2, 3 (mamba installation) and 6 (nextflow installation) accordingly. 

#### (2) Install Mamba:
```bash
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh
bash Mambaforge-$(uname)-$(uname -m).sh -b -p $HOME/mambaforge
```
#### (3) Add mamba to PATH:
```bash
export PATH="$HOME/mambaforge/bin:$PATH"
```

#### (4) Create the conda environment: 

If you want to create the full-conda environment needed to run the pipeline outside of Nextflow (this enables you to run individual python scripts), then proceed with step **4a**. 

If you want to run the pipeline using nextflow only (this will be most users), proceed with step 4b. Nextflow will handle environment creation and you would only need to install the nextflow package locally vs the entire environment.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **(4a) Create the conda environment and install the dependencies set in your environment.yml:**   

```bash
cd tostadas
mamba env create -n tostadas -f environment.yml   
```
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **(4b) Create an empty conda environment:**
```bash
conda create --name tostadas
```
#### (5) Activate the environment. 
```bash
conda activate tostadas
```
Verify which environment is active by running the following conda command: `conda env list`  . The active environment will be denoted with an asterisk `*`

#### (6) Install Nextflow using Use Mamba and the Bioconda Channel:

```bash
mamba install -c bioconda nextflow
```
:exclamation: Optionally, you may install nextflow without mamba by following the instructions found in the Nextflow Installation Documentaion Page: [Nextflow Install](https://www.nextflow.io/docs/latest/getstarted.html)

#### (7) Ensure Nextflow was installed successfully by running ```nextflow -v```

Expected Output:
```
nextflow version <CURRENT VERSION>
```
The exact version of Nextflow returned will differ from installation to installation.  It is important that the command execute successfully, and a version number is returned.

#### (8) Test your installation by running one of the following nextflow commands on test data

```bash
# for virus reads
nextflow run main.nf -profile test,<singularity/docker/conda> --virus
# for bacterial reads
nextflow run main.nf -profile test,<singularity/docker/conda> --bacteria 
```

The outputs of the pipeline will appear in the ```test_output``` folder within the project directory. You can specify an output directory in the config file or by supplying a path to the ```--output_dir``` flag in your ```nextflow run``` command.

#### (9) Start running your own analysis
**Annotate and submit viral reads**
```{bash}
nextflow run main.nf -profile docker --virus --fasta_path <path/to/fasta/files> ---meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml>
```
**Annotate and submit bacterial reads**
```{bash}
nextflow run main.nf -profile docker --bacteria --fasta_path <path/to/fasta/files> ---meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --download_bakta_db --bakta_db_type <light/full>
```
Refer to the [wiki](https://github.com/CDCgov/tostadas/wiki) for more information on input parameters and use cases 
## Get in Touch

If you have any ideas for ways to improve our existing codebase, feel free to open an Issue Request (found here: [Open New Issue](https://github.com/CDCgov/tostadas/issues/new/choose))

### Steps to Open Issue Request:
  
#### **(1) Select Appropriate Template**
  Following the link above, there are four options for issue templates and your selection will depend on (1) if you are a user vs maintainer/collaborator and (2) if the request pertains to a bug vs feature enhancement. Please select the template that accurately reflects your situation. 

#### **(2) Fill Out Necessary Information**
  Once the appropriate template has been selected, you must fill/answer all fields/questions specified. The information provided will be valuable in getting more information about the issue and any necessary context surrounding it.

#### **(3) Submit the Issue**

Once all information has been provided, you may now submit it!

Please allow for some turnaround time for us to review the issue and potentially start addressing it. If this is an urgent request and have not heard from us nor see any progress being made after quite some time (longer than a week), feel free to start a discussion (found here: [Start New Discussion](https://github.com/CDCgov/tostadas/discussions)) mentioning the following: 
  * Issue Number 
  * Date Submitted
  * General Background on Bug/Feature 
  * Reason for Urgency

  And we will get back to you as soon as possible. 
