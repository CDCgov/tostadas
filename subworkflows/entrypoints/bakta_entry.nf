#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                ONLY SPLIT FASTA ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { BAKTA                                                 } from "../../modules/bakta_annotation/main"

workflow RUN_BAKTA {

    main:
        // run bakta annotation on single fasta files
        BAKTA (
            'dummy utility signal',
              params.db_path,
              params.fasta_path
        )
}


