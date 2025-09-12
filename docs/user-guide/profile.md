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

The files required for GenBank submission will be stored in the `test_output/submission_outputs/<sample_name|batch_name>/genbank` directory. You can find information on how to submit these files to NCBI [here](https://submit.ncbi.nlm.nih.gov/).

### (1) Customizing parameters from the command line:

Parameters can be overridden during runtime by providing various flags to the `nextflow` command.

Example: Modifying the path of the output directory

`nextflow run main.nf -profile test,singularity --workflow biosample_and_sra --species virus --outdir /path/to/output/dir` Certain parameters such as -profile and pathogen type (`--species virus`) are required, while others like `--outdir` can be specified optionally. The complete list of parameters and the types of input that they require can be found in the Parameters page.

### (2) Customizing parameters by modifying the nextflow.config file:

Default parameters can be also be overridden by making changes to the nextflow.config file located in the project directory. By default, if the test option is not provided during runtime, the run configuration will be read from the nextflow.config file.

## Understanding Profiles and Environments:

Within the nextflow pipeline the `-profile` parameter is required to specify the computing environment of the run. The options of `docker`, `singularity` or `conda` can passed in. The conda environment is less stable than the docker or singularity. We recommend you choose docker or singularity when running the pipeline.

Optionally, the `test` option can be specified in the `-profile` parameter. If test is not specified, parameters are read from the nextflow.config file. The test params should remain the same for testing purposes.

## Perform a Dry Run:

For any workflow, you can add `--dry_run true` to run through all the steps but not actually upload files to NCBI's server.  This option produces a few submission log files you can read to check which folders will be uploaded and where they will be uploaded on the host server.

## Submitting to BioSample and/or SRA:

Use the `--workflow biosample_and_sra` workflow option to submit to BioSample, and submit to SRA as well by also specifying `--sra`.  

Note: The column `ncbi-spuid` in the metadata template is used as the BioSample SPUID, and the column `ncbi_sequence_name_sra` is used as the SRA SPUID.  These two fields need to be unique for each sample.
NCBI uses SPUID as temporary linkage IDs to connect a BioSample and corresponding SRA submission.

Note: SRA submission supports uploading both Nanopore and Illumina data. These will be processed as separate submission.xml files and separate uploads, as required by NCBI.

## Submitting to GenBank: 

Use the `--workflow genbank` workflow option to submit to GenBank. Please note that a GenBank submission requires a BioSample accession ID assigned by NCBI.  If you successfully ran `--workflow biosample_and_sra` previously, you can find your updated metadata file in the `final_submission_outputs` by folder by default.  Check it to make sure your accession IDs were successfully assigned.  Supply this file using `--updated_meta_path` (*NOT* `--meta_path`).  Note: TOSTADAS will automatically search for `--updated_meta_path` in your `--outdir` if you don't explicitly provide it.

❗ Note: you can only submit raw files to SRA, not to Genbank.

## Fetching NCBI Accession IDs:

TOSTADAS will go search for and fetch report.xml files, aggregate the results into a csv file, and create an updated metadata Excel file including the validated metadata and accession IDs, if assigned.
This report CSV file and updated metadata Excel file are placed in the `final_submission_outputs` by folder by default.

Run this workflow using `--workflow fetch_accessions`.  Provide the same `--outdir` and `--meta_path` you provided for the original submission, as TOSTADAS uses these two parameters to find your submission folder and fetch the corresponding reports.
If you change the naming of this folder structure, this workflow will not run.

## Running Update Submission:

NCBI allows UI-less updating of BioSample submissions, and TOSTADAS can do this using the `--workflow update_submission` workflow option.

You need to provide `--original_submission_dir` (the path to your original submission that you are updating) and `--meta_path` (the Excel file containing the new data for these same samples).
TOSTADAS will validate the metadata, recreate the same batches as in the original submission (using the batch_summary.json created during the first submission), update the original submission file and submit it.

It will save the updated submissions as date-stamped batch folders under `--outdir` and within a subdirectory called the basename of your metadata file.

Note: TOSTADAS uses the `ncbi-spuid` field to match samples in the metadata file and the original submission.xml.  The `sample_name` field is not preserved in the submission.xml, so it cannot be used as an identifier for this workflow.

Note: Please make sure your updated metadata Excel file has a `biosample_accession` column that contains accurate accession IDs.  TOSTADAS does not check these for accuracy.  Please make sure they are correct.

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
