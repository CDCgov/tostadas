# Notes for Developers (and Confused Users)

## Outline

The workflows are:
1. BIOSAMPLE_AND_SRA: Performs submission to BioSample and SRA repositories, fetches the reports, aggregates them and updates the metadata Excel file with assigned accession IDs.
2. GENBANK: performs annotation (optional, if `$params.annotation` is true), and then performs submission to GenBank repository.

The user options for "workflow" are:
1. `--workflow biosample_and_sra`: Runs BIOSAMPLE_AND_SRA, then runs the AGGREGATE_SUBMISSIONS subworkflow (fetches reports, aggregates them, updates metadata file)
2. `--genbank`: Runs GENBANK workflow. It expects `--updated_meta_path` to point to an Excel file that matches the format of a validated metadata file (output of BIOSAMPLE_AND_SRA).
                It automatically looks for this in the output directory in a subdirectory called `final_submission_outputs` within the metadata-specific subdirectory (`$params.outdir/$params.metadata_basename/$final_submission_outdir`)
3. `--fetch_accessions`: Runs AGGREGATE_SUBMISSIONS. It will look in `--outdir` for the relevant metadata subdirectory (the basename of your metadata file) and then traverse the batch directories under `submission_outputs`.
                         It fetches the report.xml files for biosample and sra submissions for each batch. It needs your NCBI Center credentials from `submission_config.yaml`
4. `--full_submissions`: Runs BIOSAMPLE_AND_SRA, then waits for awhile, then runs AGGREGATE_SUBMISSIONS, then runs GENBANK.
                         It waits for `$params.submission_wait_time` seconds, and if `$params.submission_wait_time` is `calc`, then it waits for 3 minutes * `params.batch_size`.
                         This is based on rudimentary testing that suggests NCBI takes about 3 minutes per submission to issue accession IDs (for multiple submissions).

## Workflow-specific Details and Notes

### Submitting to BioSample and SRA

This workflow is pretty straightforward.  It has a few standalone processes and two subworkflows (SUBMISSION and AGGREGATE_SUBMISSIONS).
The user can submit only to biosample by setting `$params.sra = false` or to both biosample and sra using `$params.sra = true`.

1. METADATA_VALIDATION: Process that expects an Excel file (`$params.meta_path`), performs validation and outputs tsv files (and an error log). 
                        Each tsv files contains valid metadata for a number of submissions specified by `$params.batch_size`.
                        Outputs are here: `$params.outdir/$params.metadata_basename/$params.validation_outdir/batched_tsvs`.  By default, it's: $outdir/<your_metadata_filename>/validation_outputs/batched_tsvs

2. CHECK_VALIDATION_ERRORS: Process that exits the pipeline if at least one ERROR is found in the validation log.  ERRORs will not pass NCBI submission checks.
                        Input: the validation log. Outputs: status ("OK" or "ERROR"), and pipeline exists if status is "ERROR".

3. WRITE_VALIDATED_FULL_TSV: Process that collects the batch tsv files in `batched_tsvs` and concatenates them into one validated tsv file.
                        Input: a list of all batched_tsv files. Output: `$params.outdir/$params.metadata_basename/$final_submission_outdir/validated_metadata_all_samples.tsv`.
                        This output file will be used in the AGGREGATE_SUBMISSIONS subworkflow.

4. SUBMISSION: Subworkflow that runs two (2) processes.
               Input: a Nextflow channel for one batch. Output: the submission folder (as a Nextflow channel) for that batch.

    PREP_SUBMISSION: Process that prepares all the submissions. This instantiates biosample and sra class instances, creates submission.xml and submit.ready files, and symlinks fastq files for sra submission.  
                     This is the script that creates the batch_<n>/<biosample|sra|genbank> folders. 
                     Most of its helper functions are in submission_helper.py.
                     Input: a tuple containing the list of samples and corresponding batch_id, and the submission config file. Output: a tuple containing the batch directory, and a prep_submission log file.

    SUBMIT_SUBMISSION: Process that actually submits the folders. Run with `$params.dry_run` to see what it will do (e.g., "would upload Folder X to Folder Y via ftp").
                Folder names on NCBI ftp site are constructed based on local names and following NCBI's requirement that each folder ONLY contain one XML, one submit.ready, and (if sra) the relevant raw sequence files.
                The folder structure will look like this: (local) <your_metadata_filename>/submission_outputs/<batch_n>/<biosample|sra>/ → (remote) submit/Test/<your_metadata_filename>_<batch_n>_<biosample|sra>/
                NOTE: if you're submitting both Illumina and Nanopore data to SRA, these have to be in different submission.xml files. Therefore, they need to be in different folders, so they go here:
                    (local) <your_metadata_filename>/submission_outputs/<batch_n>/<sra>/<illumina|nanopore> → (remote) submit/Test/<your_metadata_filename>_<batch_n>_<sra>_<illumina|nanopore>/
                Input: a tuple containing containing the batch directory, and the submission config file. Output: a tuple containing the batch directory, and a submission log file.

5. AGGREGATE_SUBMISSIONS: Subworkflow that runs three (3) processes:

    FETCH_REPORTS: Process that traverses the submission directory and look for the reports for each database inside each batch dir. Parses these XMLs into a batch-specific csv report file.
                   Publishes the results to `$params.submission_output_dir1
                   Input: Submission batch directory and submission config file. Output: fetch_submission log and batch report csv file.

    AGGREGATE_REPORTS: Process that collates the individual batch report csvs into one final report.csv
                   Input: Collected list (actually a Nextflow channel) of all the report csvs. Output: `$params.outdir/$params.metadata_basename/$final_submission_outdir/submission_report.csv`

    JOIN_ACCESSIONS_WITH_METADATA: Updates the initial Excel file with the accession IDs, which is needed for genbank submission.
                   Input: `$params.outdir/$params.metadata_basename/$final_submission_outdir/submission_report.csv` (AGGREGATE_REPORTS output) 
                          `$params.outdir/$params.metadata_basename/$final_submission_outdir/validated_metadata_all_samples.tsv` (WRITE_VALIDATED_FULL_TSV output)
                   Output: `$params.outdir/$params.metadata_basename/$final_submission_outdir/<your_metadata_filename>__updated.xlsx`

### Submitting to GenBank

This requires `--updated_meta_path`. It can be specified in `nextflow.config`.
If not specified, it looks for the output of JOIN_ACCESSIONS_WITH_METADATA (`$params.outdir/$params.metadata_basename/$final_submission_outdir/<your_metadata_filename>__updated.xlsx`)

GENBANK workflow doesn't validate metadata. It is assumed the user will run biosample_and_sra first (because GenBank submission requires a BioSample accession ID). 
It validates the fasta file.
If `$params.annotation = true`, it performs annotation as follows.
And it performs submission.  It does not fetch the accession IDs because at the time of development, many GenBank submissions are not done via ftp.


1. CREATE_BATCH_TSVS: Process that creates batch tsv files of size `$params.batch_size` from the updated metadata file.
            This process just replicates what metadata validation outputs because the structure is needed downstream and this was the most straightforward way to do that.
            Inputs: Path to the updated Excel file and batch size value. Outputs: Path to all the batch tsv files.

2. GENBANK_VALIDATION: Process that validates the fasta file according to NCBI requirements.
            Inputs: Tuple including a path to the original fasta. Outputs: Tuple including a path to the validated fasta, which is the original fasta renamed to `<original name>_cleaned.fsa`

if `$params.annotation = true` and `$params.repeatmasker_liftoff = true`:
    NOTE: This can take the path to any repeats library and ref files by specifying `$params.repeat_library`, `$params.ref_fasta_path`, and `$params.ref_gff_path`.

3. REPEATMASKER_LIFTOFF: Subworkflow consisting of three (3) processes
            Inputs: validated fasta. Outputs: validated fasta and gff.
    REPEATMASKER: Process that runs RepeatMasker.
            Inputs: fasta and repeats library. Outputs: all the outputs of repeatmasker (.cat, .gff, .tbl, .masked, .out)
    LIFTOFF_CLI: Process that runs liftoff.
            Inputs: fasta, reference fasta, reference gff. Outputs: all the outputs of liftoff (fasta, .gff, errors log)
    CONCAT_GFFS: Process that joins the annotations from RepeatMasker and Liftoff.
            Inputs: Tuple containing the fasta, the repeatmasker gff, and the liftoff gff; and a reference gff. Outputs: .gff, .tbl, errors log

if `$params.annotation = true` and `$params.vadr = true`:
    NOTE: The vadr model library can be specified using `$params.vadr_models_dir`, BUT it uses `$params.species` as the value for `mkey`. 
    Run the vadr container, and run `v-annotate.pl -h` for more details on what `mkey` is, and see the VADR_ANNOTATION process (`--mkey ${params.species}`).
    To add more libraries will require a bit of development effort but is not difficult. 

3. RUN_VADR: Subworkflow consisting of three (3) processes
            Inputs: validated fasta. Outputs: .gff, .tbl, errors log.
    VADR_TRIM: Process that runs fasta-trim-terminal-ambigs.pl.
            Inputs: fasta. Outputs: trimmed.fasta
    VADR_ANNOTATION: Process that annotates the fasta using the model library specified.
            Inputs: trimmed.fasta and path to vadr models directory. Outputs: path to vadr output files in a folder that has the format: `<sample_id>_<species>`
    VADR_POST_CLEANUP: Process that performs final cleanup of annotations
            Inputs: path to vadr outputs from VADR_ANNOTATION. Outputs: .gff, .tbl, errors log.

if `$params.annotation = true` and `$params.bakta = true` and `$params.species = bacteria`:
3. RUN_BAKTA: Subworkflow consisting of two (2) processes.  These are the only two nf-core modules in this pipeline.
            Inputs: fasta. Outputs: gff and fasta.
    BAKTA_BAKTADBDOWNLOAD: Process that downloads the bakta db specified.
    BAKTA_BAKTA: Process that annotates the fasta.
            Inputs: fasta, path to the bakta db, `params.bakta_proteins` and `params.bakta_prodigal_tf`. Outputs: all the bakta output files

4. SUBMISSION: Subworkflow, same as for submitting to biosample and sra but only runs for genbank.


## Known issues and idiosyncracies

1. The pipeline doesn't fetch Genbank accession IDs, but it could if they are available.  Doing so requires some optional handling for downstream report csv and updated metadata file generation.

2. GenBank doesn't allow no annotations file.  This needs to be adjusted as GenBank increasingly prohibits user-provided annotations in preference for NCBI-generated annotations.
   For this to be updated, a specific line needs to be added to the XML file (where appropriate) indicating NCBI should annotate.
   
3. Need some robust checking for the vadr_models_dir vs. species (see notes under annotation)