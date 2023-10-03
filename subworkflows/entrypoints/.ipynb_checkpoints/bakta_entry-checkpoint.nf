#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                ONLY SPLIT FASTA ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { SPLIT_FASTA                                           } from "../../modules/split_multi_fasta/main"
include { BAKTA                                                 } from "../../modules/bakta_annotation/main"

workflow RUN_BAKTA {

    main:
    // split multi fasta files into single fasta files
    SPLIT_FASTA (
        'dummy utility signal',
        params.fasta_path
    )
    
    // run bakta annotation on single fasta files
	BAKTA (
	     'dummy utility signal',
	      params.db_path,
	      SPLIT_FASTA.out.fasta_files.flatten()
	)
}


