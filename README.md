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

## Pipeline Summary

### Metadata Validation
The validation workflow checks that user provided metadata conforms to NCBI standards and matches the input data file(s). To allow for easy multi-sample submission, TOSTADAS can split a multi-sample Excel (.xlsx) file into separate tab delimited files (.tsv) for each individual sample.

TOSTADAS can accept custom metadata fields specific to a users' pathogen, sample type, or workflow. Additionally, TOSTADAS offers powerful validation tools for user- created fields, allowing users to specify which samples to apply rules to, replace empty values with user specified replacements, rename existing fields and other operations.
These features can be enabled with the `validate_custom_fields` parameter. Custom fields can be specified using the `custom_fields_file` parameter.  

A full guide to using custom metadata fields can be found here: [Custom Metadata Guide](https://github.com/CDCgov/tostadas/blob/457242fb15973f69cb3578367317a8b5e7c619f7/docs/custom_metadata_guide.md)

### Gene Annotation

TOSTADAS offers three optional annotation options:
1. RepeatMasker and Liftoff 
    * The RepeatMasker and Liftoff workflow annotates fasta-formatted sequences based upon a provided reference and annotation file.  This workflow was optimized for variola genome annotation and may require modification for other pathogens. This workflow runs [RepeatMasker](https://www.repeatmasker.org/) to annotate repeat motifs, followed by [Liftoff](https://github.com/agshumate/Liftoff) to annotate functional regions. These results are combined into a single feature file (.gff3). The Liftoff annotation workflow requires a reference genome (.fasta), reference feature .gff, single sample .fasta files, and metadata in Excel .xlsx format.  Be sure to specify the correct database in the params for this option.

    [RepeatMasker and Liftoff Example] (Link) 
 

2. VADR
    * The VADR workflow annotates  fasta-formatted viral genomes using RefSeq annotation from a set of homologous reference models. This workflow requires single sample fasta files, metadata in .xlsx format, and reference information for the pathogen genome. TOSTADAS comes packaged with support for [monkeypox (mpxv) annotation] (https://github.com/CDCgov/tostadas/tree/master/vadr_files/mpxv-models). You can find information on other supported pathogens at the [VADR GitHub Repository] (https://github.com/ncbi/vadr).

    [VADR Example] (Link) 
3. Bakta
    * The Bakta workflow annotates fasta-formatted bacterial genomes & plasmids using the [Bakta](https://github.com/CDCgov/tostadas/tree/master#gene-annotation) software. This workflow requires single sample .fasta files, metadata in .xlsx format, and optional reference database for annotation (found [here](https://zenodo.org/records/7669534)). 

    [BAKTA Example] (Link) 

All annotation workflows produce a general feature format file (.gff3) and NCBI feature table (tbl)  compatible with NCBI submission requirements.

### Submission 
The TOSTADAS Submission workflow generates the necessary files for Genbank submission, a BioSample ID, then optionally uploads Fastq files via FTP to SRA. This workflow was adapted from [SeqSender](https://github.com/CDCgov/seqsender) public database submission pipeline.

## Installation
### Repository Setup

:exclamation: Note: If you are a CDC user, please follow the set-up instructions found on Page X - [CDC User Guide](Link)

Clone the repository to your local machine:  
```bash
git clone https://github.com/CDCgov/tostadas.git
```

### Environment Setup 

:exclamation: Note: If you have mamba or nextflow installed in your local environment, you may skip steps 1, 2 (mamba installation) and 5 (nextflow installation) accordingly. 

#### (1) Install Mamba:
```bash
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh
bash Mambaforge-$(uname)-$(uname -m).sh -b -p $HOME/mambaforge
```

#### (2) Add mamba to PATH:
```bash
export PATH="$HOME/mambaforge/bin:$PATH"
```

#### (3) Create the conda environment: 

If you want to create the full-conda environment needed to run the pipeline outside of Nextflow (this enables you to run individual python scripts), then proceed with step **3a**. 

If you want to run the pipeline using nextflow only (this will be most users), proceed with step 3b. Nextflow will handle environment creation and you would only need to install the nextflow package locally vs the entire environment.

&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **(3a) Create the conda environment and install the dependencies set in your environment.yml:**   

```bash
mamba env create -n tostadas -f environment.yml   
```
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; **(3b) Create an empty conda environment:**
```bash
conda create --name tostadas
```

#### (4) Activate the environment. 
```bash
conda activate tostadas
```
Verify which environment is active by running the following conda command: `conda env list`  . The active environment will be denoted with an asterisk `*`

#### (5) Install Nextflow using Use Mamba and the Bioconda Channel:

```bash
mamba install -c bioconda nextflow
```
:exclamation: Optionally, you may install nextflow without mamba by following the instructions found in the Nextflow Installation Documentaion Page: [Nextflow Install](https://www.nextflow.io/docs/latest/getstarted.html)

## Quick Start

#### (1) Ensure Nextflow was installed successfully by running ```nextflow -v```

Expected Output:
```
nextflow version <CURRENT VERSION>
```
The exact version of Nextflow returned will differ from installation to installation.  It is important that the command execute successfully and a version number is returned.

#### (2) Check that you are in the directory where the TOSTADAS repository was installed by running ```pwd```
Expected Output:
```
/path/to/working/directory/tostadas
```
This is the default directory set in ``` nextflow.config```  for the provided test input files.


#### (3) Run one of the following nextflow commands to execute the scripts with default parameters and the local run environment: 

```bash
# for virus reads
nextflow run main.nf -profile test,conda -virus
# for bacterial reads
nextflow run main.nf -profile test,conda -bacteria 
```

The outputs of the pipeline will appear in the "nf_test_results" folder within the project directory.  You can update the output path in ```<FILE_NAME>```. 

Q. Which file can we update this in? 

#### (4) Change the ```submission_config``` parameter within ```{taxon}_test_params.config``` to the location of your personal submission config file. Note that we provide a virus and bacterial test config depending on the use case.

:exclamation: You must have your personal submission configuration file set up before running the default parameters for the pipeline and/or if you plan on using sample submission at all. More information on setting this up can be found here: [More Information on Submission](https://github.com/CDCgov/tostadas/wiki/4.-Profile-Options-&-Input-Files#45-more-information-on-submission)

#### (5) Pipeline Execution Examples 
The input parameters can be modified to perform actions such as: 
- choose which sub-workflows to execute and provide the required input files for each sub-workflow
- modify the envinroment of the run
- provide required input files 

To see examples on how to run the pipeline and understand the various use-cases of running the Tostadas pipeline, please refer to the  [How to Run](https://github.com/CDCgov/tostadas/wiki/8.-Running-the-Pipeline#81-how-to-run) page. 

## Helpful Links for Resources and Software Integrated with TOSTADAS:     
   :link: Anaconda Install: https://docs.anaconda.com/anaconda/install/
   
   :link: Nextflow Documentation: https://www.nextflow.io/docs/latest/getstarted.html
   
   :link:  SeqSender Documentation: https://github.com/CDCgov/seqsender
   
   :link: Liftoff Documentation: https://github.com/agshumate/Liftoff
   
   :link: VADR Documentation:  https://github.com/ncbi/vadr.git

   :link: Bakta Documentation:  https://github.com/oschwengers/bakta
   
   :link: table2asn Documentation: https://github.com/svn2github/NCBI_toolkit/blob/master/src/app/table2asn/table2asn.cpp

   :link: RepeatMasker Documentation: https://www.repeatmasker.org/

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
