#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { SUBMISSION                                    } from '../../modules/local/initial_submission/main'
include { FETCH_SUBMISSION                              } from '../../modules/local/fetch_submission/main'
include { UPDATE_SUBMISSION                             } from '../../modules/local/update_submission/main'
include { WAIT                                          } from '../../modules/local/general_util/wait/main'
include { MERGE_UPLOAD_LOG                              } from "../../modules/local/general_util/merge_upload_log/main"

workflow INITIAL_SUBMISSION {
    take:
        submission_ch // meta.id, tsv, fasta, fastq1, fastq2, gff
        submission_config
        wait_time
    
    main:
        if ( params.update_submission == false ) {
            // submit the files to database of choice
            SUBMISSION ( submission_ch, submission_config )
                
            // actual process to initiate wait 
            WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

            // try to fetch & parse the report.xml
            // todo: need to incorporate WAIT.out somehow
            // todo: this maybe doesn't need to take all the inputs from submission (or maybe doesn't need to be a separate module)
            FETCH_SUBMISSION ( WAIT.out, submission_ch, submission_config )
        }

        // if params.update_submission is true, update an existing submission
        else if ( params.update_submission == true ) {
            // process for updating the submitted samples
            // todo: update to take the csv output from FETCH_SUBMISSION
            UPDATE_SUBMISSION ( submission_ch, submission_config )

            // try to fetch & parse the report.xml
            // todo: need to incorporate WAIT.out somehow
            FETCH_SUBMISSION ( WAIT.out, submission_ch, submission_config )
        }
        
    emit:
        submission_files = SUBMISSION.out.submission_files
        //submission_log = SUBMISSION.out.submission_log

        //to do: add GISAID module
}
