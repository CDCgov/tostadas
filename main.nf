#!/usr/bin/env nextflow

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                CODEBASE INFORMATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    
    Github  :   https://github.com/CDCgov/tostadas

----------------------------------------------------------------------------------------
*/

nextflow.enable.dsl=2
params.projectDir = './'


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                               IMPORT NECESSARY WORKFLOWS 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { MAIN_WORKFLOW } from "$projectDir/workflows/main.nf"


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            DEFAULT WORKFLOW FOR PIPELINE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
workflow {
    // main workflow for the pipeline
    MAIN_WORKFLOW()
}


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                        SPECIFIED FULL WORKFLOW FOR PIPELINE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow MAIN {
    MAIN_WORKFLOW()
}


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            ENTRYPOINTS FOR MPXV WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// include necessary processes 
include { VALIDATE_PARAMS } from "$projectDir/modules/general_util/validate_params/main"
include { CLEANUP_FILES } from "$projectDir/modules/general_util/cleanup_files/main"
include { INITIALIZE_FILES } from "$projectDir/modules/general_util/initialize_files/main"
include { LIFTOFF } from "$projectDir/modules/liftoff_annotation/main"
include { METADATA_VALIDATION } from "$projectDir/modules/metadata_validation/main"

// include necessary subworkflows
include { RUN_REPEATMASKER_LIFTOFF } from "$projectDir/subworkflows/repeatmasker_liftoff"
include { RUN_VADR } from "$projectDir/subworkflows/vadr"
include { RUN_SUBMISSION } from "$projectDir/subworkflows/entrypoints/submission_entry"
include { RUN_INITIAL_SUBMISSION } from "$projectDir/subworkflows/entrypoints/initial_submission_entry"
include { RUN_UPDATE_SUBMISSION } from "$projectDir/subworkflows/entrypoints/update_submission_entry"

workflow only_validate_params {
    main:
        // run the process for validating general parameters
        VALIDATE_PARAMS ()
}

workflow only_cleanup_files {
    main:
        // run process for cleaning up files 
        CLEANUP_FILES (
            'dummy validate params signal' 
        )
}

workflow only_validation {
    main: 
        // run subworkflow for validation entrypoint
        METADATA_VALIDATION (
            'dummy utility signal',
            params.meta_path
        )
}

workflow only_liftoff {
    main: 
        // initialize the fasta files first 
        INITIALIZE_FILES ( 'dummy utility signal' )

        // run process for liftoff
        LIFTOFF (
            params.meta_path, 
            INITIALIZE_FILES.out.fasta_dir, 
            params.ref_fasta_path, 
            params.ref_gff_path 
        )
}

workflow only_repeatmasker_liftoff {
    main: 
        // run subworkflow for repeatmasker liftoff entrypoint
        RUN_REPEATMASKER_LIFTOFF ( 'dummy utility signal' )
}

workflow only_vadr {
    main: 
        // initialize the fasta files first 
        INITIALIZE_FILES ( 'dummy utility signal' )
        
        // run subworkflow for vadr 
        RUN_VADR (
            'dummy utility signal',
            INITIALIZE_FILES.out.fasta_files.sort().flatten()
        )
}

workflow only_submission {
    main: 
        // run subworkflow for submission entrypoint
        RUN_SUBMISSION ()
}

workflow only_initial_submission {
    main:
        // run subworkflow for initial submission entrypoint
        RUN_INITIAL_SUBMISSION ()
}

workflow only_update_submission {
    main:
        // run subworkflow for update submission entrypoint
        RUN_UPDATE_SUBMISSION ()
}