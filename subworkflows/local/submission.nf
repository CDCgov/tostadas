#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { SUBMISSION_FULL                               } from '../../modules/local/initial_submission/main_full'
include { SUBMISSION_SRA                                } from '../../modules/local/initial_submission/main_sra'
include { SUBMISSION_GENBANK                            } from '../../modules/local/initial_submission/main_genbank'
include { UPDATE_SUBMISSION                             } from '../../modules/local/update_submission/main'
include { WAIT                                          } from '../../modules/local/general_util/wait/main'
include { MERGE_UPLOAD_LOG                              } from "../../modules/local/general_util/merge_upload_log/main"

workflow INITIAL_SUBMISSION {
    take:
        submission_ch
        fastq_ch
        submission_config
        req_col_config
        wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        if ( params.genbank && params.sra ){ // genbank and sra
            // submit the files to database of choice (after fixing config and getting wait time)
            SUBMISSION_FULL ( submission_ch, fastq_ch, submission_config, req_col_config, '' )
            
            // actual process to initiate wait 
            WAIT ( SUBMISSION_FULL.out.submission_files.collect(), wait_time )

            // process for updating the submitted samples
            UPDATE_SUBMISSION (  WAIT.out, submission_config, SUBMISSION_FULL.out.submission_files, SUBMISSION_FULL.out.submission_log, '' )

            // combine the different upload_log csv files together 
            MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), '' )
        }

        if ( !params.genbank && params.sra ){ //only sra
            SUBMISSION_SRA ( submission_ch, fastq_ch, submission_config, req_col_config, '' )
            // actual process to initiate wait 
            WAIT ( SUBMISSION_SRA.out.submission_files.collect(), wait_time )

            // process for updating the submitted samples
            UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION_SRA.out.submission_files, SUBMISSION_SRA.out.submission_log, '' )

            // combine the different upload_log csv files together 
            MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), '' )
        }

        if ( params.genbank && !params.sra ){ //only genbank, fastq_ch can be empty
        // submit the files to database of choice (after fixing config and getting wait time)
            SUBMISSION_GENBANK ( submission_ch, fastq_ch, submission_config, req_col_config, '' )
            
            // actual process to initiate wait 
            WAIT ( SUBMISSION_GENBANK.out.submission_files.collect(), wait_time )

            // process for updating the submitted samples
            UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION_GENBANK.out.submission_files, SUBMISSION_GENBANK.out.submission_log, '' )

            // combine the different upload_log csv files together 
            MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), '' )
        }

        //ToDo add GISAID module
        
}
