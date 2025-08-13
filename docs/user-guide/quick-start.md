# Quick Start

## Validate Environment

### (1) Check that you are in the directory where the TOSTADAS repository was installed by running `pwd`

Expected Output:

`/path/to/working/directory/tostadas`

### (2) Change the submission\_config parameter within nextflow.config to the location of your personal submission config file.

Bacterial and viral submission configurations are provided in the repo for testing purposes, but you will not be able to perform a submission without providing a personal submission configuration.

More information on running the submission sub-workflow can be found here: [More Information on Submission](../user-guide/submission_config_guide.md)

## Pipeline Execution Examples

We describe a few use-cases of the pipeline below. For more information on input parameters, refer to the documentation found in the following pages:

*   [Profile Options and Input Files](../user-guide/profile.md)
*   [Parameters](../user-guide/parameters.md)

❗ The paths to the required files must be specified in the nextflow.config file or the params.yaml file.

## Basic Usage:

Before we dive into the more complex use-cases of the pipeline, let's look at the most basic way the pipeline can be run:

`nextflow run main.nf -profile <test(optional)>,<singularity|docker|conda> --<virus|bacteria>` `-profile <test(optional)>,<singularity|docker|conda>` Specify the run-time environment (singularity, docker or conda). The conda implementation is less stable so using singularity or docker is recommended if available on your system. You may specify the optional `-profile` argument `test` to force the pipeline to ignore the custom configuration found in your nextflow.config file and instead run using a pre-configured test data set and configuration. `--<virus|bacteria>`: The pathogen type must be specified for the pipeline to run.

❗ Important note on arguments: Arguments with a single “-“, such as -profile, are arguments to nextflow. Arguments with a double “--“, such as --virus or –-bacteria are arguments to the TOSTADAS pipeline.

Example:

`nextflow run main.nf -profile test,singularity --virus`

### Breakdown:

*   `-profile test,singularity`
    *   Set compute environment to singularity
    *   Run with test configuration
*   \--virus
    *   Viral sample Overriding parameters through the command line: Any parameter defined in nexflow.config can be overridden at runtime by providing the parameter as a command line argument with the “--” prefix.

### Example: Modifying the output directory

By default, the pipeline will create and store pipeline outputs in the test\_output directory. You can modify the location output files are stored by adding the `--outdir` flag to the command line and providing the new path as a string.

`nextflow run main.nf -profile test,singularity –-virus --outdir </path/to/output/dir>`

### Running Annotation and Submission

#### (1) Annotate viral assemblies and submit them to GenBank and SRA

Database targets are specified at run time. You can specify more than one target by adding additional arguments to the command line.

`nextflow run main.nf -profile singularity --virus --annotation --submission --genbank --sra --meta_path </path/to/meta_data/file> –-fastq_path </path/to/fastq/file/directory> --fasta_path </path/to/fasta/file/directory>`

##### Breakdown:

*   `-profile singularity`
    *   Set compute environment to singularity
*   `--virus`
    *   Viral sample
*   `--sra`
    *   Prepare an SRA submission
*   `--genbank`
    *   Prepare a GenBank submission
*   `--annotation`
    *   Run annotation
*   `--submission`
    *   Run submission
*   `--fasta_path`
    *   Provide path to directory containing your fasta files
*   `--fastq_path`
    *   Provide path to directory containing your fastq files
*   `--meta_path`
    *   Provide path to your meta-data file

#### (2) Annotate bacterial assemblies and submit to GenBank and SRA

❗ Note – If you don’t have the BAKTA database, run with the `--download_bakta_db true` flag or download from it from this [Link](https://zenodo.org/records/10522951). If you do have the database, skip ahead to (B).

#### (A) Download Bakta database

`nextflow run main.nf -profile singularity --bacteria --genbank --sra --download_bakta_db true --bakta_db_type <light|full> --submission –annotation --meta_path /path/to/meta_data/file –fastq_path /path/to/fastq/file/directory --fasta_path /path/to/fasta/file/directory`

#### (B) Provide path to existing Bakta database

`nextflow run main.nf -profile singularity –-bacteria ––annotation --submission -–genbank --sra --bakta_db_path <path/to/bakta/db> --meta_path </path/to/meta_data/file> --fastq_path </path/to/fastq/file/directory> --fasta_path </path/to/fasta/file/directory>`

##### Breakdown:

*   `--bacteria`
    *   Bacterial sample
*   `--download_bakta_db true`
    *   Download or refresh the Bakta database
*   `--bakta_db_type <light|full>`
    *   Choose between the faster, lighter-weight light Bakta database or the larger and slower, but more accurate, full Bakta database
*   `--bakta_db_path </path/to/bakta/db>`
    *   The path to the Bakta database

##### Use Case 2: Running Submission only without Annotation

❗ Note: you can only submit raw files to SRA, not to Genbank.

#### (1) Submit fastqs to SRA

`nextflow run main.nf -profile singularity --virus --annotation false --sra –submission --meta_path </path/to/meta_data/file> --fastq_path </path/to/fastq/file/directory>` `--annotation false` Disable annotation
