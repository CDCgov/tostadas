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
include { CHECK_FILES   } from "$projectDir/modules/general_util/check_files/main"
include { LIFTOFF } from "$projectDir/modules/liftoff_annotation/main"
include { METADATA_VALIDATION } from "$projectDir/modules/metadata_validation/main"

// include necessary subworkflows
include { RUN_REPEATMASKER_LIFTOFF } from "$projectDir/subworkflows/repeatmasker_liftoff"
include { RUN_VADR } from "$projectDir/subworkflows/vadr"
include { RUN_SUBMISSION } from "$projectDir/subworkflows/entrypoints/submission_entry"
include { RUN_INITIAL_SUBMISSION } from "$projectDir/subworkflows/entrypoints/initial_submission_entry"
include { RUN_UPDATE_SUBMISSION } from "$projectDir/subworkflows/entrypoints/update_submission_entry"
include { RUN_BAKTA } from "$projectDir/subworkflows/entrypoints/bakta_entry.nf"
include { RUN_VALIDATION_AND_SUBMISSION } from "$projectDir/subworkflows/entrypoints/no_annotation"

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

// TODO: need to create separate process for FASTA related /  entry annotation (figure this out)
        
workflow only_liftoff {
    main: 
        // run process for liftoff
        LIFTOFF (
            'dummy utility signal',
            params.meta_path, 
            params.fasta_path, 
            params.ref_fasta_path, 
            params.ref_gff_path 
        )
}

workflow only_repeatmasker_liftoff {
    main: 
        fastaCh = Channel.fromPath("$params.fasta_path/*.{fasta, fastq}")
        // run subworkflow for repeatmasker liftoff entrypoint
        RUN_REPEATMASKER_LIFTOFF (
            'dummy utility signal', 
            fastaCh 
        )
}

workflow only_vadr {
    main: 
        fastaCh = Channel.fromPath("$params.fasta_path/*.{fasta, fastq}")
        // run subworkflow for vadr 
        RUN_VADR (
            'dummy utility signal',
            fastaCh
        )
}

workflow only_bakta {
    main:
        fastaCh = Channel.fromPath("$params.fasta_path/*.fasta")
        RUN_BAKTA (
            'dummy utility signal',
            fastaCh
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

workflow only_validation_and_submission {
    main:
        // calls subworkflow to run only validation and submission
        RUN_VALIDATION_AND_SUBMISSION (
            'dummy utility signal',
            false
        )
}

workflow only_validation_and_initial_submission {
    main:
        // calls subworkflow to run only validation and submission
        RUN_VALIDATION_AND_SUBMISSION (
            'dummy utility signal',
            true
        )
}