# Outputs

## Pipeline Overview

The workflow will generate outputs in the following order:

- **Validation**
    - Responsible for QC of metadata
    - Aligns sample metadata .xlsx to sample .fasta
    - Formats metadata into .tsv format
- **Annotation**
    - Extracts features from .gff
    - Aligns features
    - Annotates sample genomes outputting .gff
- **Submission**
    - Formats for database submission
    - In full\_submission mode, the pipeline polls NCBI for reports using exponential backoff before proceeding to GenBank submission.

## Output Directory Formatting

The outputs are recorded in the directory specified within the nextflow.config file and will contain the following:

- `validation/` (name configurable with `--validation_outdir`)
    - `errors`
    - `fasta`
    - `tsv_per_sample`
    - `batch_summary.json` (records batch composition for reproducible re-submissions)
- `annotation/liftoff/` (name configurable with `--annotation_outdir`)
    - `errors`
    - `fasta`
    - `liftoff`
    - `tbl`
- `annotation/vadr/` (name configurable with `--annotation_outdir`)
    - `errors`
    - `fasta`
    - `gffs`
    - `tbl`
    - `batch_pass_fail.tsv` (per-sample pass/fail summary from VADR)
    - `batch_alerts.tsv` (per-sample alert details from VADR)
- `annotation/bakta/` (name configurable with `--annotation_outdir`)
    - `fasta`
    - `gff`
    - `tbl`
- `submission/` (name and path configurable with `--submission_outdir`)
    - `batch_N`
        - `biosample`
        - `sra`
        - `genbank/` -- submission files (.sqn, .zip, submission.xml)
        - `log_file`
        - `batch_summary.json`
- `accessions/` (name and path configurable with `--accessions_outdir`)
    - `updated_metadata_Excel_file`
    - `submission_report_file`

## Understanding Pipeline Outputs

The pipeline outputs include:

- `batch_<n>.tsv` files for each sample (one for each sample batch)
- Separate fasta files for each sample
- Separate gff files for each sample
- Separate tbl files containing feature information for each sample
- Submission log files
    - This output is found in the `submission/` directory within your specified output directory
