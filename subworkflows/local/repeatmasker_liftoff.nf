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
        fasta

    main:
        // run repeatmasker annotation on files
        REPEATMASKER (
           fasta,
           params.repeat_library
        )
        // run liftoff annotation on files
        LIFTOFF_CLI ( 
            fasta,
            params.ref_fasta_path, 
            params.ref_gff_path 
        )

        repeatmasker_gff_ch = REPEATMASKER.out.gff.collect().flatten()
                .map { 
                    meta = [:] 
                    meta['id'] = [id:it.getSimpleName()] 
                    [ meta, it ] 
                }

        liftoff_gff_ch = LIFTOFF_CLI.out.gff.collect().flatten()
                .map { 
                    meta = [:] 
                    meta['id'] = [id:it.getSimpleName()] 
                    [ meta, it ] 
                }

        concat_gffs_ch = repeatmasker_gff_ch.join(liftoff_gff_ch) // meta.id, fasta, repeatmasker_gff, liftoff_gff

        // concat gffs
        CONCAT_GFFS (
           params.ref_gff_path,
           concat_gffs_ch,
           fasta
        )

    emit:
        fasta = LIFTOFF_CLI.out.fasta
        gff = CONCAT_GFFS.out.gff
}