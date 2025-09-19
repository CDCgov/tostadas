# CDC User Guide

## Environment Setup

### (1) Clone the repository to your local machine:

`git clone https://github.com/CDCgov/tostadas.git` `cd tostadas`

### (2) Load the Nextflow module:

Initialize the nextflow module by running the following command:

`ml nextflow`

### (3) Ensure that Nextflow is available by running nextflow -v

Expected Output:

`nextflow version <CURRENT VERSION>`

### (4) Update the default submissions config file with your NCBI username and password, and run one of the following nextflow commands to execute the scripts with default parameters and the local run environment:

See [Run a test submission](installation.md#run-a-test-submission).