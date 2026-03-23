# Submission Guide

## Putting together the Nextflow command

Your basic command starts like this: `nextflow run main.nf -profile <docker|singularity|conda>` but needs to be configured further. See below.

## Choosing a workflow

Choose how you want to run TOSTADAS using the `--workflow` parameter:

- **biosample_and_sra**: Runs a submission to BioSample and SRA. Add `--biosample false` or `--sra false` to toggle off submission to one or the other.
- **genbank**: Runs a GenBank submission. This requires an updated metadata file that includes `biosample_accession` as required by NCBI.
- **fetch_accessions**: Fetches reports and updates the metadata file.
- **full_submission**: Executes BioSample and SRA submissions, polls NCBI for reports using exponential backoff (30s--120s intervals, 30min timeout), updates the metadata file with accession IDs, and then performs the GenBank submission. Polling parameters can be tuned with `--poll_initial_interval`, `--poll_max_interval`, and `--poll_timeout`.
- **update_submission**: Executes a BioSample submission using an updated metadata Excel file. **Note:** This workflow currently supports BioSample updates only. SRA and GenBank updates are not supported.

## Choosing an organism type and/or virus subtype

If you want to run viral annotation, you need to specify a `--virus_subtype <mpxv|rsv|mev>`.  This tells TOSTADAS which annotator profile to use if you're running VADR.

If you want to run bacterial annotation, you need to specify `--organism_type bacteria`. This tells TOSTADAS to annotate using bakta.  You can instead use a profile (see [Using specific profiles](#using-specific-profiles)).

If you're submitting to GenBank (the only option if you want to run annotation), you need to specify `--organism_type <virus|bacteria|eukaryote>`.  This tells TOSTADAS which kind of GenBank submission to do.
FTP submission to GenBank is only supported for bacteria and eukaryote assemblies.  Virus assemblies must be submitted via email (either using TOSTADAS or manually emailing the files in the results folder).

## Using specific profiles

TOSTADAS supports some profiles to make submission easier.  These are specified in the `-profile` option. See [Custom metadata validation and custom BioSample package](#custom-metadata-validation-and-custom-biosample-package) for more detail.

- **test**: Runs a test submission. It prepares all the files but does not actually submit to the test server. To submit to the test server, add `--dry_run false`
- **nwss**: Submits to SARS-CoV-2.wwsurv.1.0 BioSample package.
- **pulsenet**: Submits to OneHealthEnteric.1.0 BioSample package.
- **virus**: Sets defaults for virus submission (to run a test virus submission, use `profile test,virus,<docker|singularity|conda>`)
- **bacteria**: Sets defaults for bacteria submission (to run a test bacteria submission, use `profile test,bacteria,<docker|singularity|conda>`)
- **mpox**: Sets defaults for MPOX submission (to run a test MPOX submission, use `profile test,mpox,<docker|singularity|conda>`)
- **rsv**: Sets defaults for RSV submission (to run a test RSV submission, use `profile test,rsv,<docker|singularity|conda>`)
- **measles**: Sets defaults for Measles submission (to run a test Measles submission, use `profile test,measles,<docker|singularity|conda>`)

## Metadata input formats

TOSTADAS accepts metadata in `.xlsx`, `.csv`, `.tsv`, and `.src` (NCBI source modifier) formats via the `--meta_path` parameter.

When using `.src` files, column names are automatically mapped to TOSTADAS fields:

| Source Modifier Column | TOSTADAS Field |
|---|---|
| `SeqId` / `SeqID` | `sample_name` |
| `Strain` | `strain` |
| `Collection_date` | `collection_date` |
| `Host` | `host` |
| `Isolate` | `isolate` |

The `Country` field, when provided in `USA:State` format, is automatically split into its component parts.

### Collection date formats

Collection dates can be provided in ISO 8601 format (YYYY-MM-DD or YYYY-MM) or in NCBI abbreviated formats such as `Mon-YYYY` (e.g., Aug-2025) or `Mon.YY` (e.g., Aug.25). Abbreviated formats are converted to ISO 8601 (YYYY-MM) during validation.

### Auto-populating FASTA paths with --fasta_dir

When `--fasta_dir` is set, TOSTADAS scans the specified directory for FASTA files (`.fasta`, `.fa`, `.fna`, `.fas`) and matches them to the `sample_name` column in your metadata. Matched files are used to populate `fasta_path` automatically, eliminating the need to list file paths in the metadata for large sample sets. Samples without a matching FASTA file are skipped with a warning.

### GenBank-only mode

Use `--genbank_only` to skip BioSample/SRA-specific validation (ncbi-spuid, authors, isolation_source checks). This is useful when generating SQN files for GenBank submission without needing to register BioSamples.

### Using an existing .sbt template

Pass `--sbt <path/to/template.sbt>` to provide a pre-existing template file from NCBI's template tool. When set, TOSTADAS uses this file directly for table2asn instead of generating one from submission_config.yaml. This is useful when reusing `.sbt` files from other pipelines or NCBI's web-based template generator.

## Other customizations

All the custom parameters for TOSTADAS are found in nextflow.config and the config files inside `conf/`.  You can override any of these by specifying the parameter on the command line.

For example, the default output directory is `results`, but you can override that and choose your own output directory using `--outdir path/to/my/output` in your command.

TOSTADAS can chunk large datasets into smaller groups to submit to NCBI's servers using the `--batch_size` flag.  If you have a metadata Excel file with 200 samples, you can submit them in batches of 50 by adding `--batch_size 50` to your command. This groups 50 samples at a time into one submission file for each data repository. NCBI much prefers this over submitting samples one-at-a-time.

!!! tip
    We **highly** recommend you submit using batches. We suggest 50 as a maximum batch size.

Another example: the `--dry_run` flag (which prepares files for submission but doesn't upload to the server) defaults to `true` for the test profile and `false` otherwise, but you can override it by specifying `--dry_run <true|false>` on the command line.

## Submitting to Production

TOSTADAS defaults to submitting to the test server even if not using the test profile, to avoid accidentally pushing data to NCBI's Production server.

When you've completed testing and are ready to submit for production, add `--prod_submission` to your command line (or change `prod_submission` to `true` in `nextflow.config`).

## Typical example workflow

We'll run test submissions to BioSample and SRA using the test MPOX data included in the repository.

Submit to biosample and sra:

```bash
nextflow run main.nf -profile test,singularity,mpox --workflow biosample_and_sra --dry_run false --submission_config conf/submission_config.yaml --batch_size 5
```

!!! warning
    Remember to add credentials to your submission_config.yaml file.

Fetch the accessions if they weren't assigned (this workflow creates an updated Metadata Excel file with the validated fields and the accession IDs):

```bash
nextflow run main.nf -profile test,singularity,mpox --workflow fetch_accessions --dry_run false --submission_config conf/submission_config.yaml
```

Submit an updated biosample submission (open the updated Excel file from results/accessions/mpxv_test_metadata_updated.xlsx and add some fake SAMN IDs first):

```bash
nextflow run main.nf -profile test,singularity,mpox --workflow update_submission --dry_run false --submission_config conf/submission_config.yaml --batch_size 5 --original_submission_outdir results/submission --meta_path results/accessions/mpxv_test_metadata_updated.xlsx
```

!!! warning
    This won't run without those fake SAMN IDs in the biosample_accession field.

Now we'll run a test GenBank submission using the test bacteria data included in the repository.

Submit to BioSample first (because GenBank requires a BioSample accession):

```bash
nextflow run main.nf -profile test,singularity,bacteria --workflow biosample_and_sra --dry_run false --submission_config conf/submission_config.yaml
```

Open the updated Excel file from results/accessions/bacteria_test_metadata_1_updated.xlsx and add some fake SAMN IDs first.

!!! warning
    The next command won't run without the fake SAMN IDs in biosample_accession column.

```bash
nextflow run main.nf -profile test,singularity,bacteria --workflow genbank --dry_run false --submission_config conf/submission_config.yaml --annotation --download_bakta_db --bakta_db_type light
```

## GenBank Submission Conditions

GenBank submission behavior in TOSTADAS varies depending on the organism type. This section describes the submission paths, prerequisites, annotation handling, expected processing times, and how to retrieve accessions.

### Submission paths by organism type

**Bacteria and eukaryotes** submit via the Whole Genome Shotgun (WGS) pathway. Set `--organism_type bacteria` or `--organism_type eukaryote`. The pipeline generates WGS-formatted XML (`target_db="WGS"`) and uploads it via FTP to NCBI. This path requires genome completeness fields in the submission XML (see [WGS prerequisites](#wgs-prerequisites) below).

**SARS-CoV-2 and influenza** submit via BankIt FTP. Set `--organism_type virus`. The pipeline generates submission XML with `target_db="GenBank"` and uploads via FTP. NCBI annotates these sequences server-side, so no SQN file is generated or required.

**All other viruses** (e.g., mpox, RSV) require an SQN file produced by VADR annotation. The pipeline generates the SQN file locally, packages it into a zip archive, and emails it to NCBI. This submission cannot be done via FTP; it must go through email (either automated by TOSTADAS when `table2asn_email` is configured, or manually by emailing the zip from the results folder).

### Prerequisites

**BioSample must be submitted before GenBank.** The WGS submission XML references each sample's `biosample_accession`, so those accessions must already exist. If you use the `full_submission` workflow, TOSTADAS handles this ordering automatically. If you run workflows individually, submit BioSample first, fetch accessions, then run the `genbank` workflow.

#### WGS prerequisites

For WGS submissions (bacteria and eukaryotes), TOSTADAS includes two additional fields in the submission XML:

- `genome_representation` -- Set to `Full` (complete genome) or `Partial` (incomplete assembly). Defaults to `Full`.
- `expected_final_version` -- Set to `Yes` if this is the final version of the assembly or `No` if updates are expected. Defaults to `Yes`.

These can be configured via your metadata or pipeline parameters.

### Annotation directives

When no annotation file is provided, the pipeline automatically adds annotation directives to the submission XML:

- **WGS submissions**: Adds `annotate=yes`, which requests NCBI run PGAP (Prokaryotic Genome Annotation Pipeline) on the submitted assembly.
- **BankIt submissions**: Adds `auto_remove_failed_seqs=yes`, which tells NCBI to automatically drop sequences that fail validation rather than rejecting the entire submission.

If you supply your own annotation files, these directives are not added.

### Processing times

Expect the following turnaround times after submission to NCBI:

| Organism / Pathway | Typical Processing Time |
|---|---|
| SARS-CoV-2 (BankIt FTP) | ~10 minutes |
| Influenza via BankIt FTP | 1--5 days |
| WGS bacteria or eukaryote | 2--4 weeks |
| Annotated eukaryotes | 1+ months |

These times are approximate and depend on NCBI queue depth. Production submissions generally process faster than test submissions.

### Accession retrieval

**FTP-submitted organisms** (bacteria, eukaryotes, and BankIt viruses): Accessions are available in `report.xml` on the NCBI FTP server. Use the `fetch_accessions` workflow to download and parse these reports automatically.

**Email-submitted viruses** (mpox, RSV, and other non-BankIt viruses): Accessions are not available via FTP. Check the [NCBI Submission Portal](https://submit.ncbi.nlm.nih.gov/) manually for status and assigned accession numbers.

## Submission config fields

The fields and corresponding example values can be found here: [Submission Config](https://github.com/CDCgov/tostadas/raw/main/conf/submission_config.yaml).

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

### Supported BioSample packages

TOSTADAS validates required fields for each BioSample package using `assets/biosample_fields_key.yaml`. The table below lists every package that TOSTADAS supports with built-in field validation. To select a package, set the `BioSample_package` field in `conf/submission_config.yaml` to the desired package name.

| Package | Description | Nextflow Profile |
|---|---|---|
| `Pathogen.cl.1.0` | Pathogen: clinical or host-associated sample data (pipeline default) | -- |
| `Pathogen.env.1.0` | Pathogen: environmental or food sample data | -- |
| `SARS-CoV-2.cl.1.0` | SARS-CoV-2: clinical or host-associated surveillance | -- |
| `SARS-CoV-2.wwsurv.1.0` | SARS-CoV-2: wastewater surveillance (NWSS program) | `nwss` |
| `Microbe.1.0` | General microbial samples | -- |
| `Virus.1.0` | General virus isolate samples | -- |
| `Human.1.0` | Human tissue or clinical samples | -- |
| `Metagenome.environmental.1.0` | Environmental metagenome samples | -- |
| `OneHealthEnteric.1.0` | PulseNet One Health enteric pathogen surveillance | `pulsenet` |
| `Beta-lactamase.1.0` | Beta-lactamase antimicrobial resistance characterization | -- |

Packages listed with a Nextflow profile name (e.g., `nwss`, `pulsenet`) have a preconfigured profile that automatically sets the correct custom fields JSON and metadata template. For those packages, see [Built-in BioSample package profiles](#built-in-biosample-package-profiles) below. Packages marked `--` require manual configuration as described in the steps that follow.

TOSTADAS defaults to Pathogen.cl.1.0 (Pathogen: clinical or host-associated; version 1.0) NCBI BioSample package for submissions to the BioSample repository. You can submit using a different BioSample package by doing the following:

1.  Change the package name in the `conf/submission_config.yaml`. Choose one of the available [NCBI BioSample packages](https://www.ncbi.nlm.nih.gov/biosample/docs/packages/).
2.  Add the necessary fields for your BioSample package to your input Excel file.
3.  Add those same fields as keys to the JSON file (`assets/custom_meta_fields/example_custom_fields.json`) and provide key info as needed. This lets TOSTADAS know to validate and submit those added fields.
4.  Tell TOSTADAS to validate this metadata by adding: `--custom_fields_file <path/to/metadata_custom_fields.json> --validate_custom_fields` to your command.

replace\_empty\_with: TOSTADAS will replace any empty cells with this value (Example application: NCBI expects some value for any mandatory field, so if empty you may want to change it to "Not Provided".)

new\_field\_name: TOSTADAS will replace the field name in your metadata Excel file with this value. (Example application: you get weekly metadata Excel files and they specify 'animal\_environment' but NCBI expects 'animal\_env'; you can specify this once in the JSON file and it will be changed on every run.)

!!! note
    All fields for the BioSample package Pathogen.cl.1.0. are already in the metadata template.

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
