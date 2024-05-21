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
        fasta
        metadata_ch
    main:
        // run vadr processes

        VADR_TRIM (
            fasta
        )

        VADR_ANNOTATION (
            VADR_TRIM.out.trimmed_fasta,
            params.vadr_models_dir
        )
        cleanup_ch = metadata_ch.join(fasta)
        cleanup_ch = cleanup_ch.join(VADR_ANNOTATION.out.vadr_outputs)

        VADR_POST_CLEANUP (
            cleanup_ch
        )
    
    emit:
        gff = VADR_POST_CLEANUP.out.gff
}

