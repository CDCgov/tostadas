#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            ONLY LIFTOFF ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { LIFTOFF                                           } from "../../modules/liftoff_annotation/main"
include { INITIALIZE_FILES                                  } from "../../modules/general_util/initialize_files/main"


workflow RUN_LIFTOFF {
    main:
        // initialize the fasta files 
        INITIALIZE_FILES (
            'dummy utility signal'
        )

        // run annotation on files
        LIFTOFF ( 
            params.meta_path, 
            INITIALIZE_FILES.out.fasta_dir, 
            params.ref_fasta_path, 
            params.ref_gff_path 
        )
}
