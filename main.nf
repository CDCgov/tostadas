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
include { MPXV_MAIN } from "$projectDir/workflows/mpxv.nf"


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            DEFAULT WORKFLOW FOR PIPELINE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
workflow {
    // main workflow for mpxv pipeline
    MPXV_MAIN ()
}


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                        SPECIFIED FULL WORKFLOW FOR PIPELINE
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow MPXV {
    MPXV_MAIN ()
}


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            ENTRYPOINTS FOR MPXV WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// include necessary processes 
include { VALIDATE_PARAMS } from "$projectDir/modules/general_util/validate_params/main"
include { CLEANUP_FILES } from "$projectDir/modules/general_util/cleanup_files/main"
// include necessary subworkflows
include { RUN_VALIDATION } from "$projectDir/subworkflows/entrypoints/validation_entry"
include { RUN_LIFTOFF } from "$projectDir/subworkflows/entrypoints/liftoff_entry"
include { RUN_VADR } from "$projectDir/subworkflows/entrypoints/vadr_entry"
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
        RUN_VALIDATION ()
}

workflow only_liftoff {
    main: 
        // run subworkflow for liftoff entrypoint
        RUN_LIFTOFF ()
}

workflow only_vadr {
    main: 
        // run subworkflow for vadr entrypoint
        RUN_VADR ()
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