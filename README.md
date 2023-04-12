# TOSTADAS &#8594; <span style="color:blue"><u>**T**</u></span>oolkit for <span style="color:blue"><u>**O**</u></span>pen <span style="color:blue"><u>**S**</u></span>equence <span style="color:blue"><u>**T**</u></span>riage, <span style="color:blue"><u>**A**</u></span>nnotation and <span style="color:blue"><u>**DA**</u></span>tabase <span style="color:blue"><u>**S**</u></span>ubmission :dna: :computer:

## PATHOGEN ANNOTATION AND SUBMISSION PIPELINE

<!-- [![GitHub Downloads](https://img.shields.io/github/downloads/CDCgov/tostadas/total.svg?style=social&logo=github&label=Download)](https://github.com/CDCgov/tostadas/releases) -->
[![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A521.10.3-23aa62.svg?labelColor=000000)](https://www.nextflow.io/) [![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/) [![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/) [![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)

## Overview
  The Pathogen Annotation and Submission pipeline facilitates the running of several Python scripts, which validate metadata (QC), annotate assembled genomes, and submit to NCBI. Current implementation was tested using MPOX but future testing will seek to made the pipeline pathogen-agnostic. 

## Table of Contents
- [Overview](#overview)
- [Table of Contents](#table-of-contents)
- [Pipeline Summary](#pipeline-summary)
    - [Metadata Validation](#metadata-validation)
    - [Liftoff](#liftoff)
    - [Submission](#submission)
- [Setup](#setup)
    - [Environment Setup](#environment-setup)
        - [Non-CDC Setup](#non-cdc-setup)
        - [Scicomp Setup](#scicomp-setup)
    - [Repository Setup](#repository-setup)
- [Quickstart](#quick-start)
- [Running the Pipeline](#running-the-pipeline)
- [Profile Options & Input Files](#profile-options--input-files)
    - [Input Files Required](#input-files-required)
    - [Customizing Parameters](#customizing-parameters)
    - [Understanding Profiles and Environments](#understanding-profiles-and-environments)
    - [Toggling Submission](#toggling-submission)
    - [More Information on Submission](#more-information-on-submission)
- [Entrypoints](#entrypoints)
    - [Required Files for Submission](#required-files-for-submission-entrypoint)
- [Outputs](#outputs)
    - [Pipeline Overview](#pipeline-overview)
    - [Output Directory Formatting](#output-directory-formatting)
    - [Understanding Pipeline Outputs](#understanding-pipeline-outputs)
- [Parameters](#parameters)
    - [Input Files](#input-files)
    - [Run Environment](#run-environment)
    - [General Subworkflow](#general-subworkflow)
    - [Cleanup Subworkflow](#cleanup-subworkflow)
    - [General Output](#general-output)
    - [Metadata Validation](#metadata-validation)
    - [Liftoff](#liftoff)
    - [VADR](#vadr)
    - [Submission](#sample-submission)
- [Helpful Links](#helpful-links)
- [Get in Touch](#get-in-touch)
- [Acknowledgements](#acknowledgements)

## Pipeline Summary

### Metadata Validation
The validation workflow checks if metadata conforms to NCBI standards and matches the input fasta file. The script also splits a multi-sample xlsx file into a separate .tsv file for each individual.

### Gene Annotation

Currently, consists of two annotation options:
* (1) Liftoff 
    * The liftoff workflow annotates input fasta-formatted genomes and produces accompanying gff and genbank tbl files. The input includes the reference genome fasta, reference gff and your multi-sample fasta and metadata in .xlsx format. The [Liftoff](https://github.com/agshumate/Liftoff) workflow was brought over and integrated from the Liftoff tool, responsible for accurately mapping annotations for assembled genomes.
* (2) VADR
    * The VADR workflow annotates input fasta-formatted genomes and generates gff / tbl files. The inputs into this workflow are your multi-sample fasta, metadata in .xlsx format, and reference information for the pathogen genome which is included within this repository (found [here](https://github.com/CDCgov/tostadas/tree/lets_add_vadrv2/vadr_files/mpxv-models)). VADR is an existing package that was integrated into the pipeline and you can find more information about this tool at the following link: [VADR Git Repo](https://github.com/ncbi/vadr).

### Submission 
Submission workflow generates the necessary files for Genbank submission, generates a BioSample ID, then optionally uploads Fastq files via FTP to SRA. This workflow was adapted from [SeqSender](https://github.com/CDCgov/seqsender) public database submission pipeline.

## Setup

### Repository Setup

Before cloning, check if the following applies to you:
* CDC user with access to the Monkeypox group on Gitlab
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
** NOTE: You can check which environment is active by running the following conda command: ```conda env list```  . The active environment will be denoted with an asterisk ```*```

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

If you simply want to run the pipeline using Nextflow only (this will be most users), then you would simply initialize the nextflow module (skip all steps below):
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

#### (1) Ensure nextflow was installed successfully by running ```Nextflow -v```

Expected Output:
```
nextflow version 22.10.0.5826
```

#### (2) Check that you are in the project directory (Tostadas).
This is the default directory set in the nextflow.config file to allow for running the nextflow pipeline with the provided test input files.

#### (3) Change the ```submission_config``` parameter within ```test_params.config``` to the location of your personal submission config file.

** NOTE: You must have your personal submission configuration file set up before running the default parameters for the pipeline and/or if you plan on using sample submission at all. More information on setting this up can be found here: [More Information on Submission](#more-information-on-submission)

#### (4) Run the following nextflow command to execute the scripts with default parameters and with local run environment: 

```bash
nextflow run main.nf -profile test,conda
```

The outputs of the pipeline will appear in the "nf_test_results" folder within the project directory (update this in the standard params set for a different output path).

** NOTE: Running the pipeline with default parameters (test) will trigger a wait time equal to # of samples * 180 seconds. This default parameter can be overridden by running the following command instead:

```bash
nextflow run main.nf -profile test,conda --submission_wait_time <place integer value here in seconds>
```

More information on the ```submission_wait_time``` parameter can be found under [Submission Parameters](#submission)

## Running the Pipeline

### How to Run:
The typical command to run the pipeline based on your custom parameters defined/saved in the standard_params.config (more information about profiles and parameter sets below) and created conda environment is as follows:

```bash
nextflow run main.nf -profile standard,conda
``` 
OR with the parameters specified in the .json/.yaml files with the following command:

```bash
nextflow run main.nf -profile standard,conda --<param name> <param value>
```

Other options for the run environment include ```docker``` and ```singularity```. These options can be used simply by replacing the second profile option: 
```bash
nextflow run main.nf -profile standard,<docker or singularity>
```

Either one of the above commands will launch the nextflow pipeline and show the progress of the subworkflow:process and checks looking similar to below depending on the entrypoint specified. 

```bash
N E X T F L O W  ~  version 22.10.0
Launching `main.nf` [festering_spence] DSL2 - revision: 3441f714f2
executor >  local (7)
[e5/9dbcbc] process > VALIDATE_PARAMS                                  [100%] 1 of 1 âœ”
[53/a833be] process > CLEANUP_FILES                                    [100%] 1 of 1 âœ”
[e4/a50c97] process > with_submission:METADATA_VALIDATION (1)          [100%] 1 of 1 âœ”
[81/badd3b] process > with_submission:LIFTOFF (1)                      [100%] 1 of 1 âœ”
[d7/16d16a] process > with_submission:RUN_SUBMISSION:SUBMISSION (1)    [100%] 1 of 1 âœ”
[3c/8c7ba4] process > with_submission:RUN_SUBMISSION:GET_WAIT_TIME (1) [100%] 1 of 1 âœ”
[13/85f6f3] process > with_submission:RUN_SUBMISSION:WAIT (1)          [  0%] 0 of 1
[-        ] process > with_submission:RUN_SUBMISSION:UPDATE_SUBMISSION -
USING CONDA

````
** NOTE: The default wait time between initial submission and updating the submitted samples is three minutes or 180 seconds per sample. To override this default calculation, you can modify the submission_wait_time parameter within your config or through the command line (in terms of seconds):
 
 ```bash
nextflow run main.nf -profile <param set>,<env> --submission_wait_time 360
 ```
 
Outputs will be generated in the nf_test_results folder (if running the test parameter set) unless otherwise specified in your standard_params.config file as output_dir param. 

## Profile Options & Input Files

This section walks through the available parameters to customize your workflow.

### Input Files Required: 

#### (A) This table lists the required files to run metadata validation and annotation:
| Input files | File type | Description                                                                               |
|-------------|-----------|-------------------------------------------------------------------------------------------|
| fasta       | .fasta    | Multi-sample fasta file with your input sequences                                         |
| metadata    | .xlsx     | Multi-sample metadata matching metadata spreadsheets provided in input_files              |
| ref_fasta   | .fasta    | Reference genome to use for the  liftoff_submission branch of the pipeline                |
| ref_gff     | .gff      | Reference GFF3 file to use for the  liftoff_submission branch of  the pipeline            | 

#### (B) This table lists the required files to run with submission: 
| Input files | File type | Description                                                                               |
|-------------|-----------|-------------------------------------------------------------------------------------------|
| fasta       | .fasta    | Multi-sample fasta file with your input sequences                                         |
| metadata    | .xlsx     | Multi-sample metadata matching metadata spreadsheets provided in input_files              |
| ref_fasta   | .fasta    | Reference genome to use for the  liftoff_submission branch of the pipeline                |
| ref_gff     | .gff      | Reference GFF3 file to use for the  liftoff_submission branch of  the pipeline            | 
| submission_config| .yaml    | configuration file for submitting to NCBI, sample versions can be found in repo       |

### Customizing Parameters:
The standard_params.config file found within the conf directory is where parameters can be adjusted based on preference for running the pipeline. First you will want to ensure the file paths are correctly set for the params listed above depending on your preference for submitting your results. 
 * Adjust your file inputs within standard_params.config ensuring accurate file paths for the inputs listed above.
 * The params can be changed within the standard_params.config or you can change the standard.yml/standard.json file inside the nf_params directory and pass it in with: ```-params-file <standard_params.yml or standard_params.json>```
 * Note: DO NOT EDIT the main.nf file or other paths in the nextflow.config unless familiar with editing nextflow workflows

### Understanding Profiles and Environments:
Within the nextflow pipeline the ```-profile``` option is required as an input. The profile options with the pipeline include test and standard. These two options can be seen listed in the nextflow.config file. The test params should remain the same for testing purposes, but the standard profile can be changed to fit user preferences. Also within the nextflow pipeline there is the use of varying run environments as the second profile input. Nextflow expects at least one option for both of these configurations to be passed in: ```-profile <test/standard>,<conda/docker/singularity>```

### Toggling Submission:
Now that your file paths are set within your standard.yml or standard.json or standard_params.config file, you will want to define whether to run the full pipeline with submission or without submission. This is defined within the standard_params.config file underneath the subworkflow section as run_submission ```run_submission = true/false```
 * Apart from this main bifurcation, there exists entrypoints that you can use to access specific processes. More information is listed in the table below.

### More Information on Submission:
The submission piece of the pipeline uses the processes that are directly integrated from [SeqSender](https://github.com/CDCgov/seqsender) public database submission pipeline. It has been developed to allow the user to create a config file to select which databases they would like to upload to and allows for any possible metadata fields by using a YAML to pair the database's metadata fields which your personal metadata field columns. The requirements for this portion of the pipeline to run are listed below.

(A) Create Appropriate Accounts as needed for the [SeqSender](https://github.com/CDCgov/seqsender) public database submission pipeline integrated into TOSTADAS:
* NCBI: If uploading to NCBI, an account is required along with a center account approved for submitting via FTP. Contact the following for account creation:gb-admin@ncbi.nlm.nih.gov.
* GISAID: A GISAID account is required for submission to GISAID, you can register for an account at https://www.gisaid.org/. Test submissions are first required before a final submission can be made. When your first test submission is complete contact GISAID at hcov-19@gisaid.org to recieve a personal CID. GISAID support is not yet implemented but it may be added in the future.

(B) Config File Set-up:
* The template for the submission config file can be found in bin/default_config_files within the repo. This is where you can edit the various parameters you want to include in your submission.

## Entrypoints:

Table of entrypoints available for the nextflow pipeline:

| Workflow             | Description                                                 |
|----------------------|-------------------------------------------------------------|
| only_validate_params | Validates parameters utilizing the validate params process within the utility sub-workflow |
| only_cleanup_files   | Cleans-up files utilizing the clean-up process within the utility sub-workflow             |
| only_validation      | Runs the metadata validation process only                           |
| only_liftoff      | Runs the liftoff annotation process only                           |
| only_vadr         | Runs the VADR annotation process only                           |
| only_submission      | Runs submission sub-workflow only. Requires specific inputs mentioned here: [Required Files for Submission Entrypoint](#required-files-for-submission-entrypoint)                           |
| only_initial_submission | Runs the initial submission process but not follow-up within the submission sub-workflow. Requires specific inputs mentioned here: [Required Files for Submission Entrypoint](#required-files-for-submission-entrypoint)               |
| only_update_submission  | Updates NCBI submissions. Requires specific inputs mentioned here: [Required Files for Submission Entrypoint](#required-files-for-submission-entrypoint)                                 |

* Documentation for using entrypoints with NF can be found at [Nextflow_Entrypoints](https://www.nextflow.io/blog/2020/cli-docs-release.html) under section 5. 


The following command can be used to specify entrypoints for the workflow:

```bash
nextflow run main.nf -profile <param set>,<env> -entry <insert option from table above>
```

### Required Files for Submission Entrypoint:

If you are using the ```only_submission``` or  ```only_initial_submission``` entrypoint, you must define the paths for the following parameters:

* ```submission_only_meta``` : path to the directory containing validated metadata files (one .tsv per sample)
* ```submission_only_fasta``` : path to the directory containing split fasta files (one .fasta per sample)
* ```submission_only_gff``` : path to the directory containing the cleaned and reformatted GFF files (one .gff per sample)

It is preferred to use ```$projectDir``` to prefix the defined paths, which is a built-in variable for encoding the path to the **main.nf** file. Then, you can simply append it with the path relative to main.nf.

For example, if your files are located in a directory named **test_files** immediately below the level where main.nf is, with separate directories for fasta, gff, and metadata files (called fasta, gff, and meta) inside it, then you would use the following:
 
```submission_only_meta = $projectDir/test_files/meta```

```submission_only_fasta = $projectDir/test_files/fasta```

```submission_only_gff = $projectDir/test_files/gff```

You do have the option to use either relative paths (from where you are running the pipeline) or absolute paths, but this may introduce issues when running it on certain cloud/HPC environments.

If you are using ```only_update_submission``` entrypoint, you must define the following parameter:

* ```processed_samples``` : path to the directory containing outputs from initial submission

## Outputs
The following section walks through the outputs from the pipeline.

### Pipeline Overview:
The workflow will generate outputs in the following order:

* Validation
    * Responsible for QC of metadata  
    * Aligns sample metadata .xlsx to sample .fasta
    * Formats metadata into .tsv format
* Annotation 
    * Extracts features from .gff
    * Aligns features
    * Annotates sample genomes outputting .gff
* Submission
    * Formats for database submission
    * This section runs twice, with the second run occuring after a wait time to allow for all samples to be uploaded to NCBI. Entrypoint `only_update_submission` can be run as many times as necessary until all files are fully uploaded.

### Output Directory Formatting:
The outputs are recorded in the directory specified within the nextflow.config file and will contain the following:
* validation_outputs (**name configurable with val_output_dir)
    * name of metadata sample file
        * errors
        * tsv_per_sample
* liftoff_outputs (**name configurable with final_liftoff_output_dir)
    * name of metadata sample file
        * errors
        * fasta
        * liftoff
        * tbl
* vadr_outputs (**name configurable with vadr_output_dir)
    * name of metadata sample file
        * errors
        * fasta
        * gffs
        * tbl
* submission_outputs (**name and path configurable with submission_output_dir)
    * name of annotation results (Liftoff or VADR, etc.)
        * individual_sample_batch_info
            * biosample_sra
            * genbank
            * accessions.csv
        * terminal_outputs
        * commands_used

### Understanding Pipeline Outputs:
The pipeline outputs inlcude: 
* metadata.tsv files for each sample 
* separate fasta files for each sample
* separate gff files for each sample 
* separate tbl files containing feature information for each sample
* submission log file
    * This output is found in the submission_outputs file in your specified output_directory
    * If the file can not be found you can run the only_update_submission entrypoint for the pipeline 

## Parameters:
Default parameters are given in the nextflow.config file. This table lists the parameters that can be changed to a value, path or true/false. 
When changing these parameters pay attention to the required inputs and make sure that paths line-up and values are within range. To change a parameter you may change with a flag after the nextflow command or change them within your standard_params.config or standard.yaml file. 

* Please note the correct formatting and the default calculation of submission_wait_time at the bottom of the params table.


### Input Files

| Param                      | Description                                             | Input Required   |
|----------------------------|---------------------------------------------------------|------------------|
| --fasta_path               | Path to fasta file                                      |        Yes (path as string)      |
| --ref_fasta_path           | Reference Sequence file path                            |        Yes (path as string)      |
| --meta_path                | Meta-data file path for samples                         |        Yes (path as string)      |
| --ref_gff_path             | Reference gff file path for annotation                  |        Yes (path as string)      |
| --env_yml                  | Path to environment.yml file                            |        Yes (path as string)       |

### Run Environment
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --scicomp           | Flag for whether running on Scicomp or not                            | Yes (true/false as bool) |
| --docker_container           | Name of the Docker container                            | Yes, if running with docker profile (name as string) |
| --docker_container_vadr           | Name of the Docker container to run VADR annotation                            | Yes, if running with docker profile (name as string) |

### General Subworkflow
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --run_submission           | Toggle for running submission                            | Yes (true/false as bool) |
| --run_liftoff           | Toggle for running liftoff annotation                            | Yes (true/false as bool) |
| --run_vadr           | Toggle for running vadr annotation                            | Yes (true/false as bool) |
| --cleanup                  | Toggle for running cleanup subworkflows                 | Yes (true/false as bool) |

### Cleanup Subworkflow
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --clear_nextflow_log     | Clears nextflow work log                                |        Yes (true/false as bool)      |
| --clear_nextflow_dir     | Clears nextflow working directory                       |  Yes (true/false as bool)|
| --clear_work_dir         | Param to clear work directory created during workflow   |  Yes (true/false as bool) |                
| --clear_conda_env        | Clears conda environment                                |  Yes (true/false as bool) |               
| --clear_nf_results       | Remove results from nextflow outputs                    |  Yes (true/false as bool) |              

### General Output
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --output_dir               | File path to submit outputs from pipeline              |        Yes (path as string)      |
| --overwrite_output         | Toggle to overwriting output files in directory        | Yes (true/false as bool) |


### Metadata Validation
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --val_output_dir         | File path for outputs specific to validate sub-workflow |        Yes (folder name as string)      |
| --val_date_format_flag   | Flag to change date output                               |  Yes (-s, -o, or -v as string)   |
| --val_keep_pi            | Flag to keep personal identifying info, if provided otherwise it will return an error|        Yes (true/false as bool)      |


### Liftoff
| Param                       | Description                                             | Input Required   |
|-----------------------------|---------------------------------------------------------|------------------|
| --final_liftoff_output_dir  | File path to liftoff specific sub-workflow outputs      |        Yes (folder name as string)      |
| --lift_print_version_exit   | Print version and exit the program                      |  Yes (true/false as bool) |
| --lift_print_help_exit      |  Print help and exit the program                        |  Yes (true/false as bool) |
| --lift_parallel_processes   |  # of parallel processes to use for liftoff             |      Yes (integer)       |
| --lift_delete_temp_files    |  Deletes the temporary files after finishing transfer   |        Yes (true/false as string)       |
| --lift_child_feature_align_threshold  | Only if its child features usually exons/CDS align with sequence identity â‰¥S   |  designate a feature mapped |
| --lift_unmapped_feature_file_name  | Name of unmapped features file name             |        Yes (path as string)      |
| --lift_copy_threshold       |Minimum sequence identity in exons/CDS for which a gene is considered a copy; must be greater than -s; default is 1.0|     Yes (float)      |
|--lift_distance_scaling_factor | Distance scaling factor; by default D =2.0            |      Yes (float)       |
| --lift_flank                |Amount of flanking sequence to align as a fraction of gene length| Yes (float between [0.0-1.0]) |
| --lift_overlap              |Maximum fraction of overlap allowed by 2 features        |  Yes (float between [0.0-1.0]) |
| --lift_mismatch             |Mismatch penalty in exons when finding best mapping; by default M=2|     Yes (integer)         |
| --lift_gap_open             |Gap open penalty in exons when finding best mapping; by default GO=2|     Yes (integer)         |
| --lift_gap_extend           |Gap extend penalty in exons when finding best mapping; by default GE=1|     Yes (integer)         |
| --lift_infer_transcripts    |Use if annotation file only includes exon/CDS features and does not include transcripts/mRNA|  Yes (True/False as string) |
| --lift_copies               |Look for extra gene copies in the target genome          |  Yes (True/False as string) |
| --lift_minimap_path         |Path to minimap if you did not use conda or pip          |        Yes (N/A or path as string)       |
|--lift_feature_database_name |Name of the feature database, if none, then will use ref gff path to construct one|        Yes (N/A or name as string)      |

### VADR
| Param                       | Description                                             | Input Required   |
|-----------------------------|---------------------------------------------------------|------------------|
| --vadr_output_dir  | File path to vadr specific sub-workflow outputs      |        Yes (folder name as string)      |
| --vadr_models_dir  | File path to models for MPXV used by VADR annotation      |        Yes (folder name as string)      |

### Sample Submission
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --submission_output_dir | Either name or relative/absolute path for the outputs from submission | Yes (name or path as string) |
| --submission_prod_or_test | Whether to submit samples for test or actual production | Yes (prod or test as string) |
| --submission_only_meta   | Full path directly to the dirs containing validate metadata files|        Yes (path as string)      |
| --submission_only_gff    | Full path directly to the directory with reformatted GFFs    |        Yes (path as string)      |
| --submission_only_fasta  | Full path directly to the directory with split fastas for each sample|        Yes (path as string)      |
| --submission_config      | Configuration file for submission to public repos       |        Yes (path as string)      |
| --submission_wait_time |Calculated based on sample number (3 * 60 secs * sample_num) | integer (seconds)       |
| --batch_name | Name of the batch to prefix samples with during submission | Yes (name as string)
| --send_submission_email | Toggle email notification on/off | Yes (true/false as bool)           |
| --req_col_config | Path to the required_columns.yaml file | Yes (path as string)           |
| --processed_samples | Path to the directory containing processed samples for update only submission entrypoint (containing <batch_name>.<sample_name> dirs) | Yes (path as string)           |

** Important note about ```send_submission_email```: An email is only triggered if Genbank is being submitted to AND table2asn is the genbank_submission_type. As for the recipient, this must be specified within your submission config file under 'general' as 'notif_email_recipient'

## Helpful Links for Resources and Software Integrated with TOSTADAS:     
   :link: Anaconda Install: https://docs.anaconda.com/anaconda/install/
   
   :link: Nextflow Documentation: https://www.nextflow.io/docs/latest/getstarted.html
   
   :link:  SeqSender Documentation: https://github.com/CDCgov/seqsender
   
   :link: Liftoff Documentation: https://github.com/agshumate/Liftoff
   
   :link: VADR Documentation:  https://github.com/ncbi/vadr.git
   
   :link: table2asn Documentation: https://github.com/svn2github/NCBI_toolkit/blob/master/src/app/table2asn/table2asn.cpp


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
  Crystal Gigante | Christina Hutson | Brent Jenkins | Yu Li | Ana Litvintseva\
  Matt Mauldin | Dakota Howard | Ben Rambo-Martin | James Heuser | Justin Lee | Mili Sheth


   
   
   
   
  
