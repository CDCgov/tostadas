# NWSS Sequence Submission User Guide

### Notes, need to update!!!!!
Use docker / singularity if possible. 
Make sure that the fastq paths in the metadata are reachable.

### 1. Prerequisites
+ [Install Nextflow](https://www.nextflow.io/docs/latest/install.html)
+ Clone the TOSTADAS GitHub repository: `git clone https://github.com/CDCgov/tostadas.git`
+ Register for an [NCBI Center Account](https://cdcgov.github.io/tostadas/user-guide/general_NCBI_submission_guide/#ncbi-center-account)
+ [Create an NCBI Bioproject](https://www.protocols.io/view/ncbi-submission-protocol-for-sars-cov-2-wastewater-ewov14w27vr2/v7?version_warning=no&step=3). Link the to the NWSS umbrella Bioproject (PRJNA747181).

### 2. Fill out Metadata sheet for all samples
Download the Excel [template for wastewater metadata](/assets/sample_metadata/wastewater_biosample_template.xlsx) and fill out following the examples in the sheet. 

### 3. Fill out the submission config file
Add your center information to this [configuration file](/conf/submission_config.yaml). Rename the file as needed.

### 4. Test your set up with the test profile
Run the following command to test your setup
`nextflow run main.nf -profile ww,test,[docker,singularity,conda]

### 5. Run a test with real data !!! fix test command
Add a few of your actual samples to the Excel metadata sheet and submit these to the test server.
`nextflow run main.nf -profile ww,[docker,singularity,conda] --meta_path [PATH TO YOUR METADATA FILE] --outdir [PATH TO YOUR OUTDIR] --test`

### 6. Submit small sample to Production Server
`nextflow run main.nf -profile ww,[docker,singularity,conda] --meta_path [PATH TO YOUR METADATA FILE] --outdir [PATH TO YOUR OUTDIR] --prod`

### 6. Submit all samples to Production Server
Update your metadata path to point to all of your samples for submissions
`nextflow run main.nf -profile ww,[docker,singularity,conda] --meta_path [PATH TO YOUR METADATA FILE] --outdir [PATH TO YOUR OUTDIR] --prod`

### Troubleshooting

+ The pipeline ended on the Metadata Validation step: Check that your metadata conforms to the example in assets
+ The test submission returned an error about Bioproject. This is ok, the Bioprojects do not live on the test server so you should expect this error. 
+ 