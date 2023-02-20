#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { SUBMISSION } from '../nf_modules/main_mods'
include { UPDATE_SUBMISSION } from '../nf_modules/main_mods'
include { WAIT } from '../nf_modules/utility_mods'

workflow RUN_SUBMISSION {
    take:
        meta_signal 
        liftoff_signal
        meta_files
        lifted_fasta_files
        lifted_gff_files
        entry_flag
        submission_config
        req_col_config
        wait_time

    main:
        // submit the files to database of choice (after fixing config and getting wait time)
        SUBMISSION ( meta_files, lifted_fasta_files, lifted_gff_files, entry_flag, submission_config, req_col_config )

        // actual process to initiate wait 
        WAIT ( SUBMISSION.out.collect(), wait_time )

        UPDATE_SUBMISSION ( WAIT.out, submission_config, meta_files )
}
