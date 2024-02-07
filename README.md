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

#### (2) Clone the repository to your local machine:  
```bash
git clone https://github.com/CDCgov/tostadas.git
cd tostadas
```
:exclamation: Note: If you have mamba or nextflow installed in your local environment, you may skip steps 2, 3 (mamba installation) and 6 (nextflow installation) accordingly. 

#### (3) Create and activate the conda environment: 

```bash
mamba env create -n tostadas -f environment.yml
conda activate tostadas
```
#### (4) Test your installation by running one of the following nextflow commands on test data

```bash
# for virus reads
nextflow run main.nf -profile test,<singularity/docker/conda> --virus
# for bacterial reads
nextflow run main.nf -profile test,<singularity/docker/conda> --bacteria 
```
The pipeline outputs appear in the ```test_output``` folder within the tostadas directory. 

#### (5) Start running your own analysis
**Annotate and submit viral reads**
```{bash}
nextflow run main.nf -profile docker --virus --fasta_path <path/to/fasta/files> ---meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --output_dir <path/to/output/dir/>
```
**Annotate and submit bacterial reads**
```{bash}
nextflow run main.nf -profile docker --bacteria --fasta_path <path/to/fasta/files> ---meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --download_bakta_db --bakta_db_type <light/full>--output_dir <path/to/output/dir/>
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

## Acknowledgements
  ### Contributors
  Michael Desch | Ethan Hetrick | Nick Johnson | Kristen Knipe | Shatavia Morrison\
  Yuanyuan Wang | Michael Weigand | Dhwani Batra | Jason Caravas | Ankush Gupta\
  Kyle O'Connell | Yesh Kulasekarapandian |  Cole Tindall | Lynsey Kovar | Hunter Seabolt\
  Crystal Gigante | Christina Hutson | Brent Jenkins | Yu Li | Ana Litvintseva | Swarnali Louha\
  Matt Mauldin | Dakota Howard | Ben Rambo-Martin | James Heuser | Justin Lee | Mili Sheth
  ### Tools
  The submission portion of this pipeline was adapted from SeqSender. To find more information on this tool, please refer to their GitHub page: [SeqSender](https://github.com/CDCgov/seqsender). 
