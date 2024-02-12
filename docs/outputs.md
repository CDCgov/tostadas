# Outputs

The following section walks through the outputs from the pipeline.

## 6.1 Pipeline Overview:
The workflow will generate outputs in the following order:

* Validation
 * Responsible for QC of metadata
 * Aligns sample metadata .xlsx to sample .fasta
 * Formats metadata into .tsv format
* Annotation
 * Extracts features from .gff
 * Aligns features
 * Annotates sample genomes outputting .gff
* Submission
 * Formats for database submission
 This section runs twice, with the second run occuring after a wait time to allow for all samples to be uploaded to NCBI. Entrypoint `only_update_submission` can be run as many times as necessary until all files are fully uploaded.

## 6.2 Output Directory Formatting:
The outputs are recorded in the directory specified within the nextflow.config file and will contain the following:

* validation_outputs (name configurable with `val_output_dir`)
 * name of metadata sample file
 * errors
 * fasta
 * tsv_per_sample
* liftoff_outputs (name configurable with `final_liftoff_output_dir`)
 * name of metadata sample file
 * errors
 * fasta
 * liftoff
 * tbl
* vadr_outputs (name configurable with `vadr_output_dir`)
 * name of metadata sample file
 * errors
 * fasta
 * gffs
 * tbl
* bakta_outputs (name configurable with `bakta_output_dir`)
 * name of metadata sample file
 * fasta
 * gff
 * tbl
* submission_outputs (name and path configurable with `submission_output_dir`)
 * name of annotation results (Liftoff or VADR, etc.)
 * individual_sample_batch_info
  * biosample_sra
  * genbank
  * accessions.csv
 * terminal_outputs
 * commands_used

## 6.3 Understanding Pipeline Outputs:
The pipeline outputs include:

* metadata.tsv files for each sample
* separate fasta files for each sample
* separate gff files for each sample
* separate tbl files containing feature information for each sample
* submission log file
 * This output is found in the `submission_outputs` file in your specified `output_directory`.
 * If the file can not be found you can run the `only_update_submission` entrypoint for the pipeline.
