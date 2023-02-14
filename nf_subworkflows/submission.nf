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
        meta_files
        lifted_fasta_files
        lifted_gff_files
        entry_flag

    main:
    
        //SUBMISSION ( meta_files, lifted_fasta_files, lifted_gff_files, entry_flag )

        GET_WAIT_TIME ( true, meta_files.collect(), entry_flag )

        WAIT ( GET_WAIT_TIME.out )

        //UPDATE_SUBMISSION ( WAIT.out )
}
