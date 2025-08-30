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
    *   individual\_sample\_batch\_folder
        *   biosample
        *   sra
        *   genbank
        *   log\_file
*   final\_submission\_outputs (name and path configurable with `final_submission_outdir`)
    *   updated\_metadata\_Excel\_file
    *   submission\_report\_file

## Understanding Pipeline Outputs:

The pipeline outputs include:

*   batch_<n>.tsv files for each sample (one for each sample batch)
*   separate fasta files for each sample
*   separate gff files for each sample
*   separate tbl files containing feature information for each sample
*   submission log files
    *   This output is found in the submission\_outputs file in your specified output\_directory
