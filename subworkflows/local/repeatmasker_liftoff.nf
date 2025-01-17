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
        fasta // meta, metadata, fasta_path, fastq1, fastq2

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

        repeatmasker_gff_ch = REPEATMASKER.out.gff.collect().flatten()
                .map { 
                    meta = [:] 
                    meta['id'] = it.getSimpleName()
                    [ meta, it ] 
                }

        liftoff_gff_ch = LIFTOFF_CLI.out.gff.collect().flatten()
                .map { 
                    meta = [:] 
                    meta['id'] = it.getSimpleName()
                    [ meta, it ] 
                }

        concat_gffs_ch = fasta.join(repeatmasker_gff_ch).join(liftoff_gff_ch) // meta.id, metadata, fasta, fastq1, fastq2, repeatmasker_gff, liftoff_gff

        // concat gffs 
        CONCAT_GFFS (
           params.ref_gff_path,
           concat_gffs_ch
        )

    emit:
        fasta = LIFTOFF_CLI.out.fasta
        gff = CONCAT_GFFS.out.gff
}