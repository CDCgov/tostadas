# Submission Guide

## Toggling Submission:
You will want to define whether to run the full pipeline with submission or without submission using the `--submission` flag. By default the pipeline will submit to GenBank and SRA. If you want to submit to only SRA, specify `--genbank false --sra`.

## Submission Pre-requisites:
Link to this guide and remove from previous section

The submission component of the pipeline uses the processes that are directly integrated from SeqSender public database submission pipeline. It has been developed to allow the user to create a config file to select which databases they would like to upload to and allows for any possible metadata fields by using a YAML to pair the database's metadata fields with your personal metadata field columns. The requirements for this portion of the pipeline to run are listed below.

### (A) Create Appropriate Accounts as needed for the SeqSender public database submission pipeline integrated into TOSTADAS:

NCBI: If uploading to NCBI archives such as BioSample/SRA/Genbank, you must complete the following steps:

* Create a center account: Contact the following e-mail for account creation :   sra@ncbi.nlm.nih.gov  and provide the following information:
 * Suggested center abbreviation (16 char max)
 * Center name (full), center URL & mailing address (including country and postcode)
 * Phone number (main phone for center or lab)
 * Contact person (someone likely to remain at the location for an extended time)
 * Contact email (ideally a service account monitored by several people)
 * Whether you intend to submit via FTP or command line Aspera (ascp)
 * Gain access to an upload directory: Following center account creation, a test area and a production area will be created. Deposit the XML file and related data files into a directory and follow the instructions SRA provides via email to indicate when files are ready to trigger the pipeline.
 * GISAID: A GISAID account is required for submission to GISAID, you can register for an account at (https://www.gisaid.org/). Test submissions are first required before a final submission can be made. When your first test submission is complete contact GISAID at hcov-19@gisaid.org to receive a personal CID. GISAID support is not yet implemented but it may be added in the future.

### (B) Config File Set-up:

The template for the submission config file can be found in `bin/default_config_files` within the repo. This is where you can edit the various parameters you want to include in your submission. Read more at the SeqSender docs.
You can find more information on how to setup your own submission config and additional information on fields in the following guide: Submission Config Guide.

❗ Pre-requisite to submit to GenBank: Copy the program `table2asn` to your `tostadas/bin` directory by running the following lines of code:

* `cd ./tostadas/bin/`
* `wget https://ftp.ncbi.nlm.nih.gov/asn1-converters/by_program/table2asn/linux64.table2asn.gz`
* `gunzip linux64.table2asn.gz`
* `mv linux64.table2asn table2asn`

## Required Files for Submission
* genbank
