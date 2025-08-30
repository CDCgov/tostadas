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

## Warnings
### Plugin Compatibility Warning
❗ Important Note: This pipeline uses the nf-schema plugin to validate pipeline parameters. Users with Nextflow version 24 or later may encounter a warning message indicating that the plugin must be installed. To resolve this warning message, please install the plugin manually by following the instructions found in this [link](https://www.nextflow.io/docs/latest/plugins.html#offline-usage)

## Basic Usage:

Before we dive into the more complex use-cases of the pipeline, let's look at the most basic way the pipeline can be run:

`nextflow run main.nf -profile <test(optional)>,<singularity|docker|conda> --species <virus|bacteria|eukaryote|mpxv|rsv>` 

`-profile <test(optional)>,<singularity|docker|conda>` Specify the run-time environment (singularity, docker or conda). The conda implementation is less stable so using singularity or docker is recommended if available on your system. You may specify the optional `-profile` argument `test` to force the pipeline to ignore the custom configuration found in your nextflow.config file and instead run using a pre-configured test data set and configuration. `--species <virus|bacteria>`: The pathogen type must be specified for the pipeline to run. For submission, the species type determines the GenBank workflow (`<virus|bacteria|eukaryote>`).  For annotation, species type determines the annotation tool reference files. For example, `--species mpxv` will use the mpxv repeats library for annotation and the virus workflow for GenBank submission.

❗ Important note on arguments: Arguments with a single “-“, such as -profile, are arguments to nextflow. Arguments with a double “--“, such as --species virus or –-species bacteria are arguments to the TOSTADAS pipeline.

### Breakdown:

*   `-profile test,singularity`
    *   Set compute environment to singularity
    *   Run with test configuration
*   \--species virus
    *   Viral sample Overriding parameters through the command line: Any parameter defined in nexflow.config can be overridden at runtime by providing the parameter as a command line argument with the “--” prefix.

### Example: Modifying the output directory

By default, the pipeline will create and store pipeline outputs in the test\_output directory. You can modify the location output files are stored by adding the `--outdir` flag to the command line and providing the new path as a string.

`nextflow run main.nf -profile test,singularity –-species virus --outdir </path/to/output/dir>`

### Running Annotation and Submission

#### (1) Annotate viral assemblies and submit them to GenBank and SRA

Database targets are specified at run time. You can specify more than one target by adding additional arguments to the command line.

`nextflow run main.nf -profile singularity --species virus --annotation --submission --genbank --sra --meta_path </path/to/meta_data/file>`

##### Breakdown:

*   `-profile singularity`
    *   Set compute environment to singularity
*   `--species virus`
    *   Viral sample
*   `--sra`
    *   Prepare an SRA submission
*   `--genbank`
    *   Prepare a GenBank submission
*   `--annotation`
    *   Run annotation
*   `--submission`
    *   Run submission
*   `--meta_path`
    *   Provide path to your meta-data file

#### (2) Annotate bacterial assemblies and submit to GenBank and SRA

❗ Note – If you don’t have the BAKTA database, run with the `--download_bakta_db true` flag or download from it from this [Link](https://zenodo.org/records/10522951). If you do have the database, skip ahead to (B).

#### (A) Download Bakta database

`nextflow run main.nf -profile singularity --species bacteria --genbank --sra --download_bakta_db true --bakta_db_type <light|full> --submission –annotation --meta_path /path/to/meta_data/file`

#### (B) Provide path to existing Bakta database

`nextflow run main.nf -profile singularity –-species bacteria ––annotation --submission -–genbank --sra --bakta_db_path <path/to/bakta/db> --meta_path </path/to/meta_data/file>`

##### Breakdown:

*   `--species bacteria`
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

`nextflow run main.nf -profile singularity --species virus --annotation false --sra –submission --meta_path </path/to/meta_data/file>` 

`--annotation false`: Disable annotation

❗ Note: this also submits to BioSample, by default.

## Troubleshooting

If you encounter issues while using the TOSTADAS pipeline, refer to the following troubleshooting steps to resolve common problems:

### Common Issues and Solutions

#### 1. Errors with 'table2asn not on PATH' or a Python library missing when using the `singularity` or `docker` profiles

**Issue:** Nextflow is using an outdated cached image.

**Solution:** Locate the image (e.g., `$HOME/.singularity/staphb-tostadas-latest.img`) and delete it. This will force Nextflow to pull the latest version.

#### 2. Pipeline hangs indefinitely during the submission step, or you get a "duplicate BioSeq ID error"  

**Issue:** This may be caused by duplicate sample IDs in the FASTA file (e.g., a multicontig FASTA). This is only a problem for submissions to Genbank using `table2asn`.

**Solution:** Review the sequence headers in the sample FASTA files and ensure that each header is unique.