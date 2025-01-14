#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { SUBMISSION                                    } from '../../modules/local/initial_submission/main'
//include { UPDATE_SUBMISSION                             } from '../../modules/local/update_submission/main'
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
            SUBMISSION ( submission_ch, submission_config, Channel.of("submit") )
                
            // actual process to initiate wait 
            WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

            // try to fetch & parse the report.xml
            // todo: need to incorporate WAIT.out somehow
            SUBMISSION ( submission_ch, submission_config, Channel.of("fetch") )
        }

        // if params.update_submission is true, update an existing submission
        else if ( params.update_submission == true ) {
             // process for updating the submitted samples
            SUBMISSION ( submission_ch, submission_config, Channel.of("update") )

            // try to fetch & parse the report.xml
            // todo: need to incorporate WAIT.out somehow
            SUBMISSION ( submission_ch, submission_config, Channel.of("fetch") )
        }
        
    emit:
        submission_files = UPDATE_SUBMISSION.out.submission_files
        //submission_log = UPDATE_SUBMISSION.out.submission_log

        //to do: add GISAID module
}
