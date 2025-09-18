# More Submission Details

## Table of Contents

- [Input Files Required](#input-files-required)
  - [(A) Running Annotation and Submission to GenBank and SRA](#a-running-annotation-and-submission-to-genbank-and-sra)
  - [(B) Running SRA Submission only](#b-running-sra-submission-only)
- [Understanding Profiles and Environments](#understanding-profiles-and-environments)
- [Perform a Dry Run](#perform-a-dry-run)
- [Submitting to BioSample and/or SRA](#submitting-to-biosample-andor-sra)
- [Submitting to GenBank](#submitting-to-genbank)
- [Fetching NCBI Accession IDs](#fetching-ncbi-accession-ids)
- [Running Update Submission](#running-update-submission)

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


## Understanding Profiles and Environments:

Within the nextflow pipeline the `-profile` parameter is required to specify the computing environment of the run. The options of `docker`, `singularity` or `conda` can passed in. The conda environment is less stable than the docker or singularity. We recommend you choose docker or singularity when running the pipeline.

Optionally, the `test` option can be specified in the `-profile` parameter. If test is not specified, parameters are read from the nextflow.config file. The test params should remain the same for testing purposes.

See more about our custom built-in profiles in [Using specific profiles](submission_guide.md#using-specific-profiles).

## Perform a Dry Run:

For any workflow, you can add `--dry_run true` to run through all the steps but not actually upload files to NCBI's server.  This option produces a few submission log files you can read to check which folders will be uploaded and where they will be uploaded on the host server.

## Submitting to BioSample and/or SRA:

Use the `--workflow biosample_and_sra` workflow option to submit to BioSample and SRA.  Turn off SRA submission by specifying `--sra false`.  Turn off BioSample submission using `--biosample false`

Note: The column `ncbi-spuid` in the metadata template is used as the BioSample SPUID, and the column `ncbi-spuid-sra` is used as the SRA SPUID.  These two fields need to be unique for each sample.
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

