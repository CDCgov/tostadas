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
        fasta // meta, fasta_path

    main:
        // run repeatmasker annotation on files
        REPEATMASKER (
           fasta,
           params.repeat_library
        )
        
        // run liftoff annotation on files
        LIFTOFF_CLI ( 
            fasta,
            file(params.ref_fasta_path), 
            file(params.ref_gff_path) 
        )

        // Join the outputs 
        concat_gffs_ch = fasta
            .join(REPEATMASKER.out.gff)
            .join(LIFTOFF_CLI.out.gff)
            .map { meta, fasta_file, repeatmasker_gff, liftoff_gff -> 
                [meta, fasta_file, repeatmasker_gff, liftoff_gff] 
            }

        concat_gffs_ch.view { "CONCAT_GFFS INPUT: $it" }

        // concat gffs 
        CONCAT_GFFS (
           params.ref_gff_path,
           concat_gffs_ch
        )

    emit:
        fasta = LIFTOFF_CLI.out.fasta
        gff = CONCAT_GFFS.out.gff
}