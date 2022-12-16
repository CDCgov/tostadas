# TOSTADAS &#8594; <span style="color:blue"><u>**T**</u></span>oolkit for <span style="color:blue"><u>**O**</u></span>pen <span style="color:blue"><u>**S**</u></span>equence <span style="color:blue"><u>**T**</u></span>riage, <span style="color:blue"><u>**A**</u></span>nnotation and <span style="color:blue"><u>**DA**</u></span>tabase <span style="color:blue"><u>**S**</u></span>ubmission :microscope: :computer:

## MPOX ANNOTATION AND SUBMISSION PIPELINE

<!-- [![GitHub Downloads](https://img.shields.io/github/downloads/CDCgov/tostadas/total.svg?style=social&logo=github&label=Download)](https://github.com/CDCgov/tostadas/releases) -->
[![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A521.10.3-23aa62.svg?labelColor=000000)](https://www.nextflow.io/) [![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/) [![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/) [![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)

## Overview
  The MPOX Annotation and Submission pipeline facilitates the running of several Python scripts, which validate metadata (QC), annotate assembled genomes, and submit to NCBI. 

## Table of Contents
- [Overview](#overview)
 - [Table of Contents](#table-of-contents)
 - [Pipeline Summary](#pipeline-summary)
    - [Metadata Validation](#metadata-validation)
    - [Liftoff](#liftoff)
    - [Submission](#submission)
 - [Environment Set-up](#environment-setup)
 - [Quickstart](#quick-start)
 - [Usage](#usage)
    - [Input Files Required](#input-files-required)
    - [Customizing Parameters](#customizing-parameters)
    - [Defining Entrypoints](#defining-entrypoints)
    - [Running Submission](#running-submission)
    - [Running The Pipeline With Conda](#running-the-pipeline-with-conda)
    - [Running The Pipeline With Docker](#running-the-pipeline-with-docker)
  - [Outputs](#outputs)
    - [Pipeline Overview](#pipeline-overview)
    - [Output Directory Formatting](#output-directory-formatting)
    - [Understanding Pipeline Outputs](#understanding-pipeline-outputs)
  - [Parameters](#parameters)
    - [Input Files](#input-files)
    - [Specify Subworkflows to Run](#specify-which-subworkflows-to-run)
    - [Parameters for cleanup workflow](#parameters-specific-to-cleanup-workflow)
    - [Output Directory](#specify-where-output-files-should-be-stored-and-if-they-should-overwritten)
    - [Metadata Validation Workflow Params](#specify-metadata-validation-workflow-params)
    - [Liftoff Workflow Params](#specify-liftoff-workflow-params)
  - [Helpful Links](#helpful-links)

## Pipeline Summary

### Metadata Validation
The validation workflow checks if metadata conforms to NCBI standards and matches the input fasta file. The script also splits a multi-sample xlsx file into a separate .tsv file for each individual.

### Liftoff
The liftoff workflow annotates input fasta-formatted genomes and produces accompanying gff and genbank tbl files. The input includes the reference genome fasta, reference gff and your multi-sample fasta and metadata in .xlsx format. 

### Submission 
Submission workflow generates the necessary files for Genbank submission, generates a BioSample ID, then optionally uploads Fastq files via FTP to SRA. This workflow was adapted from [SeqSender](https://github.com/CDCgov/seqsender) public database submission pipeline.

## Environment Setup 
The environment setup needs to occur within a terminal, or can optionally be handled by the Nextflow pipeline according to the conda block of the nextflow.config file.
* Note: With mamba and nextflow installed, when you run nextflow it will create the environment from the provided environment.yml. 
* If you want to create a personalized environment you can create this environment as long as the environment name lines up with the environment name provided in the environment.yml file.

#### (A) First install mamba:
```
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh
bash Mambaforge-$(uname)-$(uname -m).sh -b -p $HOME/mambaforge
```
#### (B) Add mamba to PATH:
```
export PATH="$HOME/mambaforge/bin:$PATH"
```
#### (C) Now you can create the conda environment and install the dependencies set in your environment.yml:   
```
mamba create -n tostadas -f environment.yml   
```
#### (D) After the environment is created activate the environment. Always make sure to activate the environment with each new session.
```bash
source activate tostadas
```
#### (E) To examine which environment is active, run the following conda command: ```conda env list```  , then the active environment will be denoted with an asterisk*

#### (F) The final piece to the environment set up is to install nextflow (optionally with conda):

* First make sure your path is set correctly and you are active in your tostadas environment. Then run the following command to install nextflow with Conda: 
```bash
mamba install -c bioconda nextflow
```
Access the link provided for help with installing [nextflow](https://www.nextflow.io/docs/latest/getstarted.html)

## Quick Start

### The configs are set-up to run the default params with the test option

#### (A) First you want to ensure nextflow was installed successfully by running ```Nextflow -v```
        * Version of nextflow should be >=22.10.0

#### (B) Now check that you are in the project repo.
This is the default directory set in the nextflow.config file to allow for running the nextflow pipeline with the provided test input files.

#### (C) Finally you can run the following nextflow command to execute the scripts with default parameters: 

```bash
nextflow run main.nf -profile test,conda
```

#### (D) The outputs of the pipeline will appear in the "nf_test_results" folder with in the project directory (unless you changed that parameter in nextflow.config).

## Usage
#### This section walks through the available parameters to customize your workflow.

#### Input Files Required: 

##### (A) This table lists the required files to run metadata validation and liftoff annotation:
| Input files | File type | Description                                                                               |
|-------------|-----------|-------------------------------------------------------------------------------------------|
| fasta       | .fasta    | Multi-sample fasta file with your input sequences                                         |
| metadata    | .xlsx     | Multi-sample metadata matching metadata spreadsheets provided in input_files              |
| ref_fasta   | .fasta    | Reference genome to use for the  liftoff_submission branch of the pipeline                |
| ref_gff     | .gff      | Reference GFF3 file to use for the  liftoff_submission branch of  the pipeline            | 

##### (B) This table lists the required files to run with submission: 
| Input files | File type | Description                                                                               |
|-------------|-----------|-------------------------------------------------------------------------------------------|
| fasta       | .fasta    | Multi-sample fasta file with your input sequences                                         |
| metadata    | .xlsx     | Multi-sample metadata matching metadata spreadsheets provided in input_files              |
| ref_fasta   | .fasta    | Reference genome to use for the  liftoff_submission branch of the pipeline                |
| ref_gff     | .gff      | Reference GFF3 file to use for the  liftoff_submission branch of  the pipeline            | 
| submission_config| .yaml    | configuration file for submitting to NCBI, sample versions can be found in repo       |


#### Customizing Parameters:
The standard_params.config file found within the conf directory is where parameters can be adjusted based on preference for running the pipeline. First you will
want to ensure the file paths are correctly set for the params listed above depending on your preference for submitting your results. 
 * Adjust your file inputs within standard_params.config ensuring accurate file paths for the inputs listed above.
 * The params can be changed within the standard_params.config or you can change the standard.yml file inside of the nf_params directory and pass it in with the ```-params-file <params.yml or params.json>```
 * Note: DO NOT EDIT the main.nf file or other paths in the nextflow.config unless familiar with editing nextflow workflows

#### Understanding Profiles and Environments:
Within the nextflow pipeline the -profile option is required as an input. The profile options with the pipeline include test and standard. These two options can be seen listed in the nextflow.config file. The test params should remain the same for testing purposes, but the standard profile can be changed to fit user preferences. Also within the nextflow pipeline there is the optional use of varying environments as the second -profile input. Nextflow expects at least one of these configurations to be passed in: ```-profile <test/standard>,<conda/docker/singularity>```

#### Defining Entrypoints:
Now that your file paths are set within your standard.yml or standard_params.config file you will want to define whether to run the full pipeline with submission or without submission. This is defined within the standard_params.config file underneath the subworkflow section as run_submission ```run_submission = true/false```
 * Apart from this main bifurcation, there exists entrypoints that you can use to access specific processes. These are listed in the table below.

#### Running Submission:
The submission piece of the pipeline allows the user to create a config file to select which databases they would like to upload to and allows for any possible metadata fields by using a YAML to pair the database's metadata fields which your personal metadata field columns. The requirements for this portion of the pipeline to run are listed below. 

(A) Create Appropriate Accounts:
* NCBI: If uploading to NCBI, an account is required along with a center account approved for submitting via FTP. Contact the following for account creation:gb-admin@ncbi.nlm.nih.gov.
* GISAID: A GISAID account is required for submission to GISAID, you can register for an account at https://www.gisaid.org/. Test submissions are first required before a final submission can be made. When your first test submission is complete contact GISAID at hcov-19@gisaid.org to recieve a personal CID.

(B) Config File Set-up:
* The submission_config file is located in submission_scripts/config_files directory
* The script automatically defaults to the default_config.yaml to change the submission config to your own, you must run ```--submission_config <file path to custom config>```  as a flag, or change this parameter in the standard_params.config file.
* The template for the submission .yaml file can be found in submission scripts/config_files within the repo. This is where you can edit the various parameters you want to include in your submission. Then you must set the file path accordingly in the nextflow.config file or with the ```--submission_config``` flag to overwrite the old .yaml file (as mentioned above).



#### Running The Pipeline with Conda:
(A) The typical command to run the pipeline based on your custom parameters defined/saved in the standard_params.config and created conda environment is as follows:
      Note: The ```-profile``` flag is responsible for defining profiles. These profiles are defined in the nextflow.config file including: 
           * test profile which runs the command based on a default set of params listed in the config file for you to be able to see and example run. 
           * standard profile which runs the pipeline based on how you have set the params in the config file under the standard profile section
```bash
nextflow run main.nf -profile standard,conda
``` 
Another option to run the pipeline with specified parameters is with the following command:

```bash
nextflow run main.nf -profile standard,conda --<param name> <param value>
```

(B) Either one of the above commands will launch the nextflow pipeline and show the progress of the subworkflows and checks looking similar to below depending on the entrypoint specified. 

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


(C) Outputs will be generated in the nf_test_results folder (if running the test parameter set) unless otherwise specified in your standard_params.config file as output_dir param. 

#### Running The Pipeline with Docker:
The pipeline can be ran with Docker as well. This container has been set according to the conda environment and dependencies needed to run the pipeline. To run the pipeline using Docker use one of the following commands:
    
  To run with custom params:
```bash
nextflow run main.nf -profile standard,docker 
``` 
  For a dry run with the test params:
```bash
nextflow run main.nf -profile test,docker 
```
Then, if you want to add in custom entrypoints or params the same command can be used that was listed for use with conda: 
```bash
nextflow run main.nf -profile <param set>,docker --<param name> <param value>
```

#### Entrypoints:

Table of entrypoints available for the nextflow pipeline:

| Workflow             | Description                                                 |
|----------------------|-------------------------------------------------------------|
| only_validate_params | Validates parameters utilizing the validate params process within the utility sub-workflow |
| only_cleanup_files   | Cleans-up files utilizing the clean-up process within the utility sub-workflow             |
| only_validation      | Runs the metadata validation process only                           |
| only_liftoff      | Runs the liftoff annotation process only                           |
| only_submission      | Runs submission sub-workflow only                           |
| only_initial_submission | Runs the initial submission process but not follow-up within the submission sub-workflow               |
| only_update_submission  | Updates NCBI submissions                                 |

* Documentation for using entrypoints with NF can be found at [Nextflow_Entrypoints](https://www.nextflow.io/blog/2020/cli-docs-release.html) under section 5:. 


(D) The following command can be used to specify entrypoints for the workflow:

```bash
nextflow run main.nf -profile <param set>,<env> -entry <insert option from table above>
```

## Outputs
The following section walks through the outputs from the pipeline.

#### Pipeline Overview:
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

#### Output Directory Formatting:
The outputs are recorded in the directory specified within the nextflow.config file and will contain the following:
* validation_outputs (**name configurable with val_output_dir)
    * sample_metadata_run
        * errors
        * tsv_per_sample
* liftoff_outputs (**name configurable with final_liftoff_output_dir)
    * final_sample_metadata_file
        * errors
        * fasta
        * liftoff
        * tbl 
* submission_outputs (**name and path configurable with submission_output_dir)
    * individual_sample_batch_info
        * biosample_sra
        * genbank
        * accessions.csv
    * terminal_outputs
    * commands_used
* liftoffCommand.txt

#### Understanding Pipeline Outputs:
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


### Input files

| Param                      | Description                                             | Input Required   |
|----------------------------|---------------------------------------------------------|------------------|
| --fasta_path               | Path to fasta file                                      |        Yes (path as string)      |
| --ref_fasta_path           | Reference Sequence file path                            |        Yes (path as string)      |
| --meta_path                | Meta-data file path for samples                         |        Yes (path as string)      |
| --ref_gff_path             | Reference gff file path for annotation                  |        Yes (path as string)      |
| --liftoff_script           | Path to liftoff.py script                               |        Yes (path as string)      |
| --validation_script        | Path to validation.py script                            |        Yes (path as string)      |
| --submission_script        | Path to submission.py script                            |        Yes (path as string)       |
| --env_yml                  | Path to environment.yml file                            |        Yes (path as string)       |


### Specify which subworkflows to run
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --run_submission           | Toggle to running submission                            | Yes (true/false as bool) |
| --cleanup                  | Toggle for running cleanup subworkflows                 | Yes (true/false as bool) |
### Parameters specific to cleanup workflow
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --clear_nextflow_log     | Clears nextflow work log                                |        Yes (true/false as bool)      |
| --clear_nextflow_dir     | Clears nextflow working directory                       |  Yes (true/false as bool)|
| --clear_work_dir         | Param to clear work directory created during workflow   |  Yes (true/false as bool) |                
| --clear_conda_env        | Clears conda environment                                |  Yes (true/false as bool) |               
| --clear_nf_results       | Remove results from nextflow outputs                    |  Yes (true/false as bool) |               


### Specify where output files should be stored and if they should be overwritten
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --output_dir               | File path to submit outputs from pipeline              |        Yes (path as string)      |
| --overwrite_output         | Toggle to overwriting output files in directory        | Yes (true/false as bool) |


### Specify metadata validation workflow params:
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --val_output_dir         | File path for outputs specific to validate sub-workflow |        Yes (folder name as string)      |
| --val_date_format_flag   | Flag to change date output                               |  Yes (-s, -o, or -v as string)   |
| --val_keep_pi            | Flag to keep personal identifying info, if provided otherwise it will return an error|        Yes (true/false as bool)      |


### Specify liftoff workflow params:
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


### Specify submission workflow params:
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --submission_output_dir | Either name or relative/absolute path for the outputs from submission | Yes (name or path as string) |
| --submission_prod_or_test | Whether to submit samples for test or actual production | Yes (prod or test as string) |
| --submission_only_meta   | Full path directly to the dirs containing validate metadata files|        Yes (path as string)      |
| --submission_only_gff    | Full path directly to the directory with reformatted GFFs    |        Yes (path as string)      |
| --submission_only_fasta  | Full path directly to the directory with split fastas for each sample|        Yes (path as string)      |
| --submission_config      | Configuration file for submission to public repos       |        Yes (path as string)      |
| --submission_wait_time **|Calculated based on sample number(3 * 60secs * sample_num)| integer (seconds)|
| --batch_name | Name of the batch to prefix samples with during submission | Yes (name as string)

## Helpful Links:     
   :link: Anaconda Install: https://docs.anaconda.com/anaconda/install/
   
   :link: Nextflow Documentation: https://www.nextflow.io/docs/latest/getstarted.html
