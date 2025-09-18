# Submission Guide 

## Table of Contents
- [Putting together the Nextflow command](#putting-together-the-nextflow-command)
- [Choosing a workflow](#choosing-a-workflow)
- [Choosing an organism type and/or virus subtype](#choosing-an-organism-type-andor-virus-subtype)
- [Using specific profiles](#using-specific-profiles)
- [Other customizations](#other-customizations)
- [Typical example workflow](#typical-example-workflow)
- [Submission config fields](#submission-config-fields)
- [Custom metadata validation and custom BioSample package](#custom-metadata-validation-and-custom-biosample-package)
  - [Built-in BioSample package profiles](#built-in-biosample-package-profiles)

## Putting together the Nextflow command

Your basic command starts like this: `nextflow run main.nf -profile <docker|singularity|conda>` but needs to be confiured further. See below.

## Choosing a workflow

Choose how you want to run TOSTADAS using the `--workflow` parameter:

- **biosample_and_sra**: Runs a submission to BioSample and SRA. Add `--biosample false` or `--sra false` to toggle off submission to one or the other.
- **genbank**: Runs a GenBank submission. This requires an updated metadata file that includes `biosample_accession` as required by NCBI.
- **fetch_accessions**: Fetches reports and updates the metadata file.
- **full_submission**: Executes BioSample and SRA submissions, waits 60 seconds multiplied by `--batch_size`, fetches reports, updates the metadata file with accession IDs, and then performs the GenBank submission.
- **update_submission**: Executes a BioSample submission using an updated metadata Excel file.

## Choosing an organism type and/or virus subtype

If you want to run viral annotation, you need to specify a `--virus_subtype <mpxv|rsv>`.  This tells TOSTADAS which annotator profile to use if you're running VADR.

If you want to run bacterial annotation, you need to specify `--organism_type bacteria`. This tells TOSTADAS to annotate using bakta.  You can instead use a profile (see [Using specific profiles](#using-specific-profiles)).

If you're submitting to GenBank (the only option if you want to run annotation), you need to specify `--organism_type <virus|bacteria|eukaryote>`.  This tells TOSTADAS which kind of GenBank submission to do.
FTP submission to GenBank is only supported for bacteria and eukaryote assemblies.  Virus assemblies must be submitted via email (either using TOSTADAS or manually emailing the files in the results folder).

## Using specific profiles

TOSTADAS supports some profiles to make submission easier.  These are specified in the `-profile` option. See [Custom metadata validation and custom BioSample package](#custom-metadata-validation-and-custom-biosample-package) for more detail.

- **test**: Runs a test submission. It prepares all the files but does not actually submit to the test server. To submit to the test server, add `dry_run false`
- **nwss**: Submits to SARS-CoV-2.wwsurv.1.0 BioSample package.
- **pulsenet**: Submits to OneHealthEnteric.1.0 BioSample package. 
- **virus**: Sets defaults for virus submission (to run a test bacteria submission, use `profile test,virus,<docker|singularity|conda>`)
- **bacteria**: Sets defaults for bacteria submission (to run a test bacteria submission, use `profile test,bacteria,<docker|singularity|conda>`)
- **mpox**: Sets defaults for MPOX submission (to run a test MPOX submission, use `profile test,mpox,<docker|singularity|conda>`)
- **rsv**: Sets defaults for RSV submission (to run a test RSV submission, use `profile test,rsv,<docker|singularity|conda>`)

## Other customizations

All the custom parameters for TOSTADAS are found in nextflow.config and the config files inside `conf/`.  You can override any of these by specifying the parameter on the command line.

For example, the default output directory is `results`, but you can override that and choose your own output directory using `--outdir path/to/my/output` in your command.

Another example: the `--dry_run` flag (which prepares files for submission but doesn't upload to the server) defaults to `true` for the test profile and `false` otherwise, but you can override it by specifying `--dry_run <true|false>` on the command line.



## Typical example workflow

We'll run test submissions to BioSample and SRA using the test MPOX data included in the repository.

Submit to biosample and sra:
`nextflow run main.nf -profile test,singularity,mpox --workflow biosample_and_sra --dry_run false --submission_config conf/submission_config.yaml --batch_size 5`
**Remember** to add credentials to your submission_config.yaml file.

Fetch the accessions if they weren’t assigned (this workflow creates an updated Metadata Excel file with the validated fields and the accession IDs):
`nextflow run main.nf -profile test,singularity,mpox --workflow fetch_accessions --dry_run false --submission_config conf/submission_config.yaml` 

Submit an updated biosample submission (open the updated Excel file from results/mpxv_test_metadata/final_submission_outputs/mpxv_test_metadata_updated.xlsx and add some fake SAMN IDs first):
`nextflow run main.nf -profile test,singularity --workflow update_submission --dry_run false --species mpxv --submission_config conf/submission_config.yaml --batch_size 5 --original_submission_outdir results/mpxv_test_metadata/submission_outputs --meta_path results/mpxv_test_metadata/final_submission_outputs/mpxv_test_metadata_updated.xlsx`
**Remember** This won’t run without those fake SAMN IDs in the biosample_accession field.

Now we'll run a test GenBank submission using the test bacteria data included in the repository.

Submit to BioSample first (because GenBank requires a BioSample accession):
`nextflow run main.nf -profile test,singularity,bacteria --workflow biosample_and_sra --dry_run false --submission_config conf/submission_config.yaml`

Open the updated Excel file from results/bacteria_test_metadata_1/final_submission_outputs/bacteria_test_metadata_1_updated.xlsx and add some fake SAMN IDs first.
**The next command won't run without the fake SAMN IDs in biosample_accession column**.
`nextflow run main.nf -profile test,singularity,bacteria --workflow genbank --dry_run false --submission_config conf/submission_config.yaml --annotation --download_bakta_db --bakta_db_light`

## Submission config fields

The fields and corresponding example values can be found here: [Submission Config](../conf/submission_config.yaml).

| Field Name                    | Description                                             | Input Required   |
|--------------------------|---------------------------------------------------------|------------------|
| NCBI / username         |  Your personal username credential for NCBI                                      |    Yes (string)   |
| NCBI / password         |  Your personal password credential for NCBI                                      |    Yes (string)   |
| NCBI_ftp_host           | The FTP host name for NCBI                                                       |    Yes (string)   |
| NCBI_sftp_host          | The SFTP host name for NCBI                                                      |    Yes (string)   |
| NCBI_API_URL            | URL for the NCBI API                                                             |    Yes (string)   |
| table2asn_email         | Email address for GenBank email submission                                       |    No (string)    |
| BioSample_package       | Name of BioSample package for submission                                         |    Yes (string)   |
| Role                    | Role of person submitting (should be "owner")                                    |    Yes (string)   |
| Type                    | Type of submission (should usually be "institute")                               |    Yes (string)   |
| NCBI_Namespace          |  An SPUID attribute that is unique for each submitter, coordinate this with NCBI |    Yes (string)   |
| Org_ID                  | Organization ID for NCBI                                                         |    Yes (string)   |
| Submitting_Org          | Name of the organization or company you are affiliated with                      |    Yes (string)   |
| Submitting_Org_Dept     | Name of the department with organization or company                              |    No (string)    |
| Street                  | Street address of the organization or company                                    |    Yes (string)   |
| City                    | City of the organization or company                                              |    Yes (string)   |
| State                   | State of the organization or company                                             |    Yes (string)   |
| Postal_Code             | Zip code of the organization or company                                          |    Yes (string)   |
| Country                 | Country of the organization or company                                           |    Yes (string)   |
| Email                   | Submitter's email address                                                        |    Yes (string)   |
| Phone                   | Submitter's phone number                                                         |    No (string)    |
| Specified_Release_Date  | Specify a date to release the samples to the public repository                   |    No (string)    |
| Submitter               | Leave blank                                                                      |    Yes (blank)    |
| '@email'                | Submitter's email address                                                        |    Yes (string)   |
| '@alt_email'            | An alternate email address to also receive NCBI submission notification emails   |    Yes (string)   |
| Name                    | Leave blank                                                                      |    Yes (blank)    |
| First                   | Submitter's first name                                                           |    Yes (string)   |
| Last                    | Submitter's last name                                                            |    Yes (string)   |

## Custom metadata validation and custom BioSample package

TOSTADAS defaults to Pathogen.cl.1.0 (Pathogen: clinical or host-associated; version 1.0) NCBI BioSample package for submissions to the BioSample repository. You can submit using a different BioSample package by doing the following:

1.  Change the package name in the `conf/submission_config.yaml`. Choose one of the available [NCBI BioSample packages](https://www.ncbi.nlm.nih.gov/biosample/docs/packages/).
2.  Add the necessary fields for your BioSample package to your input Excel file.
3.  Add those same fields as keys to the JSON file (`assets/custom_meta_fields/example_custom_fields.json`) and provide key info as needed. This lets TOSTADAS know to validate and submit those added fields.
4.  Tell TOSTADAS to validate this metadata by adding: `--custom_fields_file <path/to/metadata_custom_fields.json> --validate_custom_fields` to your command.

replace\_empty\_with: TOSTADAS will replace any empty cells with this value (Example application: NCBI expects some value for any mandatory field, so if empty you may want to change it to "Not Provided".)

new\_field\_name: TOSTADAS will replace the field name in your metadata Excel file with this value. (Example application: you get weekly metadata Excel files and they specify 'animal\_environment' but NCBI expects 'animal\_env'; you can specify this once in the JSON file and it will be changed on every run.)

**Note**: All fields for the BioSample package Pathogen.cl.1.0. are already in the metadata template.

### Built-in BioSample package profiles

TOSTADAS has built-in profiles for two BioSample packages to support specific programs.  These profiles automatically import a custom_fields JSON file preconfigured for that package. Here's how to use them:

* SARS-CoV-2.wwsurv.1.0 
    1. Change the BioSample_package field in `conf/submission_config.yaml` to `SARS-CoV-2.wwsurv.1.0`
    2. Use `assets/sample_metadata/wastewater_biosample_template.xlsx` as your metadata template
    3. Run as: `nextflow run main.nf -profile nwss,<docker|singularity> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml>`
* OneHealthEnteric.1.0
    1. Change the BioSample_package field in `conf/submission_config.yaml` to `OneHealthEnteric.1.0`
    2. Use `assets/sample_metadata/onehealth_biosample_package_template.xlsx` as your metadata template
    3. Run as: `nextflow run main.nf -profile pulsenet,<docker|singularity> --meta_path <path/to/metadata_file.xlsx> --submission_config <path/to/submission_config.yaml>`
