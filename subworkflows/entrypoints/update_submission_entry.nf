#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            ONLY UPDATE SUBMISSION ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { CHECKS_4_SUBMISSION_ENTRY                         } from "./submission_entry_check"
include { PREP_UPDATE_SUBMISSION_ENTRY                      } from "../../modules/submission_entrypoint/prep_update_sub_entry/main"
include { UPDATE_SUBMISSION                                 } from "../../modules/update_submission/main"


workflow RUN_UPDATE_SUBMISSION {
    main:

        // call the check specific to submission
        CHECKS_4_SUBMISSION_ENTRY (
            'only_update_submission'
        )

        // get the parameter paths into proper format 
        PREP_UPDATE_SUBMISSION_ENTRY ( 
            CHECKS_4_SUBMISSION_ENTRY.out,
            true, 
            params.processed_samples
        )

        // call the update submission portion only
        UPDATE_SUBMISSION (
            'dummy wait signal',
            params.submission_config,
            PREP_UPDATE_SUBMISSION_ENTRY.out.samples.flatten(),
            ''
        )
}