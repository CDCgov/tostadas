# Profile Options & Input Files

## Input Files Required:

❗ Note: Currently, the pipeline does not accept input files containing period marks . in their naming convention.

### (A) Running Annotation and Submission to GenBank and SRA:

| Input files | File type | Description |
| --- | --- | --- |
| fasta | .fasta | Single sample fasta sequence file(s) |
| fastq | .fastq | Single sample fastq sequence file(s) |
| metadata | .xlsx | Multi-sample metadata matching metadata spreadsheets provided in input\_files |
| ref\_fasta | .fasta | Reference genome to use for the liftoff\_submission branch of the pipeline |
| ref\_gff | .gff | Reference GFF3 file to use for the liftoff\_submission branch of the pipeline |
| submission\_config | .yaml | configuration file for submitting to NCBI, sample versions can be found in repo |

All annotation workflows require single sample fasta input files. Input fasta files can contain multiple contigs or chromosomes, but all sequences in the file must come from the same specimen.

### (B) Running SRA Submission only:

| Input files | File type | Description |
| --- | --- | --- |
| fastq | .fastq | Single sample fastq sequence file(s) |
| metadata |     | .xlsx |
| submission\_config | .yaml | configuration file for submitting to NCBI, sample versions can be found in repo |

❗ This pipeline has been tested with paired-end sequence data.

Example metadata [Link](https://github.com/CDCgov/tostadas/blob/bb47dce749eada90f3c879a3e373a2e27c36eca4/assets/sample_metadata/MPXV_metadata_Sample_Run_1.xlsx)

### Submitting to GenBank

The files required for GenBank submission will be stored in the `test_output/submission_outputs/<sample_name>/submission_files/GENBANK/` directory. You can find information on how to submit these files to NCBI [here](https://submit.ncbi.nlm.nih.gov/).

## Customizing Parameters:

Parameters can be customized from the command line or by modifying one of the following configuration files: standard.json, standard.yml or nextflow.config.

### (1) Customizing parameters from the command line:

Parameters can be overridden during runtime by providing various flags to the `nextflow` command.

Example: Modifying the path of the output directory

`nextflow run main.nf -profile test,singularity --virus --output_dir /path/to/output/dir` Certain parameters such as -profile and pathogen type (`--virus`) are required, while others like `--output_dir` can be specified optionally. The complete list of parameters and the types of input that they require can be found in the Parameters page.

### (2) Customizing parameters by modifying the standard.json or standard.yml files:

Default parameters can be overridden by making changes to either the standard.yml or standard.json files located in the ./params directory. To modify the run with the updated parameters, use the `--params-file` runtime parameter and specify which file contains the updated parameters.

Example:

`nextflow run main.nf -profile test,singularity --virus -params-file <standard_params.yml or standard_params.json>`

### (3) Customizing parameters by modifying the nextflow.config file:

Default parameters can be also be overridden by making changes to the nextflow.config file located in the project directory. By default, if the test option is not provided during runtime, the run configuration will be read from the nextflow.config file.

## Understanding Profiles and Environments:

Within the nextflow pipeline the `-profile` parameter is required to specify the computing environment of the run. The options of `docker`, `singularity` or `conda` can passed in. The conda environment is less stable than the docker or singularity. We recommend you choose docker or singularity when running the pipeline.

Optionally, the `test` option can be specified in the `-profile` parameter. If test is not specified, parameters are read from the nextflow.config file. The test params should remain the same for testing purposes.

## Running with Annotation and Submission:

You will want to define whether to run the full pipeline with submission or without submission using the `--submission` and `--annotation` flags. By default the pipeline will run both sub-workflows and submit to submit to GenBank and SRA. If you want to submit to only SRA, specify `--genbank false --sra`.

`nextflow run main.nf -profile <singularity/docker/conda> --virus --genbank --sra --submission_wait_time 5`

## Running Submission only:

You will want to define whether to run the full pipeline with submission or without submission using the `--submission` and `--annotation` flags. By default, the pipeline will run both sub-workflows. To only run the submission sub-workflow, specify `--annotation false`. By default the pipeline will submit to GenBank and SRA. If you want to submit to only SRA, specify `--genbank false --sra`.

❗ Note: you can only submit raw files to SRA, not to Genbank.

`nextflow run main.nf -profile <test,standard>,<singularity,docker> --<virus,bacteria> --annotation false --sra --submission_wait_time 5`

## Submission Pre-requisites:

The submission component of the pipeline is adapted from SeqSender public database submission pipeline. It has been developed to allow the user to create a config file to select which databases they would like to upload to and allows for any possible metadata fields by using a YAML to pair the database's metadata fields with your personal metadata field columns. The requirements for this portion of the pipeline to run are listed below.

(A) Create Appropriate Accounts as needed for the SeqSender public database submission pipeline integrated into TOSTADAS:

*   NCBI: If uploading to NCBI archives such as BioSample/SRA/Genbank, you must complete the following steps:
    
    *   Create a center account: Contact the following e-mail for account creation: sra@ncbi.nlm.nih.gov and provide the following information:
        *   Suggested center abbreviation (16 char max)
        *   Center name (full), center URL & mailing address (including country and postcode)
        *   Phone number (main phone for center or lab)
        *   Contact person (someone likely to remain at the location for an extended time)
        *   Contact email (ideally a service account monitored by several people)
        *   Whether you intend to submit via FTP or command line Aspera (ascp)
    *   Gain access to an upload directory: Following center account creation, a test area and a production area will be created. Deposit the XML file and related data files into a directory and follow the instructions SRA provides via email to indicate when files are ready to trigger the pipeline.
    *   GISAID: GISAID support is not yet implemented but it may be added in the future.

(B) Config File Set-up:

*   The template for the submission config file can be found in bin/default\_config\_files within the repo. This is where you can edit the various parameters you want to include in your submission. Read more at the SeqSender docs.
*   You can find more information on how to setup your own submission config and additional information on fields in the following guide: Submission Config Guide.
