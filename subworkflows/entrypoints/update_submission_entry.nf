#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            ONLY UPDATE SUBMISSION ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { CHECK_FILES                                       } from "../../modules/general_util/check_files/main"
include { CHECKS_4_SUBMISSION_ENTRY                         } from "./submission_entry_check"
include { UPDATE_SUBMISSION                                 } from "../../modules/update_submission/main"


workflow RUN_UPDATE_SUBMISSION {
    main:

        /*
        // call the check specific to submission
        CHECKS_4_SUBMISSION_ENTRY (
            'only_update_submission'
        )
        */

        /*
        // get the parameter paths into proper format 
        PREP_UPDATE_SUBMISSION_ENTRY ( 
            CHECKS_4_SUBMISSION_ENTRY.out,
            true, 
            params.processed_samples
        )
        */

        CHECK_FILES (
            'dummy utility signal',
            false,
            false,
            true,
            params.processed_samples
        )

        // TODO: need to have an output for a directory containing all of the outputs 
        // call the update submission portion only
        UPDATE_SUBMISSION (
            'dummy wait signal',
            params.submission_config,
            CHECK_FILES.out.samples.sort().flatten(),
            ''
        )
}