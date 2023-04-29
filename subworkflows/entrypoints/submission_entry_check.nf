#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            CHECKS FOR SUBMISSION ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { GENERAL_SUBMISSION_ENTRY_CHECK } from '../../modules/submission_entrypoint/gen_sub_entry_check/main'
include { ONLY_INITIAL_SUBMISSION_ENTRY_CHECK } from '../../modules/submission_entrypoint/initial_sub_entry_check/main'
include { ONLY_UPDATE_SUBMISSION_ENTRY_CHECK } from '../../modules/submission_entrypoint/update_sub_entry_check/main'

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