#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            CHECKS FOR SUBMISSION ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { GENERAL_SUBMISSION_ENTRY_CHECK } from '../nf_modules/utility_mods'
include { ONLY_INITIAL_SUBMISSION_ENTRY_CHECK } from '../nf_modules/utility_mods'
include { ONLY_UPDATE_SUBMISSION_ENTRY_CHECK } from '../nf_modules/utility_mods'

workflow CHECKS_4_SUBMISSION_ENTRY {

    take:
        which_entrypoint 

    main: 
        GENERAL_SUBMISSION_ENTRY_CHECK() 

        if ( which_entrypoint == 'only_submission' || which_entrypoint == 'only_initial_submission' ) {
            ONLY_INITIAL_SUBMISSION_ENTRY_CHECK()
        }

        if ( which_entrypoint == 'only_submission' || which_entrypoint == 'only_update_submission' ) {
            ONLY_UPDATE_SUBMISSION_ENTRY_CHECK()
        }

    emit:
        true
}