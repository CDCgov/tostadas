# Outputs

## Pipeline Overview:

The workflow will generate outputs in the following order:

*   Validation
    *   Responsible for QC of metadata
    *   Aligns sample metadata .xlsx to sample .fasta
    *   Formats metadata into .tsv format
*   Annotation
    *   Extracts features from .gff
    *   Aligns features
    *   Annotates sample genomes outputting .gff
*   Submission
    *   Formats for database submission
    *   In full\_submission mode, the pipeline polls NCBI for reports using exponential backoff before proceeding to GenBank submission.

## Output Directory Formatting:

The outputs are recorded in the directory specified within the nextflow.config file and will contain the following:

*   validation/ (name configurable with `validation_outdir`)
    *   errors
    *   fasta
    *   tsv\_per\_sample
    *   batch\_summary.json (records batch composition for reproducible re-submissions)
*   annotation/liftoff/ (name configurable with `annotation_outdir`)
    *   errors
    *   fasta
    *   liftoff
    *   tbl
*   annotation/vadr/ (name configurable with `annotation_outdir`)
    *   errors
    *   fasta
    *   gffs
    *   tbl
    *   batch\_pass\_fail.tsv (per-sample pass/fail summary from VADR)
    *   batch\_alerts.tsv (per-sample alert details from VADR)
*   annotation/bakta/ (name configurable with `annotation_outdir`)
    *   fasta
    *   gff
    *   tbl
*   submission/ (name and path configurable with `submission_outdir`)
    *   batch\_N
        *   biosample
        *   sra
        *   genbank/
            *   submission files (.sqn, .zip, submission.xml)
        *   log\_file
        *   batch\_summary.json
*   accessions/ (name and path configurable with `accessions_outdir`)
    *   updated\_metadata\_Excel\_file
    *   submission\_report\_file

## Understanding Pipeline Outputs:

The pipeline outputs include:

*   batch_<n>.tsv files for each sample (one for each sample batch)
*   separate fasta files for each sample
*   separate gff files for each sample
*   separate tbl files containing feature information for each sample
*   submission log files
    *   This output is found in the submission/ directory within your specified output\_directory
