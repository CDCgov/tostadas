# Quick Start

## Steps
(1) Check that you are in the directory where the TOSTADAS repository was installed by running `pwd`
Expected Output:

* `/path/to/working/directory/tostadas`
This is the default directory set in  nextflow.config for the provided test input files.

(2) Change the submission_config parameter within `test_params.config` or `nextflow.config` (if running with your own data) to the location of your personal submission config file. Note that we provide a virus and bacterial test config depending on the use case.
❗ You must have your personal submission configuration file set up before running the default parameters for the pipeline and/or if you plan on using sample submission at all. More information on setting this up can be found here: More Information on Submission

(3) Pipeline Execution Examples
We describe a few use-cases of the pipeline below. For more information on input parameters, refer to the documentation found in the following pages:

## Profile Options and Input Files
### Parameters
❗ Note: For all use cases, the paths to the required files should be specified in the nextflow.config file or the params.yaml file.

#### Use Case 1: Running Annotation and Submission
1. Annotate viral assemblies and submit to GenBank and SRA

Required files: fasta files, metadata file

* `nextflow run main.nf -profile <singularity/docker/conda> --virus --genbank --sra --submission_wait_time 5`
##### Breakdown:

`-profile:`
This parameter is required. Specify the profile and run-time environment (`singularity`, `docker` or `conda`). Conda implementation is less stable, `singularity` or `docker` is recommended.
`--virus:`
The pathogen type is specified as `virus`
`--sra:`
`sra` is specified as the database to submit to
`--submission_wait_time`:
This parameter is optional. Running the pipeline with default parameters will trigger a wait time equal to # of samples * 180 seconds. This default parameter can be overridden by supplying an integer value to the `submission_wait_time` parameter.
`--genbank`:
`genbank` is specified as the database to submit to
❗ Pre-requisite to submit to GenBank: In order to submit to GenBank, the program table2asn must be executable in your local environment. Copy the program table2asn to you tostadas/bin directory by running the following lines of code:

* `cd ./tostadas/bin/`
* `wget https://ftp.ncbi.nlm.nih.gov/asn1-converters/by_program/table2asn/linux64.table2asn.gz`
* `gunzip linux64.table2asn.gz`
* `mv linux64.table2asn table2asn`

2. Annotate bacterial assemblies and submit to GenBank and SRA **

Required files: fasta files, metadata file

(A) Download BAKTA Database

* `nextflow run main.nf -profile <singularity/docker/conda> --bacteria --genbank --sra --submission_wait_time 5 --download_bakta_db --bakta_db_type <light/full>`
(B) Provide path to existing BAKTA Database

* `nextflow run main.nf -profile <singularity/docker/conda> --bacteria --genbank --sra --submission_wait_time 5 --bakta_db_path`

Breakdown:

`--bacteria`:
The pathogen type is specified as `bacteria`
`--genbank`:
`genbank` is specified as the database to submit to