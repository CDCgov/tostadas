#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { SUBMISSION } from '../modules/submission/main'
include { UPDATE_SUBMISSION } from '../modules/update_submission/main'
include { WAIT } from '../modules/general_util/wait/main'

workflow LIFTOFF_SUBMISSION {
    take:
        meta_files
        liftoff_fasta_files
        liftoff_gff_files
        entry_flag
        submission_config
        req_col_config
        wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( meta_files, liftoff_fasta_files, liftoff_gff_files, entry_flag, submission_config, req_col_config, 'liftoff' )

        // actual process to initiate wait 
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, 'liftoff' )
}

workflow VADR_SUBMISSION {
    take:
        meta_files
        vadr_fasta_files
        vadr_gff_files
        entry_flag
        submission_config
        req_col_config
        wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( meta_files, vadr_fasta_files, vadr_gff_files, entry_flag, submission_config, req_col_config, 'vadr' )

        // actual process to initiate wait 
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, 'vadr' )
}

workflow ENTRY_SUBMISSION {
    take:
        entry_meta_files
        entry_fasta_files
        entry_gff_files
        entry_flag
        submission_config
        req_col_config
        wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( entry_meta_files, entry_fasta_files, entry_gff_files, entry_flag, submission_config, req_col_config, '' )

        // actual process to initiate wait 
        WAIT ( SUBMISSION.out.submission_files.collect(), wait_time )

        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, '' )
}