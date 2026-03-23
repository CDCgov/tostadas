# Developer Notes

## Outline

The workflows are:
1. BIOSAMPLE_AND_SRA: Performs submission to BioSample and SRA repositories, fetches the reports, aggregates them and updates the metadata Excel file with assigned accession IDs.
2. GENBANK: performs annotation (optional, if `$params.annotation` is true), and then performs submission to GenBank repository.

The user options for `--workflow` are:

- **`biosample_and_sra`** -- Runs BIOSAMPLE_AND_SRA, then runs the AGGREGATE_SUBMISSIONS subworkflow (fetches reports, aggregates them, updates metadata file).
- **`genbank`** -- Runs GENBANK workflow. Expects `--updated_meta_path` to point to a validated metadata file (output of BIOSAMPLE_AND_SRA). Automatically looks for this in `$params.outdir/$params.accessions_outdir`.
- **`fetch_accessions`** -- Runs AGGREGATE_SUBMISSIONS. Looks in `--outdir` for batch directories under `submission/`. Fetches report.xml files for biosample and SRA submissions. Requires NCBI Center credentials from `submission_config.yaml`.
- **`full_submission`** -- Runs BIOSAMPLE_AND_SRA, then polls NCBI for reports using POLL_AND_FETCH_REPORTS (exponential backoff from `poll_initial_interval` to `poll_max_interval`, up to `poll_timeout`), then runs AGGREGATE_SUBMISSIONS, then runs GENBANK.
- **`update_submission`** -- Runs BIOSAMPLE_UPDATE workflow. Submits updates to biosample accessions. Requires a metadata file with `biosample_accession` column, such as the one output by BIOSAMPLE_AND_SRA in `$params.outdir/$params.accessions_outdir`.

## Workflow-Specific Details and Notes

The master branch supports individual sample submission only. The dev branch adds batch submission support.

### Submitting to BioSample and SRA

This workflow consists of the following processes and two subworkflows (SUBMISSION and AGGREGATE_SUBMISSIONS).
The user can submit only to biosample by setting `$params.sra = false` or to both biosample and sra using `$params.sra = true`.

**METADATA_VALIDATION** -- Expects an Excel file (`$params.meta_path`), performs validation, and outputs batch TSV files and an error log. Each TSV contains valid metadata for a number of submissions specified by `$params.batch_size`. Outputs to `$params.outdir/$params.validation_outdir/batched_tsvs`.

**CHECK_VALIDATION_ERRORS** -- Exits the pipeline if at least one ERROR is found in the validation log. Input: the validation log. Output: status ("OK" or "ERROR").

**WRITE_VALIDATED_FULL_TSV** -- Collects the batch TSV files and concatenates them into one validated TSV. Output: `$params.outdir/$params.validation_outdir/validated_metadata_all_samples.tsv`. This file is used in the AGGREGATE_SUBMISSIONS subworkflow.

**SUBMISSION** -- Subworkflow that runs two processes:

- **PREP_SUBMISSION** -- Prepares all submissions. Creates `submission.xml` and `submit.ready` files, symlinks FASTQ files for SRA. Creates the `batch_<n>/<biosample|sra|genbank>` folder structure. Most helper functions are in `submission_helper.py`.
- **SUBMIT_SUBMISSION** -- Uploads submission folders to NCBI FTP. Run with `$params.dry_run` to preview actions. Folder names on NCBI FTP follow the pattern: `submit/Test/<metadata_filename>_<batch_n>_<biosample|sra>/`. When submitting both Illumina and Nanopore data to SRA, these are placed in separate subdirectories (`illumina/` and `nanopore/`) since each requires its own `submission.xml`.

**AGGREGATE_SUBMISSIONS** -- Subworkflow that runs three processes:

- **POLL_AND_FETCH_REPORTS** -- Polls the NCBI FTP server with exponential backoff (from `poll_initial_interval` to `poll_max_interval`, up to `poll_timeout`) until reports are available, then fetches and parses them into a batch-specific CSV report. Publishes to `$params.accessions_outdir`.
- **AGGREGATE_REPORTS** -- Collates individual batch report CSVs into one final `submission_report.csv`. Output: `$params.outdir/$params.accessions_outdir/submission_report.csv`.
- **JOIN_ACCESSIONS_WITH_METADATA** -- Updates the initial Excel file with accession IDs. Output: `$params.outdir/$params.accessions_outdir/<metadata_filename>_updated.xlsx`.

### Submitting to GenBank

This requires `--updated_meta_path`. It can be specified in `nextflow.config`.
If not specified, it looks for the output of JOIN_ACCESSIONS_WITH_METADATA (`$params.outdir/$params.accessions_outdir/<your_metadata_filename>__updated.xlsx`)

GENBANK workflow does not validate metadata. It is assumed the user will run biosample_and_sra first (because GenBank submission requires a BioSample accession ID). 
It validates the fasta file.
If `$params.annotation = true`, it performs annotation as follows.
And it performs submission.  It does not fetch the accession IDs because at the time of development, many GenBank submissions are not done via ftp.


The updated metadata file is rebatched for GenBank submission using the same batch structure as the BioSample/SRA submission.

**GENBANK_VALIDATION** -- Validates the FASTA file according to NCBI requirements. Outputs the validated FASTA renamed to `<original_name>_cleaned.fsa`.

If `$params.annotation = true`, one of the following annotation subworkflows runs depending on organism type and configuration:

**REPEATMASKER_LIFTOFF** (when `$params.repeatmasker_liftoff = true`) -- Subworkflow with three processes. Custom repeats library and reference files can be specified via `$params.repeat_library`, `$params.ref_fasta_path`, and `$params.ref_gff_path`.

- **REPEATMASKER** -- Runs RepeatMasker. Outputs: .cat, .gff, .tbl, .masked, .out
- **LIFTOFF_CLI** -- Runs Liftoff. Inputs: FASTA, reference FASTA, reference GFF. Outputs: FASTA, .gff, errors log
- **CONCAT_GFFS** -- Joins annotations from RepeatMasker and Liftoff. Outputs: .gff, .tbl, errors log

**RUN_VADR** (when `$params.vadr = true`) -- Subworkflow with four processes. The VADR model library is specified via `$params.vadr_models_dir` and uses `$params.virus_subtype` as the `mkey` value.

- **VADR_TRIM** -- Runs `fasta-trim-terminal-ambigs.pl`. Outputs: trimmed FASTA
- **VADR_ANNOTATION** -- Annotates the FASTA using the specified model library. Outputs: VADR output directory (`<sample_id>_<virus_subtype>`)
- **VADR_POST_CLEANUP** -- Final cleanup of annotations. Outputs: .gff, .tbl, errors log
- **SUMMARY** -- Generates batch-level VADR summary reports. Outputs: `batch_pass_fail.tsv` and `batch_alerts.tsv`, published to `annotation/vadr/`

**RUN_BAKTA** (when `$params.bakta = true` and `$params.organism_type = bacteria`) -- Subworkflow with two nf-core modules.

- **BAKTA_BAKTADBDOWNLOAD** -- Downloads the specified Bakta database
- **BAKTA_BAKTA** -- Annotates the FASTA. Outputs: all Bakta output files

**SUBMISSION_GENBANK** -- Same subworkflow structure as BioSample/SRA submission but uses process aliases (PREP_GENBANK and SUBMIT_GENBANK) so that GenBank outputs are written to separate directories. This prevents overwriting in `full_submission` mode.


### Updating a BioSample Submission

This workflow requires that `${params.meta_path}` point to a metadata file with the updated biosample fields and a `biosample_accession` column with a valid Accession ID. 
The workflow as-is does not check the validity of the biosample accession because there is no straightforward way to do that.  Please make sure your accession ID is valid and correct.

The workflow also requires `${params.original_submission_outdir}` which should point to your original NCBI submission for these samples.
It is expecting that the original submission was made with Tostadas, so it wants a path ending in `submission` (`${params.submission_outdir}`) here.
It will look through the batch folders for `biosample/submission.xml` to validate that certain fields are unchanged, as required by NCBI.

It also expects to find the batch_summary.json file from the original submission (in validation/batched_tsvs) and it uses this file to recreate the same batches as in the original submission.
It has to do this in order to validate that certain metadata are unchanged from the original submission, and to update the original submission with the PrimaryId.

The workflow runs METADATA_VALIDATION, CHECK_VALIDATION_ERRORS, and WRITE_VALIDATED_FULL_TSV as in BIOSAMPLE_AND_SRA workflow.  After that, it diverges as follows:

**REBATCH_METADATA** -- Recreates the original batches to match the data in `${params.original_submission_outdir}`. Inputs: `validated_metadata_all_samples.tsv` and the original `batch_summary.json`. Outputs: rebatched JSON and TSV files.

**UPDATE_SUBMISSION** -- Updates the biosample submission. Inputs: batch samples, submission config, and original submission directory. Outputs: updated batch directory and log file.


## Known Issues

- GenBank accession fetching is enabled but may require additional handling for downstream report CSV and updated metadata file generation.
- Additional testing is required for the `update_submission` workflow. More nf-tests should be created.
- A specific annotation directive line may need to be added to the GenBank XML for FTP-based submissions when no GFF is provided. GenBank SQN files for SARS and flu have not been tested.
- VADR model directory vs. virus subtype validation has been added as a pre-flight check, but additional robustness may be needed.
- In `update_submission`, the metadata file is referenced from its work directory rather than being staged as a proper Nextflow input. This should be refactored.
- The `update_submission` workflow only supports BioSample updates. The `enabled` list in `REBATCH_METADATA` is hardcoded to `["biosample"]`. Extending to SRA or GenBank updates requires changes to both `REBATCH_METADATA` and `UPDATE_SUBMISSION`.
- In `submission_helper.py`, some GenBank validation values (around line 963) are hard-coded and should be made configurable. BioSample/SRA XML generation differs from GenBank XML generation (see `submission_prep.py`). The locus tag prefix issue (line ~1222) has been resolved with a logged warning.