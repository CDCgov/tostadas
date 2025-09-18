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
4. `--full_submission`: Runs BIOSAMPLE_AND_SRA, then waits for awhile, then runs AGGREGATE_SUBMISSIONS, then runs GENBANK.
                         It waits for `$params.submission_wait_time` seconds, and if `$params.submission_wait_time` is `calc`, then it waits for 3 minutes * `params.batch_size`.
                         This is based on rudimentary testing that suggests NCBI takes about 3 minutes per submission to issue accession IDs (for multiple submissions).
5. `--update_submission`: Runs BIOSAMPLE_UPDATE workflow.  It is used to submit updates to biosample accessions.
                           It requires an Excel metadata file with biosample_accession, such as the one output by BIOSAMPLE_AND_SRA here: `$params.outdir/$params.metadata_basename/$final_submission_outdir`.

## Workflow-Specific Details and Notes

The master branch conducts sample submissions one at a time (not in batch).  It has a different command (notably, no `dry_run` flag and no `workflow` flag because it only run ones workflow).
One CDC team is still using the master branch, and was not ready to test and adapt their workflow for the dev branch (i.e., to handle batch sample submissions) as of August 2025.

**So dev cannot be merged to master.**

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
                   Publishes the results to `$params.submission_outdir`
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
    NOTE: The vadr model library can be specified using `$params.vadr_models_dir`, BUT it uses `$params.virus_subtype` as the value for `mkey`. 
    Run the vadr container, and run `v-annotate.pl -h` for more details on what `mkey` is, and see the VADR_ANNOTATION process (`--mkey ${params.virus_subtype}`).
    To add more libraries will require a bit of development effort but is not difficult. 

3. RUN_VADR: Subworkflow consisting of three (3) processes
            Inputs: validated fasta. Outputs: .gff, .tbl, errors log.
    VADR_TRIM: Process that runs fasta-trim-terminal-ambigs.pl.
            Inputs: fasta. Outputs: trimmed.fasta
    VADR_ANNOTATION: Process that annotates the fasta using the model library specified.
            Inputs: trimmed.fasta and path to vadr models directory. Outputs: path to vadr output files in a folder that has the format: `<sample_id>_<virus_subtype>`
    VADR_POST_CLEANUP: Process that performs final cleanup of annotations
            Inputs: path to vadr outputs from VADR_ANNOTATION. Outputs: .gff, .tbl, errors log.

if `$params.annotation = true` and `$params.bakta = true` and `$params.organism_type = bacteria`:
3. RUN_BAKTA: Subworkflow consisting of two (2) processes.  These are the only two nf-core modules in this pipeline.
            Inputs: fasta. Outputs: gff and fasta.
    BAKTA_BAKTADBDOWNLOAD: Process that downloads the bakta db specified.
    BAKTA_BAKTA: Process that annotates the fasta.
            Inputs: fasta, path to the bakta db, `params.bakta_proteins` and `params.bakta_prodigal_tf`. Outputs: all the bakta output files

4. SUBMISSION: Subworkflow, same as for submitting to biosample and sra but only runs for genbank.


### Updating a BioSample Submission

This workflow requires that `${params.meta_path}` point to a metadata file with the updated biosample fields and a `biosample_accession` column with a valid Accession ID. 
The workflow as-is DOES NOT check the validity of the biosample accession because there is no straightforward way to do that.  Please make sure your accession ID is valid and correct.

The workflow also requires `${params.original_submission_outdir}` which should point to your original NCBI submission for these samples.
It is expecting that the original submission was made with Tostadas, so it wants a path ending in `submission_outputs` (`${params.submission_outdir}`) here.  
It's going to look through the batch folders for `biosample/submission.xml` to validate that certain fields are unchanged, as required by NCBI.

It also expects to find the batch_summary.json file from the original submission (in validation_outputs/batched_tsvs) and it uses this file to recreate the same batches as in the original submission.
It has to do this in order to validate that certain metadata are unchanged from the original submission, and to update the original submission with the PrimaryId.

The workflow runs METADATA_VALIDATION, CHECK_VALIDATION_ERRORS, and WRITE_VALIDATED_FULL_TSV as in BIOSAMPLE_AND_SRA workflow.  After that, it diverges as follows:

1. REBATCH_METADATA: Process that recreates the original batches to match the data as `${params.original_submission_outdir}`.
        Input: `$params.outdir/$params.metadata_basename/$final_submission_outdir/validated_metadata_all_samples.tsv` (WRITE_VALIDATED_FULL_TSV output), 
                `${params.original_submission_outdir}/../${params.validation_outdir}/batched_tsvs/batch_summary.json`
        Output: paths to the rebatched json and tsv files.

2. UPDATE_SUBMISSION: Process that updates the biosample submission.
        Input: a tuple containing the list of samples and corresponding batch_id, and the submission config file, the original submission directory, and the submission config file.
        Output: a tuple containing the batch directory, and a prep_submission log file.


## Known issues and idiosyncracies

1. The pipeline doesn't fetch Genbank accession IDs, but it could if they are available.  Doing so will require some optional handling for downstream report csv and updated metadata file generation.

2. The update_submissions workflow was added very late and I didn't have time to rigorously test it. More testing should be done, and additional nf-tests created for the additional processes.

3. I believe a specific line needs to be added to the GenBank XML file (where appropriate) indicating NCBI should perform annotations.  So the pipeline may be to be adjusted such that if there is no gff file provided in the channel, this line gets added to the XML file for appropriate GenBank submissions (i.e., only those that are submitted via ftp). Also, GenBank sqn file needs to be rigorously validated (sars and flu haven't been tested at all).
   
4. Need some robust checking for the vadr_models_dir vs. species (see notes under annotation).

5. For update_submission, the metadata file is not being copied to the workDir, it's being referenced from its own workDir.  This is not ideal Nextflow coding, and should be changed so that it copies the actual file.  
   It's happening because of the channel construction (which is being made from a json file in REBATCH_METADATA process). I think this can be pretty easily modified to just output the channel.

6. Outstanding to-do notes in `submission_helper.py`: 
        Line 963: These are hard-coded but probably need to be controlled during GENBANK_VALIDATION somehow.
        Line 982: This is not an issue, it's actually more of a reminder to me that the way Biosample and SRA XML files get made is different from Genbank (they are called differently in submission_prep.py). 
        Line 1273: We never did figure out if locus tag prefix can be set automatically. I think it has to be assigned before, which means it must be specified in `${params.bakta_locus_tag}`