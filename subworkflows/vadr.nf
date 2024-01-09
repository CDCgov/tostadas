#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            VADR SUBWORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { VADR                                              } from "../modules/vadr_annotation/main"
include { VADR_POST_CLEANUP                                 } from "../modules/post_vadr_annotation/main"


workflow RUN_VADR {
    take:
        utility_signal
        fasta_files

    main:
        // run vadr processes
        VADR (
            utility_signal, 
            fasta_files,
            params.vadr_models_dir
        )

        VADR_POST_CLEANUP (
            VADR.out.vadr_outputs,
            params.meta_path,
            fasta_files
        )
    
    emit:
        VADR_POST_CLEANUP.out.gff
}

