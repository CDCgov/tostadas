# Profile Options & Input Files

This section walks through the available parameters to customize your workflow.

## Input Files Required:
### (A) This table lists the required files to run metadata validation and annotation:

|Input files	|File type	|Description|
|---------------|-----------|-----------|
|Running Annotation and Submission|||		
|fasta	|.fasta	|Single sample fasta sequence file(s)|
|metadata	|.xlsx	|Multi-sample metadata matching metadata spreadsheets provided in input_files|
|Running Submission only without Annotation (Raw Files)|||		
|fasta	|.fasta	|Single sample fasta sequence file(s)|
|metadata	|.xlsx	|Multi-sample metadata matching metadata spreadsheets provided in input_files|
| fasta | .fasta | Single sample fasta sequence file(s) | | metadata | .xlsx | Multi-sample metadata matching metadata spreadsheets provided in input_files | | ref_fasta | .fasta | Reference genome to use for the liftoff_submission branch of the pipeline | | ref_gff | .gff | Reference GFF3 file to use for the liftoff_submission branch of the pipeline |

** Please note that the pipeline expects ONLY pre-split FASTA files, where each FASTA file contains only the sequence(s) associated with its corresponding sample. The name of each FASTA file corresponding to a particular sample must be placed within your metadata sheet under fasta_file_name.

Here is an example of how this would look like.

### (B) This table lists the required files to run with submission:

|Input files	|File type	|Description|
|fasta	|.fasta	|Single sample fasta sequence file(s) sequences|
|metadata	|.xlsx	|Multi-sample metadata matching metadata spreadsheets provided in input_files|
|ref_fasta	|.fasta	|Reference genome to use for the liftoff_submission branch of the pipeline|
|ref_gff	|.gff	|Reference GFF3 file to use for the liftoff_submission branch of the pipeline|
|submission_config	|.yaml	|configuration file for submitting to NCBI, sample versions can be found in repo|

## Customizing Parameters:
Parameters can be customized from the nextflow.config file or from the command line, through the use of flags.

### Customizing the nextflow.config
The nextflow.config file is where parameters can be adjusted based on preference for running the pipeline.

Adjust your file inputs within standard_params.config ensuring accurate file paths for the inputs listed above. The params can be changed within the standard_params.config or you can change the standard.yml/standard.json file inside the params directory and pass it in with: `-params-file <standard_params.yml or standard_params.json>`

❗ DO NOT EDIT the `main.nf` file unless familiar with editing nextflow workflows

### Customizing Parameters from the Command Line
Parameters can be overridden during runtime by providing various flags to the nextflow command.

Example: Modifying the path of the output directory

`nextflow run main.nf -profile test,singularity --virus --output_dir /path/to/output/dir`
Certain parameters such as `-profile` and pathogen type (`--virus`) are required, while others like `--output_dir` can be specified optionally. The complete list of parameters and the types of input that they require can be found in the Parameters page.

## Understanding Profiles and Environments:
Within the nextflow pipeline the `-profile` parameter is required as an input. The profile option can be specified as `test`. If test is not specified, parameters are read from the `nextflow.config` file. The test params should remain the same for testing purposes, but the standard profile can be changed to fit user preferences. The run environment is supplied as the second argument to the `profile` parameter. The options of `docker`, `singularity` or `conda` can passed in. The conda environment is less stable than the docker or singularity. we recommend you choose docker or singularity when running the pipeline.

## Running with Annotation and Submission:
By default, the pipeline will run the annotation and submission and sub-workflows. You may specify which databases to submit to using the database flags `--genbank` or `--sra`.

* `nextflow run main.nf -profile <singularity/docker/conda> --virus --genbank --sra --submission_wait_time 5`
params listed here: https://github.com/CDCgov/tostadas/blob/dev/nextflow.config

## Running Submission Only:
By default, the pipeline will run the annotation and submission and sub-workflows. You may override this but using the `--submission` and `--annotation` flags. To run only submission, use the flag `--annotation false` in your nextflow command.

❗ Note: you can only submit raw files to SRA, not to Genbank.

* `nextflow run main.nf -profile <test,standard>,<singularity,docker> --<virus,bacteria> --annotation false --sra --submission_wait_time 5`
Now that your file paths are set within your standard.yml or standard.json or nextflow.config file, you will want to define whether to run the full pipeline with submission or without submission. This is defined within the standard_params.config file underneath the subworkflow section as submission submission = true/false

### Q. Can we use standard.yml standard.json?

Submission Pre-requisites:
The submission component of the pipeline is adapted from SeqSender public database submission pipeline. It has been developed to allow the user to create a config file to select which databases they would like to upload to and allows for any possible metadata fields by using a YAML to pair the database's metadata fields with your personal metadata field columns. The requirements for this portion of the pipeline to run are listed below.

#### (A) Create Appropriate Accounts as needed for the SeqSender public database submission pipeline integrated into TOSTADAS:

NCBI: If uploading to NCBI archives such as BioSample/SRA/Genbank, you must complete the following steps:

* Create a center account: Contact the following e-mail for account creation: sra@ncbi.nlm.nih.gov  and provide the following information:
 * Suggested center abbreviation (16 char max)
 * Center name (full), center URL & mailing address (including country and postcode)
 * Phone number (main phone for center or lab)
 * Contact person (someone likely to remain at the location for an extended time)
 * Contact email (ideally a service account monitored by several people)
 * Whether you intend to submit via FTP or command line Aspera (ascp)
 * Gain access to an upload directory: Following center account creation, a test area and a production area will be created. Deposit the XML file and related data files into a directory and follow the instructions SRA provides via email to indicate when files are ready to trigger the pipeline.
 * GISAID: A GISAID account is required for submission to GISAID, you can register for an account at (https://www.gisaid.org/). Test submissions are first required before a final submission can be made. When your first test submission is complete contact GISAID at (hcov-19@gisaid.org) to receive a personal CID. GISAID support is not yet implemented but it may be added in the future.

#### (B) Config File Set-up:

The template for the submission config file can be found in `bin/default_config_files` within the repo. This is where you can edit the various parameters you want to include in your submission. Read more at the [SeqSender](https://cdcgov.github.io/seqsender/#id_3-config-file-creation) docs.
You can find more information on how to setup your own submission config and additional information on fields in the following guide: [Submission Config Guide](https://github.com/CDCgov/tostadas/blob/b904111d78262efb82589bdd72b0482f27770f87/docs/submission_config_guide.md).
❗ Pre-requisite to submit to GenBank: Copy the program [table2asn](https://www.ncbi.nlm.nih.gov/genbank/table2asn/) to you tostadas/bin directory by running the following lines of code:

* `cd ./tostadas/bin/`
* `wget https://ftp.ncbi.nlm.nih.gov/asn1-converters/by_program/table2asn/linux64.table2asn.gz`
* `gunzip linux64.table2asn.gz`
* `mv linux64.table2asn table2asn`