#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            ONLY VALIDATION ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { METADATA_VALIDATION                               } from "../../modules/metadata_validation/main"


workflow RUN_VALIDATION {
    main:
        // run metadata validation
        METADATA_VALIDATION (
            'dummy signal signal', 
            params.meta_path, 
            params.fasta_path
        )
}