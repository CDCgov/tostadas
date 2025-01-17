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
        fasta // meta, metadata, fasta_path, fastq1, fastq2

    main:
        // run vadr processes
        VADR_TRIM (
            fasta
        )

        VADR_ANNOTATION (
            VADR_TRIM.out.trimmed_fasta,
            file(params.vadr_models_dir)
        )

        cleanup_ch = fasta.map { meta, tsv, fa, fq1, fq2 ->
            [meta, tsv] // drop everything except the tsv for post-cleanup input
        }
        cleanup_ch = cleanup_ch.join(VADR_ANNOTATION.out.vadr_outputs)
        
        VADR_POST_CLEANUP (
            cleanup_ch
        )
    
    emit:
        tbl = VADR_POST_CLEANUP.out.tbl
}

