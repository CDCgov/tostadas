#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { SUBMISSION                                    } from '../../modules/local/submission/main_sra'
include { UPDATE_SUBMISSION                             } from '../../modules/local/update_submission/main_sra'
include { WAIT                                          } from '../../modules/local/general_util/wait/main'
include { MERGE_UPLOAD_LOG                              } from "../../modules/local/general_util/merge_upload_log/main"

workflow SRA_SUBMISSION {
    take:
        submission_ch
        submission_config
        req_col_config
        wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( submission_ch, submission_config, req_col_config, '' )

        // actual process to initiate wait 
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        // process for updating the submitted samples
        UPDATE_SUBMISSION ( WAIT.out, submission_ch, submission_config, SUBMISSION.out.submission_files, '' )

        // combine the different upload_log csv files together 
        MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), '' )
}
