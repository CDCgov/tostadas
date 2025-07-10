# TOSTADAS &#8594; <span style="color:blue"><u>**T**</u></span>oolkit for <span style="color:blue"><u>**O**</u></span>pen <span style="color:blue"><u>**S**</u></span>equence <span style="color:blue"><u>**T**</u></span>riage, <span style="color:blue"><u>**A**</u></span>nnotation and <span style="color:blue"><u>**DA**</u></span>tabase <span style="color:blue"><u>**S**</u></span>ubmission :dna: :computer:

## PATHOGEN ANNOTATION AND SUBMISSION PIPELINE

<!-- [![GitHub Downloads](https://img.shields.io/github/downloads/CDCgov/tostadas/total.svg?style=social&logo=github&label=Download)](https://github.com/CDCgov/tostadas/releases) -->
[![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A521.10.3-23aa62.svg?labelColor=000000)](https://www.nextflow.io/) [![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/) [![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/) [![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)

For the complete TOSTADAS documentation, please see the [Wiki](https://github.com/CDCgov/tostadas/wiki)

## Warnings
### Plugin Compatibility Warning
❗ Important Note: This pipeline uses the nf-schema plugin to validate pipeline parameters. Users with Nextflow version 24 or later may encounter a warning message indicating that the plugin must be installed. To resolve this warning message, please install the plugin manually by following the instructions found in this [link](https://www.nextflow.io/docs/latest/plugins.html#offline-usage)

## Overview
**T O S T A D A S**  
**T**oolkit for **O**pen **S**equence **T**riage, **A**nnotation, and **DA**tabase **S**ubmission  
  
A portable, open-source pipeline designed to streamline submission of pathogen genomic data to public repositories.  Reducing barriers to timely data submission increases the value of public repositories for both public health decision making and scientific research. TOSTADAS facilitates routine sequence submission by standardizing and automating: 

+ Metadata Validation   
+ Genome Annotation    
+ File submission    

TOSTADAS is designed to be flexible, modular, and pathogen agnostic, allowing users to customize their submission of raw read data, assembled genomes, or both. The current release has been tested with sequence data from Poxviruses and select bacteria. Testing for additional pathogen is planned for future releases.

## Installation and Quick Start
❗ Note: If you are a CDC user, please follow the set-up instructions found here: [CDC User Guide](https://github.com/CDCgov/tostadas/wiki/CDC-User-Guide)

For non-CDC users, please follow the instructions below.
### 1. Clone the repository to your local machine
```
git clone https://github.com/CDCgov/tostadas.git
```
! Note: If you already have Nextflow installed in your local environment, skip ahead to step 5.
### 2. Install mamba and add it to your PATH 

 **2a. Install mamba** 
 
❗ Note: If you have mamba installed in your local environment, skip ahead to step 3 ([Create and activate a conda environment](https://github.com/CDCgov/tostadas/edit/dev/README.md#3-create-and-activate-a-conda-environment))
```
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh
bash Mambaforge-$(uname)-$(uname -m).sh -b -p $HOME/mambaforge
```
 **2b. Add mamba to PATH:**
```
export PATH="$HOME/mambaforge/bin:$PATH"
```
### 3. Install Nextflow using mamba and the bioconda Channel
```
mamba install -c bioconda nextflow
```
### 4. Update the default submissions config file with your NCBI username and password 
```
# update this config file (you don't have to use vim)
vim conf/submission_config.yaml
```
### 5. Run the workflow with default parameters and the local run environment:
```
# test command for virus reads
nextflow run main.nf -profile test,<singularity|docker|conda> --species virus
```
The pipeline outputs appear in `tostadas/test_output`

### 6. Start running your own analysis

**Annotate and submit viral reads**
```
nextflow run main.nf -profile <docker|singularity> --species virus --submission --annotation  --genbank true --sra true --biosample true --output_dir <path/to/output/dir/> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml>
```
**Annotate and submit bacterial reads**
```
nextflow run main.nf -profile <docker|singularity> --species bacteria --submission --annotation  --genbank true --sra true --biosample true --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --download_bakta_db --bakta_db_type <light|full> --output_dir <path/to/output/dir/>
```
Refer to the wiki for more information on input parameters and use cases

### 7. Custom metadata validation and custom BioSample package

TOSTADAS defaults to Pathogen.cl.1.0 (Pathogen: clinical or host-associated; version 1.0) NCBI BioSample package for submissions to the BioSample repository. You can submit using a different BioSample package by doing the following:
1. Change the package name in the `conf/submission_config.yaml`. Choose one of the available [NCBI BioSample packages](https://www.ncbi.nlm.nih.gov/biosample/docs/packages/). 
2. Add the necessary fields for your BioSample package to your input Excel file.
3. Add those fields as keys to the JSON file (`assets/custom_meta_fields/example_custom_fields.json`) and provide key info as needed.
    replace_empty_with: TOSTADAS will replace any empty cells with this value (Example application: NCBI expects some value for any mandatory field, so if empty you may want to change it to "Not Provided".)
    new_field_name: TOSTADAS will replace the field name in your metadata Excel file with this value. (Example application: you get weekly metadata Excel files and they specify 'animal_environment' but NCBI expects 'animal_env'; you can specify this once in the JSON file and it will changed on every run.)

**Submit to a custom BioSample package**
```
nextflow run main.nf -profile <docker|singularity> --species virus --submission --annotation  --genbank true --sra true --biosample true --output_dir <path/to/output/dir/> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --custom_fields_file  <path/to/metadata_custom_fields.json>
```
### Workflow Parameters Overview

This section outlines the primary parameters available for configuring and running the TOSTADAS pipeline effectively, allowing users to tailor the workflow for their needs:

| Parameter               | Description                                                                                       | Input Required           |
|-------------------------|---------------------------------------------------------------------------------------------------|--------------------------|
| `--validate_params`     | Flag to enable or disable parameter validation                                                    | No (true/false as bool)  |
| `--annotation`          | Toggle for running annotation                                                                     | Yes (true/false as bool) |
| `--submission`          | Toggle for running submission                                                                     | Yes (true/false as bool) |
| `--update_submission`   | Toggle to update data for existing BioSample or SRA records                                       | Yes (true/false as bool) |
| `--fetch_reports_only`  | Toggle for only fetching submission reports                                                       | Yes (true/false as bool) |

For more detailed information on each parameter and additional configurations, please refer to the [TOSTADAS documentation](https://github.com/CDCgov/tostadas/wiki).

## Troubleshooting

If you encounter issues while using the TOSTADAS pipeline, refer to the following troubleshooting steps to resolve common problems:

### Common Issues and Solutions

#### 1. Errors with 'table2asn not on PATH' or a Python library missing when using the `singularity` or `docker` profiles

**Issue:** Nextflow is using an outdated cached image.

**Solution:** Locate the image (e.g., `$HOME/.singularity/staphb-tostadas-latest.img`) and delete it. This will force Nextflow to pull the latest version.

#### 2. Pipeline hangs indefinitely during the submission step, or you get a "duplicate BioSeq ID error"  

**Issue:** This may be caused by duplicate sample IDs in the FASTA file (e.g., a multicontig FASTA). This is only a problem for submissions to Genbank using `table2asn`.

**Solution:** Review the sequence headers in the sample FASTA files and ensure that each header is unique.

## Get in Touch
If you need to report a bug, suggest new features, or just say “thanks”, [open an issue](https://github.com/CDCgov/tostadas/issues/new/choose) and we’ll try to get back to you as soon as possible!

## Acknowledgements
### Contributors
Jessica Rowell | Kyle O'Connell | Yesh Kulasekarapandian | Ankush Gupta | Cole Tindall | Swarnali Louha | Michael Desch | Ethan Hetrick | Nick Johnson | Kristen Knipe | Shatavia Morrison | Yuanyuan Wang | Michael Weigand | Dhwani Batra | Jason Caravas | Lynsey Kovar | Hunter Seabolt | Crystal Gigante | Christina Hutson | Brent Jenkins | Yu Li | Ana Litvintseva | Matt Mauldin | Dakota Howard | Ben Rambo-Martin | James Heuser | Justin Lee | Mili Sheth

### Tools
The submission portion of this pipeline was adapted from SeqSender. To find more information on this tool, please refer to their GitHub page: [SeqSender](https://github.com/CDCgov/seqsender)

## Resources

:link: NCBI Submission Guidelines: https://submit.ncbi.nlm.nih.gov/sarscov2/sra/#step6

:link: SeqSender Documentation: https://github.com/CDCgov/seqsender

:link: Liftoff Documentation: https://github.com/agshumate/Liftoff

:link: VADR Documentation:  https://github.com/ncbi/vadr.git

:link: Bakta Documentation:  https://github.com/oschwengers/bakta

:link: RepeatMasker Documentation: https://www.repeatmasker.org/

## CDC Metadata
```
Organization: NCEZID-OAMD
contact email: ncezid_shareit@cdc.gov
exemption status: NA
exemption justification: NA
description fields: Nextflow workflow for viral and bacterial annotation and automated upload to NCBI databases
```



