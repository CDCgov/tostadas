#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            ONLY VADR ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { VADR                                              } from "../../modules/vadr_annotation/main"
include { VADR_POST_CLEANUP                                 } from "../../modules/post_vadr_annotation/main"


workflow RUN_VADR {
    main:
        // run vadr processes
        VADR (
            'dummy utility signal', 
            params.fasta_path,
            params.vadr_models_dir
        )
        VADR_POST_CLEANUP (
            VADR.out.vadr_outputs,
            params.meta_path,
            params.fasta_path
        )
}

