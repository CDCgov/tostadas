# MPXV ANNOTATION AND SUBMISSION PIPELINE 
## Overview
  The MPXV Annotation and Submission pipeline facilitates the running of several Python scripts, which validate metadata (QC), annotate assembled genomes, and submit to NCBI. 

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
The nextflow.config file found within the main project directory is where parameters can be adjusted based on preference for running the pipeline. First you will
want to ensure the file paths are correctly set for the params listed above depending on your preference for submitting your results. 
 * Adjust your file inputs within nextflow.config ensuring accurate file paths for the inputs listed above.
 * Additional parameters can be changed and are listed and defined in the standard_params.yml file.
 * IMPORTANT: when running with submission, the flag --val_meta_file_name must match the meta excel file name prefix
 * The params can be changed within the nextflow.config or you can change the params.yml file and pass it in with the -params-file <params.yml or params.json>
 * Note: DO NOT EDIT the main.nf file or other paths in the nextflow.config unless familiar with editing nextflow workflows

#### Understanding Profiles and Environments:
Within the nextflow pipeline the -profile option is required as an input. The profile options with the pipeline include test and standard. These two options can be seen listed in the nextlofw.congih file. The test params should remain the same for testing purposes, but the standard profile can be changed to fit user preferences. Also within the nextflow pipeline there is the optional use of varying environments as the -profile input. This includes using one of the following -profile <test,standard>,<conda,docker,singularity>.

#### Defining Entrypoints:
Now that your file paths are set within your standard_params.yml or nextflow.config file you will want to define whether to run the full pipeline with
submission or without submission. This is defined within the nextflow.config file underneath the specify which workflows to run or with entrypoints. 
 * The pipeline can be run with or without submission, and a few other entrypoints are customizable and are listed in the table below.
 * To run your pipeline with or without submission depending on preference you should change the nextflow.config param ```with_submission = true/false```

#### Running Submission:
The submission piece of the pipeline allows the user to create a config file to select which databases they would like to upload to and allows for any possible metadata fields by using a YAML to pair the database's metadata fields which your personal metadata field columns. The requirements for this portion of the pipeline to run are listed below. 

(A) Create Appropriate Accounts:
* NCBI: If uploading to NCBI, an account is required along with a center account approved for submitting via FTP. Contact the following for account creation:gb-admin@ncbi.nlm.nih.gov.
* GISAID: A GISAID account is required for submission to GISAID, you can register for an account at https://www.gisaid.org/. Test submissions are first required before a final submission can be made. When your first test submission is complete contact GISAID at hcov-19@gisaid.org to recieve a personal CID.

(B) Config File Set-up:
* The submission_config file is located in submission_scripts/config_files directory
* The script automatically defaults to the default_config.yaml to change the submission_config.yaml you run --submission_config < file path to custom config>  as a flag, or change the parameter in the nextflow.config file.
* The config.yaml can be found in the submission scripts folder of the repo, this is where you can edit the various parameters you want to include in your submission. Then you must set the file path accordingly in the nextflow.config file or with the --submission_config flag to overwrite the old .yaml file



#### Running The Pipeline with Conda:
(A) The typical command to run the pipeline based on your custom parameters defined/saved in the nextflow.config and created conda environment is as follows:
      Note: The -with flag is responsible for defining profiles. These profiles are defined in the nextflow.config file including: 
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
** Note: Depending on the wait time the user wants to specify between initial_submission and update_submission- they will have to insert a command 
 to override the default wait time which is 3 minutes per sample. This command would have a specified value (in seconds) after the flag signifying the total number of seconds to wait example listed: 
 
 ```bash
nextflow run main.nf -profile <profile> <env> --submission_wait_time 360
 ```


(C) Outputs will be set in the nf_test_results folder unless otherwise specified in the nextflow.config file under
the out_dir param. 

#### Running The Pipeline with Docker:
The pipeline can be ran with Docker as well. This container has been set according to the conda environment and dependencies needed to run the pipeline.  To run the pipeline using Docker use one of the following commands:
    
  To run with custom params:
 ```bash
nextflow run main.nf -profile standard,docker 
``` 
  For a dry run with the test params:
 ```bash
nextflow run main.nf -profile test,docker 
```
Then if you want to add in custom entrypoints or params the same command can be used that was listed for use with conda: 
```bash
nextflow run main.nf -profile <profile>,docker --<param name> <param value>
```

#### Entrypoints:

Table of entrypoints available for the nextflow pipeline:

| Workflow             | Description                                                 |
|----------------------|-------------------------------------------------------------|
| --with_submission      | Runs pipeline all the way through to submission             |
| --without_submission   | Runs only metadata validation and liftoff annotation        |
| --only_validate_params | Validates parameters utilizing validate params sub-workflow |
| --only_cleanup_files   | Cleans-up files utilizing clean-up sub-workflow             |
| --only_validation      | Runs validation sub-workflow only                           |
| --only_annotation      | Runs annotation sub-workflow only                           |
| --only_submission      | Runs submission sub-workflow only                           |
| --only_initial_submission | Runs initial submission but not follow-up                |
| --only_update_submission  | Updates NCBI submissions                                 |

* Documentation for using entrypoints with NF can be found at [Nextflow_Entrypoints](https://www.nextflow.io/blog/2020/cli-docs-release.html) under section 5:. 


(D) The following command can be used to specify entrypoints for the workflow:

```bash
nextflow run main.nf -profile <profile> <env> -entry <insert option from table above>
```

## Outputs
The following section walks through the outputs from the pipeline.

#### Pipeline Overview:
The workflow will generate outputs in the following order:

* Validation
    * Responsible for QC of metadata  
    * Aligns sample metadata .xlsx to sample .fasta
    * formats metadata into .tsv format
* Annotation 
    * Extracts features from .gff
    * aligns features
    * annotates sample genomes outputting .gff
* Submission
    * formats for database submission
    * This section runs twice, with the second run occuring after a wait time to allow for all samples to be uploaded to NCBI. Entrypoint `only_update_submission` can be run as many times as necessary until all files are fully uploaded.

#### Output Directory Formatting:
The outputs are recorded in the directory specified within the nextflow.config file and will contain the following:
* validation_outputs
    * sample_metadata_run
        * errors
        * tsv_per_sample
* liftoff_outputs
    * final_sample_metadata_file
        * errors
        * fasta
        * liftoff
        * tbl 
* submission_outputs
    * individual_sample_batch_info
        * biosample_sra
        * genbank
        * accessions.csv
    * sample_outputs
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
When changing these parameters pay attention to the required inputs and make sure that paths line-up and values are within range. To change a parameter you may change with a flag after the nextflow command or change them within the nextflow.config file. 

* IMPORTANT: There are a two parameters (file names) that need to line up if you are running submission. That is the --val_meta_file_name and meta_path.
* Also note the correct formatting and the default calculation of submission_wait_time at the bottom of the params table.


### Input files

| Param                      | Description                                             | Input Required   |
|----------------------------|---------------------------------------------------------|------------------|
| --fasta_path               | Path to fasta file                                      |        Yes       |
| --ref_fasta_path           | Reference Sequence file path                            |        Yes       |
| --meta_path                | Meta-data file path for samples                         |        Yes       |
| --ref_gff_path             | Reference gff file path for annotation                  |        Yes       |
| --liftoff_script           | Path to liftoff.py script                               |        Yes       |
| --validation_script        | Path to validation.py script                            |        Yes       |
| --submission_script        | Path to submission.py script                            |        Yes       |
| --env_yml                  | Path to environment.yml file                            |        Yes       |


### Specify which subworkflows to run
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| run_docker               | Toggle for docker usage                                 | Yes (true/false) |
| run_submission           | Toggle to running submission                            | Yes (true/false) |
| cleanup                  | Toggle for running cleanup subworkflows                 | Yes (true/false) |
### Parameters specific to cleanup workflow
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --clear_nextflow_log     | Clears nextflow work log                                |        Yes       |
| --clear_nextflow_dir     | Clears nextflow working directory                       |  Yes (true/false)|
| --clear_work_dir         | Param to clear work directory created during workflow   |  Yes (true/false |                
| --clear_conda_env        | Clears conda environment                                |  Yes (true/false |               
| --clear_nf_results       | Remove results from nextflow outputs                    |  Yes (true/false |               


### Specify where output files should be stored and if they should overwritten
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --output_dir               | File path to submit outputs from pipeline              |        Yes       |
| --overwrite_output         | Toggle to overwriting output files in directory        | Yes (true/false) |


### Specify metadata validation workflow params:
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --val_meta_file_name     | Name of metadata file name input without extension      |        Yes       |
| --val_output_dir         | File path for outputs specific to validate sub-workflow |        Yes       |
| --val_date_format_flag   | Flag to change date ouptu                               |  Yes(-s,-o,-v)   |
| --val_keep_pi            | Flag to keep personal identifying info, if provided otherwise it will return an error|        Yes       |

** when using the --val_meta_file_name, this must line up with the file name for the --meta_path given if running submission.

### Specify liftoff workflow params:
| Param                       | Description                                             | Input Required   |
|-----------------------------|---------------------------------------------------------|------------------|
| --final_liftoff_output_dir  | File path to liftoff specific sub-workflow outputs      |        Yes       |
| --lift_print_version_exit   | Print version and exit the program                      |  Yes(true/false) |
| --lift_print_help_exit      |  Print help and exit the program                        |  Yes(true/false) |
| --lift_parallel_processes   |  # of parallel processes to use for liftoff             |      Value       |
| --lift_delete_temp_files    |  Deletes the temporary files after finishing transfer   |        Yes       |
| --lift_child_feature_align_threshold  | Only if its child features usually exons/CDS align with sequence identity â‰¥S   |  designate a feature mapped |
| --lift_unmapped_feature_file_name  | Name of unmapped features file name             |        Yes       |
| --lift_copy_threshold       |Minimum sequence identity in exons/CDS for which a gene is considered a copy; must be greater than -s; default is 1.0|     Value      |
|--lift_distance_scaling_factor | Distance scaling factor; by default D =2.0            |      Value       |
| --lift_flank                |Amount of flanking sequence to align as a fraction of gene length| Value[0.0-1.0] |
| --lift_overlap              |Maximum fraction of overlap allowed by 2 features        |  Value[0.0-1.0]  |
| --lift_mismatch             |Mismatch penalty in exons when finding best mapping; by default M=2|     Value         |
| --lift_gap_open             |Gap open penalty in exons when finding best mapping; by default GO=2|     Value         |
| --lift_gap_extend           |Gap extend penalty in exons when finding best mapping; by default GE=1|     Value         |
| --lift_infer_transcripts    |Use if annotation file only includes exon/CDS features and does not include transcripts/mRNA|  Yes(true/false) |
| --lift_copies               |Look for extra gene copies in the target genome          |  Yes(true/false) |
| --lift_minimap_path         |Path to minimap if you did not use conda or pip          |        Yes       |
|--lift_feature_database_name |Name of the feature database, if none, then will use ref gff path to construct one|        Yes       |


### Specify submission workflow params:
| Param                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| --submission_only_meta   | Path directly to the dirs containing validate metadata files|        Yes       |
| --submission_only_gff    | Path directly to the directory with reformatted GFFs    |        Yes       |
| --submission_only_fasta  | Path directly to the directory with split fastas for each sample|        Yes       |
| --submission_config      | Configuration file for submission to public repos       |        Yes       |
| --submission_wait_time **|Calculated based on sample number(3 * 60secs * sample_num)| integer(seconds)|


## Helpful Links:     
   (a)- https://docs.anaconda.com/anaconda/install/
   (b)- https://www.nextflow.io/docs/latest/getstarted.html
