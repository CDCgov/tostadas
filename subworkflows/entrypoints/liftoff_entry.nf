#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            ONLY LIFTOFF ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { REPEATMASKER                                      } from "../../modules/repeatmasker_annotation/main"
include { LIFTOFF                                           } from "../../modules/liftoff_annotation/main"

workflow RUN_LIFTOFF {
    main:
        // run repeatmasker annotation on files
	REPEATMASKER (
	   'dummy utility signal',
	   params.fasta_path,
	   params.repeat_lib
	)
	// run annotation on files
        LIFTOFF ( 
            'dummy utility signal', 
            params.meta_path, 
            params.fasta_path, 
            params.ref_fasta_path, 
            params.ref_gff_path,
	    REPEATMASKER.out.gff 
        )
}
