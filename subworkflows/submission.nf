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

workflow REPEAT_MASKER_LIFTOFF_SUBMISSION {
    take:
        // tuple val(meta_files), path(fasta), path(gff)
        meta_files
        fasta
        gff
        submission_config
        req_col_config
        wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( meta_files, fasta, gff, submission_config, req_col_config, 'liftoff' )

        // actual process to initiate wait 
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        // process for updating the submitted samples
        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, 'repeatmasker_liftoff', SUBMISSION.out.sample_name )

        // combine the different upload_log csv files together 
        MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), 'repeatmasker_liftoff' )
}


workflow LIFTOFF_SUBMISSION {
    take:
        meta_files
        liftoff_fasta_files
        liftoff_gff_files
        submission_config
        req_col_config
        wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( meta_files, liftoff_fasta_files, liftoff_gff_files, submission_config, req_col_config, 'liftoff' )

        // actual process to initiate wait 
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        // process for updating the submitted samples
        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, 'liftoff', SUBMISSION.out.sample_name )

        // combine the different upload_log csv files together 
        MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), 'liftoff' )
}

workflow VADR_SUBMISSION {
    take:
        meta_files
        vadr_fasta_files
        vadr_gff_files
        submission_config
        req_col_config
        wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( meta_files, vadr_fasta_files, vadr_gff_files, submission_config, req_col_config, 'vadr' )

        // actual process to initiate wait 
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        // process for updating the submitted samples
        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, 'vadr', SUBMISSION.out.sample_name )

        // combine the different upload_log csv files together 
        MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), 'vadr' )
}

workflow BAKTA_SUBMISSION {
    take:
         meta_files
         bakta_fasta_files
         bakta_gff_files
         submission_config
         req_col_config
         wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( meta_files, bakta_fasta_files, bakta_gff_files, submission_config, req_col_config, 'bakta' )

        // actual process to initiate wait
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        // process for updating the submitted samples
        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, 'bakta', SUBMISSION.out.sample_name )

        // combine the different upload_log csv files together
        MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), 'bakta' )
}

workflow GENERAL_SUBMISSION {
    take:
        meta_files
        fasta_files
        gff_files
        submission_config
        req_col_config
        wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( meta_files, fasta_files, gff_files, submission_config, req_col_config, '' )

        // actual process to initiate wait 
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        // process for updating the submitted samples
        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, '', SUBMISSION.out.sample_name )

        // combine the different upload_log csv files together 
        MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), '' )
}
