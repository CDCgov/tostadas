# NWSS Sequence Submission User Guide

### Overview
This workflow uses Nextflow to automate submission of FASTQ read files to NCBI's SRA database. It includes three steps. 
+ Metadata validation: Check that your Excel data conforms to NCBI expectations
+ Biosample submission: Submit each sample to Biosample database and return Biosample ID
+ SRA submission: Submit each FASTQ file to SRA database and return an Accession ID

***We recommend that you use the singularity or docker profile if possible, and only use conda when containers are not an option.***

### 1. Prerequisites

+ [Review Nextflow Getting Started](https://www.nextflow.io/docs/latest/) if you have never used Nextflow before
+ [Install Nextflow](https://www.nextflow.io/docs/latest/install.html)
+ Clone the TOSTADAS GitHub repository: `git clone https://github.com/CDCgov/tostadas.git`
+ Register for an [NCBI Center Account](https://cdcgov.github.io/tostadas/user-guide/general_NCBI_submission_guide/#ncbi-center-account)
+ [Create an NCBI Bioproject](https://www.protocols.io/view/ncbi-submission-protocol-for-sars-cov-2-wastewater-ewov14w27vr2/v7?version_warning=no&step=3). Link to the NWSS umbrella Bioproject (PRJNA747181).

### 2. Fill out Metadata for all samples

Download the Excel [template for wastewater metadata](https://github.com/CDCgov/tostadas/raw/master/assets/sample_metadata/wastewater_biosample_template.xlsx) and fill out following the examples in the sheet. Rename your file.

### 3. Fill out the submission config file
Add your center information to this [configuration file](https://github.com/CDCgov/tostadas/raw/master/conf/submission_config.yaml). Make sure for Biosample package you enter `SARS-CoV-2.wwsurv.1.0`. Rename the file as needed, but make sure you keep it in the conf/ directory.

### 4. Test your set up with the test profile
Run the following command to test your setup
`nextflow run main.nf -profile nwss,test,[docker,singularity,conda]`

### 5. Run a test with real data
Add a few of your actual samples to the Excel metadata sheet and submit these to the test server. NCBI provides a test server to validate the sftp connection before submitting to production. 

`nextflow run main.nf -profile nwss,<docker|singularity|conda> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --outdir <path/to/outdir>`

### 6. Submit small sample to production server

`nextflow run main.nf -profile nwss,<docker|singularity|conda> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --outdir <path/to/outdir> --prod_submission true`

### 7. Submit all samples to production server
Update your metadata path to point to all of your samples for submissions
`nextflow run main.nf -profile nwss,<docker|singularity|conda> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --outdir <path/to/outdir> --prod_submission true`

### 8. Troubleshooting
View [the docs](https://cdcgov.github.io/tostadas/user-guide/quick-start/#troubleshooting)
