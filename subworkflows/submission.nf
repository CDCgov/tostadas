#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { SUBMISSION                                    } from '../modules/submission/main'
include { UPDATE_SUBMISSION                             } from '../modules/update_submission/main'
include { WAIT                                          } from '../modules/general_util/wait/main'
include { MERGE_UPLOAD_LOG                              } from "../modules/general_util/merge_upload_log/main"


workflow LIFTOFF_SUBMISSION {
    take:
        ch_submission_files
        submission_config
        req_col_config
        wait_time
        //

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( ch_submission_files, submission_config, req_col_config, 'liftoff' )

        // actual process to initiate wait 
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        // process for updating the submitted samples
        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, 'liftoff' )

        // combine the different upload_log csv files together 
        MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), 'liftoff' )
}

workflow VADR_SUBMISSION {
    take:
        ch_submission_files
        submission_config
        req_col_config
        wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( ch_submission_files, submission_config, req_col_config, 'vadr' )

        // actual process to initiate wait 
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        // process for updating the submitted samples
        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, 'vadr' )

        // combine the different upload_log csv files together 
        MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), 'vadr' )
}

workflow BAKTA_SUBMISSION {
    take:
         ch_submission_files
         submission_config
         req_col_config
         wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( ch_submission_files, submission_config, req_col_config, 'bakta' )

        // actual process to initiate wait
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        // process for updating the submitted samples
        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, 'bakta' )

        // combine the different upload_log csv files together
        MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), 'bakta' )
}

workflow REPEAT_MASKER_LIFTOFF_SUBMISSION {
    take:
        ch_submission_files
        submission_config
        req_col_config
        wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( ch_submission_files, submission_config, req_col_config, 'repeatmasker_liftoff' )

        // actual process to initiate wait 
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        // process for updating the submitted samples
        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, 'repeatmasker_liftoff' )

        // combine the different upload_log csv files together 
        MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), 'repeatmasker_liftoff' )
}

workflow GENERAL_SUBMISSION {
    take:
        general_submission_ch
        submission_config
        req_col_config
        wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( general_submission_ch, submission_config, req_col_config, '' )

        // actual process to initiate wait 
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        // process for updating the submitted samples
        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, '' )

        // combine the different upload_log csv files together 
        MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), '' )
}
