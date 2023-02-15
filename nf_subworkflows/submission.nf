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
    
        //SUBMISSION ( meta_files, lifted_fasta_files, lifted_gff_files, entry_flag, submission_config )

        GET_WAIT_TIME ( meta_signal, liftoff_signal, meta_files.collect() )

        WAIT ( GET_WAIT_TIME.out )

        //UPDATE_SUBMISSION ( WAIT.out )
}
