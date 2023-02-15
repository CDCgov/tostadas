#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { SUBMISSION } from '../nf_modules/main_mods'
include { UPDATE_SUBMISSION } from '../nf_modules/main_mods'
include { WAIT } from '../nf_modules/utility_mods'
include { GET_WAIT_TIME } from '../nf_modules/utility_mods'
include { CHECK_CONFIG } from "$projectDir/nf_modules/utility_mods"

workflow RUN_SUBMISSION {
    take:
        meta_signal 
        liftoff_signal
        meta_files
        lifted_fasta_files
        lifted_gff_files
        entry_flag
        submission_config

    main:

        // pre submission process + get wait time (parallel)
        CHECK_CONFIG ( meta_signal, liftoff_signal, params.submission_config )
        GET_WAIT_TIME ( meta_signal, liftoff_signal, meta_files.collect() )

        // submit the files to database of choice (after fixing config and getting wait time)
        // SUBMISSION ( meta_files, lifted_fasta_files, lifted_gff_files, entry_flag, CHECK_CONFIG.out )

        // actual process to initiate wait 
        WAIT ( 'duumy submission output', GET_WAIT_TIME.out )

        //UPDATE_SUBMISSION ( WAIT.out )
}
