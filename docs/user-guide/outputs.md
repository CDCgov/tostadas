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
    *   This section runs twice, with the second run occurring after a wait time to allow for all samples to be uploaded to NCBI.

## Output Directory Formatting:

The outputs are recorded in the directory specified within the nextflow.config file and will contain the following:

*   validation\_outputs (name configurable with `validation_outdir`)
    *   name of metadata sample file
        *   errors
        *   fasta
        *   tsv\_per\_sample
*   liftoff\_outputs (name configurable with `final_liftoff_outdir`)
    *   name of metadata sample file
        *   errors
        *   fasta
        *   liftoff
        *   tbl
*   vadr\_outputs (name configurable with `vadr_outdir`)
    *   name of metadata sample file
    *   errors
    *   fasta
    *   gffs
    *   tbl
*   bakta\_outputs (name configurable with `bakta_outdir`)
    *   name of metadata sample file
    *   fasta
    *   gff
    *   tbl
*   submission\_outputs (name and path configurable with `submission_outdir`)
    *   name of annotation results (Liftoff or VADR, etc.)
        *   individual\_sample\_batch\_info
        *   biosample\_sra
        *   genbank
        *   accessions.csv
    *   terminal\_outputs
    *   commands\_used

## Understanding Pipeline Outputs:

The pipeline outputs include:

*   metadata.tsv files for each sample
*   separate fasta files for each sample
*   separate gff files for each sample
*   separate tbl files containing feature information for each sample
*   submission log file
    *   This output is found in the submission\_outputs file in your specified output\_directory
