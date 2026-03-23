# NWSS Sequence Submission User Guide

## Overview

This workflow uses Nextflow to automate submission of FASTQ read files to NCBI's SRA database. It includes three steps:

- **Metadata validation** -- Check that your Excel data conforms to NCBI expectations
- **Biosample submission** -- Submit each sample to Biosample database and return Biosample ID
- **SRA submission** -- Submit each FASTQ file to SRA database and return an Accession ID

!!! tip
    The Singularity or Docker profile is recommended if possible. Use Conda only when containers are not an option.

## Prerequisites

- [Review Nextflow Getting Started](https://www.nextflow.io/docs/latest/) if you have never used Nextflow before
- [Install Nextflow](https://www.nextflow.io/docs/latest/install.html)
- Clone the TOSTADAS GitHub repository:

    ```bash
    git clone https://github.com/CDCgov/tostadas.git
    ```

- Register for an [NCBI Center Account](general_NCBI_submission_guide.md#ncbi-center-account)
- [Create an NCBI Bioproject](https://www.protocols.io/view/ncbi-submission-protocol-for-sars-cov-2-wastewater-ewov14w27vr2/v7?version_warning=no&step=3). Link to the NWSS umbrella Bioproject (PRJNA747181).

## Prepare Metadata

Download the Excel [template for wastewater metadata](https://github.com/CDCgov/tostadas/raw/main/assets/sample_metadata/wastewater_biosample_template.xlsx) and fill out following the examples in the sheet. Rename your file.

## Configure Submission Settings

Add your center information to this [configuration file](https://github.com/CDCgov/tostadas/raw/main/conf/submission_config.yaml). Make sure for Biosample package you enter `SARS-CoV-2.wwsurv.1.0`. Rename the file as needed, but make sure you keep it in the `conf/` directory.

## Test with the Test Profile

Run the following command to test your setup:

```bash
nextflow run main.nf -profile nwss,test,<docker|singularity|conda>
```

## Test with Real Data

Add a few of your actual samples to the Excel metadata sheet and submit these to the test server. NCBI provides a test server to validate the ftp connection before submitting to production.

```bash
nextflow run main.nf -profile nwss,<docker|singularity|conda> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --outdir <path/to/outdir> --dry_run false
```

## Submit a Small Batch to Production

```bash
nextflow run main.nf -profile nwss,<docker|singularity|conda> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --outdir <path/to/outdir> --prod_submission true --dry_run false
```

## Submit All Samples to Production

Update your metadata path to point to all of your samples for submissions:

```bash
nextflow run main.nf -profile nwss,<docker|singularity|conda> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --outdir <path/to/outdir> --prod_submission true --dry_run false
```

## Troubleshooting

View [the docs](troubleshooting.md)
