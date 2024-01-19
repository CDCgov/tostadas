# TOSTADAS &#8594; <span style="color:blue"><u>**T**</u></span>oolkit for <span style="color:blue"><u>**O**</u></span>pen <span style="color:blue"><u>**S**</u></span>equence <span style="color:blue"><u>**T**</u></span>riage, <span style="color:blue"><u>**A**</u></span>nnotation and <span style="color:blue"><u>**DA**</u></span>tabase <span style="color:blue"><u>**S**</u></span>ubmission :dna: :computer:

## PATHOGEN ANNOTATION AND SUBMISSION PIPELINE

<!-- [![GitHub Downloads](https://img.shields.io/github/downloads/CDCgov/tostadas/total.svg?style=social&logo=github&label=Download)](https://github.com/CDCgov/tostadas/releases) -->
[![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A521.10.3-23aa62.svg?labelColor=000000)](https://www.nextflow.io/) [![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/) [![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/) [![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)

## Overview
The Pathogen Annotation and Submission pipeline facilitates the running of several Python scripts, which validate metadata (QC), annotate assembled genomes, and submit to NCBI. Current implementation has been tested with Pox virus sequences as well as some bacteria. Ongoing development aims to make the pipeline pathogen agnostic.

## Documentation 
For in-depth documentation on the features of Tostadas, check out our Wiki page: [Tostadas Wiki](https://github.com/CDCgov/tostadas/wiki)! 

## Pipeline Summary

### 1.1 Metadata Validation
The validation workflow checks if metadata conforms to NCBI standards and matches the input fasta file. The script also splits a multi-sample xlsx file into a separate .tsv file for each individual.

Recently, we have added the ability to pass in the names of custom metadata fields, in order to carry out a variety of checks and modifications. You have the ability to specify check/modifcation properties for each custom field within a .JSON file and consists of the following:
* Name of samples to apply checks/mods
* Data type check and potential casting
* Populated vs empty check
* Replacement for empty values
* New name for field 

A comprehensive guide for custom metadata fields can be found here: [Custom Metadata Guide](./docs/custom_metadata_guide.md)

### 1.2 Gene Annotation

Currently, consists of three annotation options:
* (1) Liftoff 
    * The liftoff workflow annotates input fasta-formatted genomes and produces accompanying gff and genbank tbl files. The input includes the reference genome fasta, reference gff, single-sample fasta files, and metadata in .xlsx format. The [Liftoff](https://github.com/agshumate/Liftoff) workflow was brought over and integrated from the Liftoff tool, responsible for accurately mapping annotations for assembled genomes. We recently integrated [RepeatMaster](https://www.repeatmasker.org/) into this workflow, and the updated workflow used RepeatMasker to annotate repeats, and Liftoff to annotate functional regions, then combines the GFF outputs. RepeatMasker was added to support variola in addition to MPOX. Be sure to specifiy the correct database in the params for this option.
* (2) VADR
    * The VADR workflow annotates input fasta-formatted genomes and generates gff / tbl files. The inputs into this workflow are your single-sample fasta files, metadata in .xlsx format, and reference information for the pathogen genome which is included within [this repository](https://github.com/CDCgov/tostadas/tree/master/vadr_files/mpxv-models). Find out more at the [VADR GitHub Repo](https://github.com/ncbi/vadr).
* (3) Bakta
    * The Bakta workflow annotates input fasta-formatted bacterial genomes & plasmids and generates gff / tbl files. The inputs into this workflow are single-sample fasta files, metadata in .xlsx format, and optionally a reference database used for annotation (found [here](https://zenodo.org/records/7669534)). Bakta is an existing bacterial annotation tool that was integrated into the pipeline. You can find more information about this tool at the following link: [Bakta Git Repo](https://github.com/CDCgov/tostadas/tree/master#gene-annotation).

### 1.3 Submission 
Submission workflow generates the necessary files for Genbank submission, generates a BioSample ID, then optionally uploads Fastq files via FTP to SRA. This workflow was adapted from [SeqSender](https://github.com/CDCgov/seqsender) public database submission pipeline.

## Setup

### Repository Setup

Before cloning, check if the following applies to you:
* CDC user with access to the MPOX group on Gitlab
* Require access to available submission config files

Then, follow the cloning instructions outlined here: [cdc_configs_access](docs/cdc_configs_access.md)

Otherwise, proceed with cloning the repo to your local machine: 
```bash
git clone https://github.com/CDCgov/tostadas.git
```

### Environment Setup 
Based on whether or not you are a CDC user and running on Scicomp servers, the setup steps will differ. 

If you are not running the pipeline on CDC HPC, then perform steps directly below: ([Non-CDC Setup](#non-cdc-setup)), else if you are running on Scicomp servers then proceed to the setup steps under [Scicomp Setup](#scicomp-setup)

#### Non-CDC Setup:

The following steps are for running the pipeline in a non-CDC environment.

If you want to create the full-conda environment needed to run the pipeline outside of Nextflow (enables you to run individual python scripts), then proceed with **steps 1-5** below. 

If you simply want to run the pipeline using Nextflow only (this will be most users), then you would simply create an empty conda environment (skip **step 3** but perform **steps 1-2 and steps 4-5**):
```bash
conda create --name tostadas
```
Nextflow will handle environment creation and you would only need to install the nextflow package locally vs the entire environment.

#### (1) Install Mamba:
```bash
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh
bash Mambaforge-$(uname)-$(uname -m).sh -b -p $HOME/mambaforge
```

#### (2) Add Mamba to PATH:
```bash
export PATH="$HOME/mambaforge/bin:$PATH"
```

#### (3) Now you can create the conda environment and install the dependencies set in your environment.yml:   
```bash
mamba env create -n tostadas -f environment.yml   
```

#### (4) After the environment is created activate the environment. Always make sure to activate the environment with each new session.
```bash
source activate tostadas
```
:exclamation: You can check which environment is active by running the following conda command: `conda env list`  . The active environment will be denoted with an asterisk `*`

#### (5) Install Nextflow:

You need the Nextflow package to actually run the pipeline and have two options for installing it:

(5a) Using Mamba and the Bioconda Channel:
```bash
mamba install -c bioconda nextflow
```
(5b) Externally to mamba environment following the instructions here: [Nextflow Install](https://www.nextflow.io/docs/latest/getstarted.html)

#### Scicomp Setup:

The following steps are for running the pipeline on Scicomp at the CDC.

If you want to create the full-conda environment needed to run the pipeline outside of Nextflow (enables you to run individual python scripts), then proceed with the steps listed below [here](#1-activate-the-miniconda-module). 

If you simply want to run the pipeline using Nextflow only (this will be most users), then you would simply initialize the nextflow module (skip **steps 1-4** below):
```bash
ml nextflow
```

#### (1) Activate the miniconda module:
```bash
ml miniconda3
```

#### (2) Create conda environment using mamba:
```bash
mamba env create -n tostadas -f environment.yml   
```

#### (3) Activate the conda environment:
```bash
conda activate tostadas   
```

#### (4) Install Nextflow:

You need the Nextflow package to actually run the pipeline and can install it in the following manner:

Using mamba and the bioconda channel:
```bash
mamba install -c bioconda nextflow
```

## Quick Start

The configs are set-up to run the default params with the test option

#### (1) Ensure nextflow was installed successfully by running ```nextflow -v```

Expected Output:
```
nextflow version 22.10.0.5826
```

#### (2) Check that you are in the project directory (Tostadas).
This is the default directory set in the nextflow.config file to allow for running the nextflow pipeline with the provided test input files.

#### (3) Optional: Change the ```submission_config``` parameter within ```{taxon}_test_params.config``` to the location of your personal submission config file. Note that we provide a virus and bacterial test config depending on the use case.

:exclamation: You must have your personal submission configuration file set up before running the default parameters for the pipeline and/or if you plan on using sample submission at all. More information on setting this up can be found here: [More Information on Submission](#more-information-on-submission)

#### (4) Run one of the following nextflow command to execute the scripts with default parameters and with local run environment: 

```bash
# for virus reads
nextflow run main.nf -profile test,conda,virus
# for bacteria reads
nextflow run main.nf -profile test,conda,bacteria --download_bakta_db true --bakta_db_type light
```
:exclamation: Note: if you would like to run bacterial samples with annotation, refer to the *Running with Bakta* section found under the [How to Run](#how-to-run) examples.

The outputs of the pipeline will appear in the "nf_test_results" folder within the project directory (update this in the standard params set for a different output path).

:exclamation: Running the pipeline with default parameters (test) will trigger a wait time equal to # of samples * 180 seconds. This default parameter can be overridden by running the following command instead:

```bash
nextflow run main.nf -profile test,conda,virus --submission_wait_time <place integer value here in seconds>
```

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
   
  ## Acknowledgements
  Michael Desch | Ethan Hetrick | Nick Johnson | Kristen Knipe | Shatavia Morrison\
  Yuanyuan Wang | Michael Weigand | Dhwani Batra | Jason Caravas | Ankush Gupta\
  Kyle O'Connell | Yesh Kulasekarapandian |  Cole Tindall | Lynsey Kovar | Hunter Seabolt\
  Crystal Gigante | Christina Hutson | Brent Jenkins | Yu Li | Ana Litvintseva | Swarnali Louha\
  Matt Mauldin | Dakota Howard | Ben Rambo-Martin | James Heuser | Justin Lee | Mili Sheth
