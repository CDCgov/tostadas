#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            VADR SUBWORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { VADR_TRIM                                         } from "../../modules/local/vadr_trim/main"
include { VADR_ANNOTATION                                   } from "../../modules/local/vadr_annotation/main"
include { VADR_POST_CLEANUP                                 } from "../../modules/local/vadr_post_cleanup/main"

workflow RUN_VADR {
    take:
        fasta // meta, fasta_path, fastq1, fastq2, nnp

    main:
        // Step 1: Trim terminal ambiguous nucleotides from fasta
        VADR_TRIM(fasta)
        
        // Step 2: Run VADR annotation on trimmed fasta
        VADR_ANNOTATION(
            VADR_TRIM.out.trimmed_fasta,
            params.vadr_models_dir
        )
        
        // Step 3: Post-process VADR outputs
        VADR_POST_CLEANUP(VADR_ANNOTATION.out.vadr_outputs)

    emit:
        gff    = VADR_POST_CLEANUP.out.gff      // tuple val(meta), path('*/transformed_outputs/gffs/*.gff')
        errors = VADR_POST_CLEANUP.out.errors   // tuple val(meta), path('*/transformed_outputs/errors/*.txt')
        tbl    = VADR_POST_CLEANUP.out.tbl      // tuple val(meta), path('*/transformed_outputs/tbl/*.tbl')
}