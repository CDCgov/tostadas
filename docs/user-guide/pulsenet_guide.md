# PulseNet Submission Guide

## Overview

[PulseNet](https://www.cdc.gov/pulsenet/) is a national laboratory network coordinated by CDC that connects foodborne illness cases to detect outbreaks. PulseNet laboratories perform whole-genome sequencing (WGS) of foodborne, waterborne, and One Health enteric pathogens such as *Salmonella*, *Listeria monocytogenes*, *Escherichia coli*, and *Campylobacter*. Sequence data from PulseNet submissions are deposited in NCBI databases under the **OneHealthEnteric.1.0** BioSample package.

TOSTADAS provides a built-in `pulsenet` profile that preconfigures the pipeline for OneHealthEnteric.1.0 submissions, including custom field validation and the correct metadata template.

This guide walks through the steps to submit bacterial sequence data to NCBI as part of PulseNet surveillance using TOSTADAS.

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
- Create an NCBI BioProject to associate with the submissions

## What the PulseNet Profile Sets

When `-profile pulsenet` is included in the Nextflow command, the following parameters are applied automatically:

| Parameter | Value | Description |
|---|---|---|
| `biosample_pkg` | `onehealth` | Selects the OneHealthEnteric.1.0 BioSample package |
| `workflow` | `biosample_and_sra` | Submits to both BioSample and SRA |
| `meta_path` | `assets/sample_metadata/onehealth_biosample_package_template.xlsx` | Points to the OneHealth metadata template |
| `validate_custom_fields` | `true` | Enables validation of OneHealth-specific fields |
| `custom_fields_file` | `assets/custom_meta_fields/onehealth_biosample_pkg.json` | Specifies the custom field definitions for OneHealth |
| `biosample` | `true` | Enables BioSample submission |
| `sra` | `true` | Enables SRA submission |

!!! note
    The `pulsenet` profile does not set `organism_type` or enable annotation. To run Bakta annotation for bacterial genomes, combine the `pulsenet` profile with the `bacteria` profile or add `--organism_type bacteria --bakta` to the command line.

## Prepare Metadata

Download the Excel [template for OneHealth metadata](https://github.com/CDCgov/tostadas/raw/main/assets/sample_metadata/onehealth_biosample_package_template.xlsx) and fill it out following the examples in the sheet.

### Required fields

TOSTADAS validates the following fields as required for the OneHealthEnteric.1.0 BioSample package:

| Field | Description |
|---|---|
| `sample_name` | Unique identifier for each sample |
| `strain` | Strain name or identifier for the isolate |

### Custom fields validated by the PulseNet profile

The `pulsenet` profile enables validation of the following additional fields through its custom fields JSON (`assets/custom_meta_fields/onehealth_biosample_pkg.json`):

| Field | Behavior |
|---|---|
| `strain` | Empty values are replaced with "Not Provided" |
| `source_type` | Empty values are replaced with "Not Provided" |
| `animal_environment` | Column is renamed to `animal_env` to match NCBI expectations |

!!! warning
    The OneHealthEnteric.1.0 package defines many additional fields beyond the minimum required set above. Consult the [NCBI OneHealthEnteric.1.0 package specification](https://www.ncbi.nlm.nih.gov/biosample/docs/packages/OneHealthEnteric.1.0/) for the full list of expected attributes. Populate as many fields as possible in the metadata template to ensure submissions pass NCBI server-side validation.

## Configure Submission Settings

Copy the submission configuration template and update it with your organization's information:

```bash
cp conf/submission_config.yaml conf/my_submission_config.yaml
```

Edit the following fields in the configuration file:

```yaml
NCBI_username: "<your_ncbi_username>"
NCBI_password: "<your_ncbi_password>"
NCBI_ftp_host: "ftp-private.ncbi.nlm.nih.gov"
NCBI_sftp_host: "sftp-private.ncbi.nlm.nih.gov"
BioSample_package: "OneHealthEnteric.1.0"
NCBI_Namespace: "<your_namespace>"
Org_ID: "<your_org_id>"
Submitting_Org: "<your_organization>"
Street: "<your_street_address>"
City: "<your_city>"
State: "<your_state>"
Postal_code: "<your_postal_code>"
Country: "<your_country>"
Email: "<your_email>"
Submitter:
  '@email': "<your_email>"
  '@alt_email': "<alternate_email>"
  Name:
    First: "<first_name>"
    Last: "<last_name>"
```

!!! warning
    Set the `BioSample_package` field to `OneHealthEnteric.1.0`. This value must match the package expected by NCBI for PulseNet submissions.

## Test with the Test Profile

Run the following command to verify that the pipeline configuration is correct. The `test` profile prepares submission files without uploading them:

```bash
nextflow run main.nf \
    -profile pulsenet,test,<docker|singularity|conda>
```

## Test with Real Data

Add a few actual samples to the metadata file and submit to the NCBI test server. NCBI provides a test server to validate the FTP connection before submitting to production:

```bash
nextflow run main.nf \
    -profile pulsenet,<docker|singularity|conda> \
    --meta_path <path/to/metadata_file.xlsx> \
    --submission_config <path/to/submission_config.yaml> \
    --outdir <path/to/outdir> \
    --dry_run false
```

## Submit to Production

When testing is complete, add `--prod_submission` to submit to the NCBI production server:

```bash
nextflow run main.nf \
    -profile pulsenet,<docker|singularity|conda> \
    --meta_path <path/to/metadata_file.xlsx> \
    --submission_config <path/to/submission_config.yaml> \
    --outdir <path/to/outdir> \
    --prod_submission true \
    --dry_run false
```

!!! tip
    Use `--batch_size 50` to submit samples in groups of 50. NCBI recommends batch submissions over individual sample submissions.

## Running with Bakta Annotation

To annotate bacterial genomes with Bakta and submit to GenBank in addition to BioSample and SRA, combine the `pulsenet` and `bacteria` profiles:

```bash
nextflow run main.nf \
    -profile pulsenet,bacteria,<docker|singularity|conda> \
    --workflow full_submission \
    --meta_path <path/to/metadata_file.xlsx> \
    --submission_config <path/to/submission_config.yaml> \
    --outdir <path/to/outdir> \
    --download_bakta_db \
    --bakta_db_type light \
    --prod_submission true \
    --dry_run false
```

The `bacteria` profile sets `organism_type` to `bacteria` and enables Bakta annotation. When combined with `pulsenet`, the pipeline will:

1. Validate metadata against the OneHealthEnteric.1.0 package requirements
2. Submit samples to BioSample and SRA
3. Annotate assemblies using Bakta
4. Submit annotated assemblies to GenBank via the WGS pathway

!!! note
    The `full_submission` workflow handles the ordering automatically: it submits to BioSample and SRA first, polls for accession IDs, then performs the GenBank submission. If running workflows individually, submit BioSample first, fetch accessions, then run the `genbank` workflow.

## Expected Output

After a successful run, the following output directories are created under the specified `--outdir`:

| Directory | Contents |
|---|---|
| `submission/` | Submission XML files organized by batch (e.g., `batch_1/`, `batch_2/`) |
| `accessions/` | Updated metadata file with BioSample and SRA accession IDs appended |
| `validation/` | Validated and cleaned metadata files |
| `annotation/` | Bakta annotation output (when annotation is enabled) |

The updated metadata file in `accessions/` contains the original metadata with `biosample_accession` and `sra_accession` columns populated after NCBI processes the submission.

## Troubleshooting

View [the troubleshooting docs](troubleshooting.md) for common issues and solutions.
