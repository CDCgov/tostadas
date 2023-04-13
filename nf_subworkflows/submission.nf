#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { SUBMISSION } from '../nf_modules/main_mods'
include { UPDATE_SUBMISSION } from '../nf_modules/main_mods'
include { WAIT } from '../nf_modules/utility_mods'

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

        UPDATE_SUBMISSION ( WAIT.out, submission_config, SUBMISSION.out.submission_files, 'vadr', false )
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