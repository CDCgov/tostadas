#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            REPEAT MASKER & LIFTOFF ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { REPEATMASKER                                      } from "../../modules/local/repeatmasker_annotation/main"
include { LIFTOFF_CLI                                       } from "../../modules/local/liftoff_cli_annotation/main"
include { CONCAT_GFFS                                       } from "../../modules/local/concat_gffs/main"

workflow REPEATMASKER_LIFTOFF {

    take:
        utility_signal
        fasta

    main:
        // run repeatmasker annotation on files
        REPEATMASKER (
           utility_signal,
           fasta,
           params.repeat_library
        )
        // run liftoff annotation on files
        LIFTOFF_CLI ( 
            utility_signal,
            fasta,
            params.ref_fasta_path, 
            params.ref_gff_path 
        )
        // concat gffs
        CONCAT_GFFS (
           params.ref_gff_path,
           REPEATMASKER.out.gff,
           LIFTOFF_CLI.out.gff,
           fasta
        )

    emit:
        fasta = LIFTOFF_CLI.out.fasta
        gff = CONCAT_GFFS.out.gff
}
