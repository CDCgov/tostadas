# Submission Config Guide 

## Table of Contents
- [Introduction](#introduction)
- [General Format & Content](#general-format--content)
    - [Specifying NCBI Databases](#specifying-ncbi-databases)
    - [Email Notifcation For Genbank/Table2asn](#email-notifcation-for-genbanktable2asn)
- [Information For Each Field](#information-for-each-field)
    - [Personal Fields](#personal-fields)
    - [General Fields](#general-fields)
    - [General NCBI Fields](#general-ncbi-fields)
    - [NCBI Databases Fields (General)](#ncbi-databases-fields-general)
    - [NCBI Databases Fields (Specific)](#ncbi-databases-fields-specific)

## Introduction 

A submission configuration file (.config) is needed in order to successfully submit samples to NCBI or GISAID databases through TOSTADAS. 

This file contains all necessary information about the user's credentials and properties for the submission itself to each of the NCBI databases. 

Before beginning to populate the submission configuration file, please ensure that you have NCBI access (a working username/password for authentication). For more information on how to gain access to NCBI and/or GISAID, it can be found [here](../README.md#more-information-on-submission).

## General Format & Content

The fields and corresponding example values can be found here: [Default Config](../bin/default_config_files/default_config.yaml).

### Specifying NCBI Databases 

The submission configuration file contains multiple fields for specifying which NCBI databases to submit samples to. 

These fields are __ONLY__ used when the __submission_database__ (nextflow parameter) is set to __'submit'__. Otherwise, the databases specified for the NF parameter ('sra', 'gisaid', 'biosample', 'joint_sra_biosample') will take precedence over the contents of the submission config. This allows easy specification for a single database through the NF parameter set and a more complex combination of databases to submit to, based on your specific needs.

The following are the specific fields that toggle between databases for submission:
```
submit_Genbank: True
submit_GISAID: True
submit_SRA: False
submit_BioSample: True
joint_SRA_BioSample_submission: True
```
TOSTADAS will submit to each database that is set to __True__ and ignore all others.

### Email Notifcation For Genbank/Table2asn

There is built-in functionality to toggle email notifications on/off, specifically during Genbank/Table2asn submission, as well as the recipients of these emails. 

The Nextflow parameter that controls toggling this functionality on/off is: __send_submission_email__. Set to __True__ if you would like to send out an email to recipients during this submission configuration, otherwise __False__ if you would like it disabled. 

As for specifying the recipients of these emails, this can be done within your submission configuration file under the __notif_email_recipient__ field. If you would like to specify multiple recipients for these emails, then you can append the field name. Here is an example in practice: 
```
notif_email_recipient1: 'randomemail@random.com'
notif_email_recipient2: 'randomemail2@random.com'
```

## Information For Each Field

### Personal Fields

| Field Name                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| contact_email1  |  General email for potential contact   |    Yes (string)      |
| contact_email2  |  A second general email for potential contact   |    Yes (string)      |
| submitter_info |  Contains subfields for the submitter's personal information   |    Yes (string)      |
| NCBI / username |  Your personal username credential for NCBI   |    Yes (string)      |
| NCBI / password |  Your personal password credential for NCBI   |    Yes (string)      |
| organization_name |  Name of the organization or company you are affiliated with   |    Yes (string)      |
| ncbi / citation_address |  Contains subfields for information about the location for sample generation, for citation purposes   |    Yes (string)      |
| ncbi / publication_title |  Name of the publication or project   |    Yes (string)      |
| ncbi / BioProject |  Collection of biological data related to a single initiative, originating from a single organization or from a consortium   |    Yes (string)      |
| ncbi / Center_title |  Name of your affiliated center / group   |    Yes (string)      |
| gisaid / username |  Your personal username credential for GISAID   |    Yes (string)      |
| gisaid / password |  Your personal password credential for GISAID   |    Yes (string)      |


### General Fields

| Field Name                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| submit_Genbank  |  Toggle submission of samples to Genbank  |    Yes (bool)      |
| submit_GISAID  |  Toggle submission of samples to GISAID  |    Yes (bool)      |
| submit_SRA  |  Toggle submission of samples to SRA  |    Yes (bool)      |
| submit_BioSample  |  Toggle submission of samples to BioSample  |    Yes (bool)      |
| joint_SRA_BioSample_submission  |  Toggle submission of samples to joint SRA + BioSample  |    Yes (bool)      |
| genbank_submission_type  |  Method or type for submitting Genbank (i.e. table2asn)  |    Yes (string)      |
| authorset  |  Field or name designating the authors per sample   |    Yes (string)      |
| organism_name  |  Name of the organism for submitted samples   |    Yes (string)      |
| metadata_file_sep  |  The separation for your metadata file (i.e. \t)   |    Yes (string)      |
| fasta_sample_name_col  |  Name of column containing name of samples   |    Yes (string)      |
| collection_date_col  |  Name of column containing the collection dates for the samples   |    Yes (string)      |
| baseline_surveillance  |  Whether baseline surveillance occurred or not   |    Yes (bool)      |

### General NCBI Fields 

| Field Name                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| ncbi_org_id              | Organization ID for NCBI             |        Yes (string)      |
| ncbi / hostname              | The FTP host name for NCBI            |        Yes (string)      |
| ncbi / api_url              | URL for the NCBI API            |        Yes (string)      |
| ncbi_ftp_path_to_submission_folders              | Path to the submission folders at endpoint            |        Yes (string)      |


### NCBI Databases Fields (General)

| Field Name                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| ncbi / SRA_file_location               | Location of SRA file              |        Yes (string)      |
| ncbi / SRA_file_column(1-3)              | Name of column containing SRA file information              |        Yes (string)      |
| ncbi / Genbank_organization_type               | Type of organization for Genbank              |        Yes (string)      |
| ncbi / Genbank_organization_role               | Role for Genbank              |        Yes (string)      |
| ncbi / Genbank_spuid_namespace               | The namespace for Genbank              |        Yes (string)      |
| ncbi / Genbank_auto_remove_sequences_that_fail_qc               | Whether or not to remove sequences that fail QC for Genbank              |        Yes (bool)      |

### NCBI Databases Fields (Specific)

| Field Name                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| gisaid / column_names              | The column names from metadata sheet that correspond to various GISAID database variables             |        Yes (string)      |
| SRA_attributes / column_names              | The column names from metadata sheet that correspond to various SRA database variables             |        Yes (string)      |
| BioSample_attributes / column_names              | The column names from metadata sheet that correspond to various BioSample database variables             |        Yes (string)      |
| genbank_cmt_metadata / column_names              | The column names from metadata sheet that correspond to various Genbank database variables             |        Yes (string)      |
| genbank_src_metadata / column_names              | The column names from metadata sheet that correspond to various Genbank database variables             |        Yes (string)      |
