# TOSTADAS &#8594; <span style="color:blue"><u>**T**</u></span>oolkit for <span style="color:blue"><u>**O**</u></span>pen <span style="color:blue"><u>**S**</u></span>equence <span style="color:blue"><u>**T**</u></span>riage, <span style="color:blue"><u>**A**</u></span>nnotation and <span style="color:blue"><u>**DA**</u></span>tabase <span style="color:blue"><u>**S**</u></span>ubmission :dna: :computer:

## PATHOGEN ANNOTATION AND SUBMISSION PIPELINE

<!-- [![GitHub Downloads](https://img.shields.io/github/downloads/CDCgov/tostadas/total.svg?style=social&logo=github&label=Download)](https://github.com/CDCgov/tostadas/releases) -->
[![Nextflow](https://img.shields.io/badge/nextflow%20DSL2-%E2%89%A524.04.0-23aa62.svg?labelColor=000000)](https://www.nextflow.io/) [![run with conda](http://img.shields.io/badge/run%20with-conda-3EB049?labelColor=000000&logo=anaconda)](https://docs.conda.io/en/latest/) [![run with docker](https://img.shields.io/badge/run%20with-docker-0db7ed?labelColor=000000&logo=docker)](https://www.docker.com/) [![run with singularity](https://img.shields.io/badge/run%20with-singularity-1d355c.svg?labelColor=000000)](https://sylabs.io/docs/)

For the complete TOSTADAS documentation, please see the [Complete Documentation](https://cdcgov.github.io/tostadas/)

## Warnings
### Plugin Compatibility Warning
❗ Important Note: This pipeline uses the nf-schema plugin to validate pipeline parameters. Users with Nextflow version 24 or later may encounter a warning message indicating that the plugin must be installed. To resolve this warning message, please install the plugin manually by following the instructions found in this [link](https://www.nextflow.io/docs/latest/plugins.html#offline-usage)

## Overview
**T O S T A D A S**
**T**oolkit for **O**pen **S**equence **T**riage, **A**nnotation, and **DA**tabase **S**ubmission

A portable, open-source pipeline designed to streamline submission of pathogen genomic data to public repositories.  Reducing barriers to timely data submission increases the value of public repositories for both public health decision making and scientific research. TOSTADAS facilitates routine sequence submission by standardizing and automating:

+ Metadata Validation
+ Genome Annotation
+ File submission

TOSTADAS is designed to be flexible, modular, and pathogen agnostic, allowing users to customize their submission of raw read data, assembled genomes, or both. The current release has been tested with sequence data from Poxviruses, Measles, RSV, and select bacteria. Testing for additional pathogens is planned for future releases.

## Installation and Quick Start
❗ Note: If you are a CDC user, please follow the set-up instructions found here: [CDC User Guide](./docs/user-guide/cdc-user-guide.md)

For non-CDC users, please follow the instructions below.
### 1. Clone the repository to your local machine
```
git clone https://github.com/CDCgov/tostadas.git
```
! Note: If you already have Nextflow installed in your local environment, skip ahead to step 5.
### 2. Install mamba and add it to your PATH

 **2a. Install mamba**

❗ Note: If you have mamba installed in your local environment, skip ahead to step 3 ([Create and activate a conda environment](https://github.com/CDCgov/tostadas/edit/main/README.md#3-create-and-activate-a-conda-environment))
```
curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh
bash Mambaforge-$(uname)-$(uname -m).sh -b -p $HOME/mambaforge
```
 **2b. Add mamba to PATH:**
```
export PATH="$HOME/mambaforge/bin:$PATH"
```
### 3. Install Nextflow using mamba and the bioconda Channel
```
mamba install -c bioconda nextflow
```
### 4. Update the default submissions config file with your NCBI username and password
```
# update this config file (you don't have to use vim)
vim conf/submission_config.yaml
```
### 5. Run the workflow with default parameters and the local run environment:
```
# test command for virus reads
nextflow run main.nf -profile test,mpox,<singularity|docker|conda>
```
The pipeline outputs appear in `results/`

### 6. Start running your own analysis

**Annotate and submit viral reads**
```
nextflow run main.nf -profile virus,<docker|singularity> --workflow biosample_and_sra --submission --annotation --outdir <path/to/output/dir/> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml>
```
Metadata can also be provided as `.csv`, `.tsv`, or `.src` (NCBI source modifier) files. Column names from `.src` files are automatically mapped to TOSTADAS fields (e.g., `SeqId` to `sample_name`, `Collection_date` to `collection_date`). The `Country` field in `USA:State` format is auto-split into separate values.

To avoid listing FASTA paths in the metadata file, use `--fasta_dir` to point to a directory of FASTA files. TOSTADAS matches each `sample_name` to filenames (`.fasta`, `.fa`, `.fna`, `.fas`) in that directory and fills in `fasta_path` automatically. Samples without a matching file are skipped with a warning.

**Annotate and submit bacterial reads**
```
nextflow run main.nf -profile bacteria,<docker|singularity> --workflow biosample_and_sra --submission --annotation --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --download_bakta_db --bakta_db_type <light|full> --outdir <path/to/output/dir/>
```

**Submit to GenBank**

GenBank submission requires a modified metadata file that includes the GenBank accession ID. This file will be generated as an output of the biosample and SRA workflow and can be found in the results directory, for example: results/mpxv_test_metadata/final_submission_outputs/mpxv_test_metadata_updated.xlsx.

To submit reads to GenBank, use the following command:

```
nextflow run main.nf -profile mpox,<docker|singularity> --workflow genbank --dry_run false --submission_config <path/to/submission_config.yaml> --updated_meta_path <path/to/updated/metadata/file>
```

To generate SQN files for GenBank without BioSample/SRA submission, add `--genbank_only` to skip BioSample/SRA-specific validation (ncbi-spuid, authors, isolation_source checks).

If you already have a `.sbt` template file from NCBI's template tool, pass it with `--sbt <path/to/template.sbt>` to use it directly for table2asn instead of generating one from submission_config.yaml.

**Annotate and submit measles reads to GenBank**

Measles uses VADR for annotation. Use the `measles` profile to load the appropriate VADR models and configuration:
```
nextflow run main.nf -profile measles,<docker|singularity> --workflow genbank --updated_meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml>
```

Refer to the github pages website for more information on input parameters and use cases.

**Retrieve accession IDs**

To fetch and parse report.xml files from a previous submission, use the following command:

```
nextflow run main.nf -profile mpox,<docker|singularity> --workflow fetch_accessions --dry_run false --submission_config <path/to/submission_config.yaml> --meta_path assets/sample_metadata/mpxv_test_metadata.xlsx
```

**Submit updates to a BioSample submission**

NCBI allows UI-less updating of BioSample submissions, and TOSTADAS can do this using the `--workflow update_submission` workflow option.

To submit updated metadata to biosample, use the following command:

```
nextflow run main.nf -profile mpox,<docker|singularity> --workflow update_submission --dry_run false --submission_config <path/to/submission_config.yaml> --original_submission_outdir <results/mpxv_test_metadata/submission_outputs> --meta_path <path/to/updated/metadata/file>
```

Please make sure your updated metadata Excel file has a `biosample_accession` column that contains accurate accession IDs.  TOSTADAS does not check these for accuracy.  Please make sure they are correct.

Note: TOSTADAS uses the `ncbi-spuid` field to match samples in the metadata file and the original submission.xml.  The `sample_name` field is not preserved in the submission.xml, so it cannot be used as an identifier for this workflow.

### 7. Custom metadata validation and custom BioSample package

TOSTADAS defaults to Pathogen.cl.1.0 (Pathogen: clinical or host-associated; version 1.0) NCBI BioSample package for submissions to the BioSample repository. You can submit using a different BioSample package by doing the following:
1. Change the package name in the `conf/submission_config.yaml`. Choose one of the available [NCBI BioSample packages](https://www.ncbi.nlm.nih.gov/biosample/docs/packages/).
2. Add the necessary fields for your BioSample package to your input Excel file.
3. Add those fields as keys to the JSON file (`assets/custom_meta_fields/example_custom_fields.json`) and provide key info as needed.
    replace_empty_with: TOSTADAS will replace any empty cells with this value (Example application: NCBI expects some value for any mandatory field, so if empty you may want to change it to "Not Provided".)
    new_field_name: TOSTADAS will replace the field name in your metadata Excel file with this value. (Example application: you get weekly metadata Excel files and they specify 'animal_environment' but NCBI expects 'animal_env'; you can specify this once in the JSON file and it will changed on every run.)

**Submit to a custom BioSample package**
```
nextflow run main.nf -profile virus,<docker|singularity> --workflow biosample_and_sra --submission --annotation --sra true --outdir <path/to/output/dir/> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml> --custom_fields_file  <path/to/metadata_custom_fields.json> --validate_custom_fields
```

### Available Profiles

Organism and program profiles are combined with a container profile when running the pipeline. For example: `-profile mpox,docker` or `-profile test,virus,singularity`.

| Profile    | Type     | Description                                        |
|------------|----------|----------------------------------------------------|
| `test`     | Test     | Runs a small test dataset to verify installation   |
| `mpox`     | Organism | Mpox virus configuration                           |
| `rsv`      | Organism | Respiratory syncytial virus configuration          |
| `measles`  | Organism | Measles virus configuration (uses VADR annotation) |
| `bacteria` | Organism | Bacterial genome configuration (uses Bakta)        |
| `virus`    | Organism | General virus configuration                        |
| `nwss`     | Program  | National Wastewater Surveillance System config     |
| `pulsenet` | Program  | PulseNet configuration                             |
| `docker`   | Container | Run with Docker                                   |
| `singularity` | Container | Run with Singularity                          |
| `conda`    | Container | Run with Conda/Mamba                              |

### Workflow Parameters Overview

This section outlines the primary parameters available for configuring and running the TOSTADAS pipeline effectively, allowing users to tailor the workflow for their needs:

| Parameter                    | Description                                                                                       | Input Required           |
|------------------------------|---------------------------------------------------------------------------------------------------|--------------------------|
| `--workflow`                 | Workflow to execute: `biosample_and_sra`, `genbank`, `fetch_accessions`, `update_submission`, `full_submission` | Yes (string) |
| `--annotation`               | Toggle for running annotation                                                                     | Yes (true/false as bool) |
| `--submission`               | Toggle for running submission                                                                     | Yes (true/false as bool) |
| `--meta_path`                | Path to metadata file (.xlsx, .csv, .tsv, or .src)                                                | Yes (path)               |
| `--fasta_dir`                | Directory of FASTA files; auto-populates `fasta_path` by matching `sample_name` to filenames      | No (path)                |
| `--genbank_only`             | Skip BioSample/SRA-specific validation; use when generating SQN files for GenBank only            | No (true/false as bool)  |
| `--sbt`                      | Path to an existing .sbt template file for table2asn (bypasses auto-generation)                   | No (path)                |
| `--updated_meta_path`        | Path to accession-augmented metadata file (required for genbank workflow)                          | Yes (path)               |
| `--outdir`                   | Output directory                                                                                  | No (default: `results`)  |
| `--organism_type`            | Organism type: `virus`, `bacteria`, `eukaryote`                                                   | No (set by profile)      |
| `--virus_subtype`            | Virus subtype: `mpxv`, `rsv`, `mev`                                                              | No (set by profile)      |
| `--submission_config`        | Path to NCBI credentials config (submission_config.yaml)                                          | Yes (path)               |
| `--dry_run`                  | Log what would be submitted without connecting to NCBI                                            | No (true/false as bool)  |
| `--batch_size`               | Number of samples per submission batch                                                            | No (default: 5)          |

#### Workflow Options

The following workflows are available for the `--workflow` parameter:

- **biosample_and_sra**: Runs a submission to BioSample and SRA.
- **genbank**: Runs a GenBank submission.
- **fetch_accessions**: Fetches reports and updates the metadata file.
- **update_submission**: Updates data for existing BioSample or SRA records.
- **full_submission**: Executes BioSample and SRA submissions, waits 30 seconds multiplied by `params.batch_size`, fetches reports, updates the metadata file with accession IDs, and then performs the GenBank submission.

**Note**: The GenBank submission cannot complete without a BioSample accession ID.

For more detailed information on each parameter and additional configurations, please refer to the [TOSTADAS documentation](https://cdcgov.github.io/tostadas/).

## Troubleshooting

For common issues and solutions, see the [Troubleshooting Guide](https://cdcgov.github.io/tostadas/user-guide/troubleshooting/).

## Get in Touch
If you need to report a bug, suggest new features, or just say "thanks", [open an issue](https://github.com/CDCgov/tostadas/issues/new/choose) and we'll try to get back to you as soon as possible!

## Acknowledgements
### Contributors
Josh Forstedt | Jessica Rowell | Kyle O'Connell | Yesh Kulasekarapandian | Ankush Gupta | Cole Tindall | Ramiya Sivakumar | Swarnali Louha | Michael Desch | Ethan Hetrick | Nick Johnson | Kristen Knipe | Shatavia Morrison | Yuanyuan Wang | Michael Weigand | Dhwani Batra | Jason Caravas | Lynsey Kovar | Hunter Seabolt | Crystal Gigante | Christina Hutson | Brent Jenkins | Yu Li | Ana Litvintseva | Matt Mauldin | Dakota Howard | Ben Rambo-Martin | James Heuser | Justin Lee | Mili Sheth

### Tools
The submission portion of this pipeline was adapted from SeqSender. To find more information on this tool, please refer to their GitHub page: [SeqSender](https://github.com/CDCgov/seqsender)

## Resources

:link: NCBI Submission Guidelines: https://submit.ncbi.nlm.nih.gov/

:link: SeqSender Documentation: https://github.com/CDCgov/seqsender

:link: Liftoff Documentation: https://github.com/agshumate/Liftoff

:link: VADR Documentation:  https://github.com/ncbi/vadr.git

:link: VADR MeV Models (Greninger Lab):  https://github.com/greninger-lab/vadr-models-mev

:link: Bakta Documentation:  https://github.com/oschwengers/bakta

:link: RepeatMasker Documentation: https://www.repeatmasker.org/

---

## Public Domain Standard Notice

This repository constitutes a work of the United States Government and is not
subject to domestic copyright protection under 17 USC § 105. This repository
is in the public domain within the United States, and copyright and related
rights in the work worldwide are waived through the
[CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
All contributions to this repository will be released under the CC0 dedication.
By submitting a pull request you are agreeing to comply with this waiver of
copyright interest.

## License Standard Notice

The repository utilizes code licensed under the terms of the Apache Software
License and therefore is licensed under ASL v2 or later.

This source code in this repository is free: you can redistribute it and/or
modify it under the terms of the Apache Software License version 2, or (at
your option) any later version.

This source code in this repository is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the Apache Software
License for more details.

You should have received a copy of the Apache Software License along with this
program. If not, see https://www.apache.org/licenses/LICENSE-2.0.html.

The source code forked from other open source projects will inherit its license.

## Privacy Standard Notice

This repository contains only non-sensitive, publicly available data and
information. All material and community participation is covered by the
[Disclaimer](DISCLAIMER.md) and [Code of Conduct](code-of-conduct.md). For
more information about CDC's privacy policy, please visit
https://www.cdc.gov/other/privacy.html.

## Contributing Standard Notice

Anyone is encouraged to contribute to the repository by
[forking](https://help.github.com/articles/fork-a-repo) and submitting a pull
request. (If you are new to GitHub, you might start with a
[basic tutorial](https://help.github.com/articles/set-up-git).) By contributing
to this project, you grant a world-wide, royalty-free, perpetual, irrevocable,
non-exclusive, transferable license to all users under the terms of the
[Apache Software License v2](https://www.apache.org/licenses/LICENSE-2.0.html)
or later.

All comments, messages, pull requests, and other submissions received through
CDC including this GitHub page may be subject to applicable federal law,
including but not limited to the Federal Records Act, and may be archived. Learn
more at https://www.cdc.gov/other/privacy.html.

## Records Management Standard Notice

This repository is not a source of government records but is a copy to increase
collaboration and collaborative potential. All government records will be
published through the [CDC web site](https://www.cdc.gov).

## Additional Standard Notices

Please refer to [CDC's Template Repository](https://github.com/CDCgov/template)
for more information about [contributing to this repository](https://github.com/CDCgov/template/blob/master/CONTRIBUTING.md),
[public domain notices and disclaimers](https://github.com/CDCgov/template/blob/master/DISCLAIMER.md),
and [code of conduct](https://github.com/CDCgov/template/blob/master/code-of-conduct.md).

## SHARE IT Act Compliance

The [SHARE IT Act](https://github.com/CDCgov/ShareIT-Act) is a federal law
that requires government agencies like CDC to be more transparent about the
software built using federal funds.

**Organization:** CDC/NCEZID/OAMD
**Contact email:** ncezid_shareit@cdc.gov

TOSTADAS (Toolkit for Open Sequence Triage, Annotation and DAtabase Submission)
is a Nextflow pipeline for pathogen genomic data validation, annotation, and
submission to NCBI public databases (BioSample, SRA, GenBank). It supports
multiple organism types including viruses (measles, RSV, mpox), bacteria, and
eukaryotes with automated metadata validation, VADR/Bakta/RepeatMasker
annotation, and FTP-based submission.
