#!/usr/bin/env nextflow
nextflow.enable.dsl=2

def helpMessage() {
  log.info """
        Usage:
        The general command for running nextflow with values set in config:
        nextflow run main.nf

        To pass in arguments and override params in config:
        nextflow run main.nf --<param name> <param value>

        To access a specific sub-workflow via entrypoint:
        nextflow run main.nf -entry <name of sub workflow>

        Mandatory Arguments (either set in config of passed through command line):
         --meta_path                            Path to the metadata file (accepts string)
         --fasta_path                           Path to the fasta file (accepts string)
         --ref_fasta_path                       Path to the reference fasta file (accepts string)
         --ref_gff_path                         Path to the reference gff file (accepts string)

         --liftoff_script                       Path to the liftoff_submission.py script (accepts string)
         --validation_script                    Path to the validate_metadata.py script (accepts string)
         --submission_script                    Path to the submission.py script (accepts string)

         --run_docker                           Flag for whether to run docker or not (accepts bool: true/false)
         --run_submission                       Flag for whether to run submission portion or not (accepts bool: true/false)
         --cleanup                              Flag for whether to run the cleanup process (accepts bool: true/false)

         --clear_nextflow_log                   Defines the cleanup process further: whether to clear the nextflow log files (accepts bool: true/false)
         --clear_work_dir                       Defines the cleanup process further: whether to clear the work directory (accepts bool: true/false)
         --clear_conda_env                      Defines the cleanup process further: whether to clear the conda environment (accepts bool: true/false)
         --clear_nf_results                     Defines the cleanup process further: whether to clear the previous generated results (accepts bool: true/false)

         --env_yml                              Path to the .yml file for building the cond environment from (accepts string)
         --output_dir                           Name of the output directory for the results from nextflow (accepts string)
         --overwrite_output                     Flag for whether to overwrite the existing files in the output directory (accepts bool: true/false)
         --final_liftoff_output_dir             Name of the output directory for the annotation pipeline (accepts string)
         --val_output_dir                       Name of the output directory for the validation pipeline (accepts string)

         --val_date_format_flag                 Flag corresponding to format for date, possible options are 's', 'o', 'v'. Please consult documentation for more info.
         --val_keep_pi                          Flag to keep personal information or not (accepts bool: true/false)
         --val_meta_file_name                   Name of the metadata file name (without extension) (accepts string)

         --lift_print_version_exit              Flag to print out the version of liftoff and exit (accepts bool: true/false)
         --lift_print_help_exit                 Flag to print out the help message for liftoff and exit (accepts bool: true/false)
         --lift_parallel_processes              Number of parallel processes to run when running liftoff (accepts integer)
         --lift_delete_temp_files               Flag to delete temporary files generated during annotation (accepts bool: true/false)
         --lift_coverage_threshold              Designate a feature mapped only if it aligns with coverage ≥A
         --lift_child_feature_align_threshold   Designate a feature mapped only if its child features usually exons/CDS align with sequence identity ≥S
         --lift_unmapped_features_file_name     Name of unmapped features file name
         --lift_copy_threshold                  Minimum sequence identity in exons/CDS for which a gene is considered a copy; must be greater than -s; default is 1.0
         --lift_distance_scaling_factor         Alignment nodes separated by more than a factor of D in the target genome will not be connected in the graph; by default D=2.0
         --lift_flank                           Amount of flanking sequence to align as a fraction [0.0-1.0] of gene length. This can improve gene alignment where gene structure differs between target and reference; by default F=0.0
         --lift_overlap                         Maximum fraction [0.0-1.0] of overlap allowed by 2 features; by default O=0.1
         --lift_mismatch                        Mismatch penalty in exons when finding best mapping; by default M=2
         --lift_gap_open                        Gap open penalty in exons when finding best mapping; by default GO=2
         --lift_gap_extend                      Gap extend penalty in exons when finding best mapping; by default GE=1
         --lift_infer_transcripts               Use if annotation file only includes exon/CDS features and does not include transcripts/mRNA
         --lift_copies                          Look for extra gene copies in the target genome
         --lift_minimap_path                    Path to minimap if you did not use conda or pip
         --lift_feature_database_name           Name of the feature database, if none, then will use ref gff path to construct one

         --submission_only_meta                 Path to the validated metadata directory if calling submission entrypoint (accepts string)
         --submission_only_gff                  Path to the reformatted gff directory if calling submission entrypoint (accepts string)
         --submission_only_fasta                Path to the split fasta files directory if calling submission entrypoint (accepts string)
         --submission_config                    Path to the configuration file used for the submission process (accepts string)

       Optional arguments:
        --submission_wait_time                  Overwrites the default calculation of (3 * 60 * num samples) in seconds for wait time after initial submission
        --help                                  Flag to call in help statements mentioned in this block
        """
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                INITIALIZE VARS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// channels for data files
def get_channels() {
    try {
        meta_path_ch = Channel.fromPath(params.meta_path)
        fasta_path_ch = Channel.fromPath(params.fasta_path)
        ref_fasta_path_ch = Channel.fromPath(params.ref_fasta_path)
        ref_gff_path_ch = Channel.fromPath(params.ref_gff_path)
        return [
            'meta': meta_path_ch, 
            'fasta': fasta_path_ch, 
            'ref_fasta': ref_fasta_path_ch, 
            'ref_gff': ref_gff_path_ch
        ]
    } catch (Exception e) {
        throw new Exception("\nERROR: Could not get channel from meta_path or fasta_path or ref_fasta_path or ref_gff_path. Please make sure that a params set is selected either using -profile <standard/test> or -params-file <standard/test .yml/.json> AND these params are specified")
    }
}


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                         GET NECESSARY MODULES OR SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// get the utility processes
include { VALIDATE_PARAMS } from "$projectDir/nf_modules/utility_mods"
include { CLEANUP_FILES } from "$projectDir/nf_modules/utility_mods"
include { WAIT } from "$projectDir/nf_modules/utility_mods"
include { SUBMISSION_ENTRY_CHECK } from "$projectDir/nf_modules/utility_mods"

// get the main processes
include { METADATA_VALIDATION } from "$projectDir/nf_modules/main_mods"
include { LIFTOFF } from "$projectDir/nf_modules/main_mods"
include { SUBMISSION } from "$projectDir/nf_modules/main_mods"
include { UPDATE_SUBMISSION } from "$projectDir/nf_modules/main_mods"

// get the subworkflows
include { RUN_SUBMISSION } from "$projectDir/nf_subworkflows/submission"
include { RUN_UTILITY } from "$projectDir/nf_subworkflows/utility"

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
workflow {

    // check if help parameter is set
    if ( params.help == true ) {
        helpMessage()
        exit 0
    }

    // check parameters + cleanup the files 
    RUN_UTILITY()

    // run validation script
    if ( params.run_submission == true ) {
        with_submission( RUN_UTILITY.out )
    } else if ( params.run_submission == false ) {
        without_submission( RUN_UTILITY.out )
    } else {
        println ("Running with submission since a run_submission flag was not specified")
        with_submission()
    }
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    SUB WORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow with_submission {
    take:
        cleanup_signal
    main:
        // get channels 
        channels = get_channels()

        // run metadata validation
        METADATA_VALIDATION (  cleanup_signal, channels['meta'], channels['fasta'] )

        // run liftoff (in parallel)
        LIFTOFF ( cleanup_signal, channels['meta'], channels['fasta'], channels['ref_fasta'], channels['ref_gff'] )

        // run post annotation checks
        RUN_SUBMISSION ( LIFTOFF.out[1], METADATA_VALIDATION.out[1], false,
            "$params.output_dir/$params.val_output_dir",
            "$params.output_dir/$params.final_liftoff_output_dir",
            "$params.output_dir/$params.final_liftoff_output_dir"
        )
}

workflow without_submission {
    take:
        cleanup_signal
    main:
        // get channels 
        channels = get_channels()

        // run metadata validation
        METADATA_VALIDATION ( cleanup_signal, channels['meta'], channels['fasta'] )

        // run liftoff (in parallel)
        LIFTOFF ( cleanup_signal, channels['meta'], channels['fasta'], channels['ref_fasta'], channels['ref_gff'] )
}

workflow only_validate_params {
    main:
        VALIDATE_PARAMS()
}

workflow only_cleanup_files {
    main:
        CLEANUP_FILES ( 'dummy validate params signal' )
}

workflow only_validation {
    main:
        // check parameters + cleanup the files 
        RUN_UTILITY()

        // get channels 
        channels = get_channels()

        // run metadata validation
        METADATA_VALIDATION ( RUN_UTILITY.out, channels['meta'], channels['fasta'] )
}

workflow only_annotation {
    main:
        // check parameters + cleanup the files 
        RUN_UTILITY()

        // get channels 
        channels = get_channels()

        // run annotation on files
        LIFTOFF ( RUN_UTILITY.out, channels['meta'], channels['fasta'], channels['ref_fasta'], channels['ref_gff'] )
}

workflow only_submission {
    main:
        // check that certain paths are specified
        SUBMISSION_ENTRY_CHECK ( )

        // call the submission workflow
        RUN_SUBMISSION (
            SUBMISSION_ENTRY_CHECK.out,
            'dummy signal value', 
            true,
            params.submission_only_meta,
            params.submission_only_fasta,
            params.submission_only_gff
        )
}

workflow only_initial_submission {
    main:
        // call the check specific to submission
        SUBMISSION_ENTRY_CHECK ( )

        // call the initial submission portion only
        SUBMISSION (
            SUBMISSION_ENTRY_CHECK.out,
            'dummy signal value', 
            params.submission_only_meta,
            params.submission_only_fasta,
            params.submission_only_gff,
            true
        )
}

workflow only_update_submission {
    main:
        // call the check specific to submission
        SUBMISSION_ENTRY_CHECK ( )

        // call the update submission portion only
        UPDATE_SUBMISSION (
            SUBMISSION_ENTRY_CHECK.out
        )
}