#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                ONLY BAKTA ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { BAKTA                                             } from "../../modules/bakta/bakta/main"
include { BAKTADBDOWNLOAD                                   } from "../../modules/bakta/baktadbdownload/main"
include { BAKTA_POST_CLEANUP                                } from "../../modules/post_bakta_annotation/main"

workflow RUN_BAKTA {

    main:
        // run bakta annotation on single fasta files
        BAKTADBDOWNLOAD ()
        
        BAKTA (
            BAKTADBDOWNLOAD.out.db
            params.prodigal_tf
            params.proteins
        )
	    // BAKTA_POST_CLEANUP (
	    //     BAKTA.out.bakta_results,
	    //     params.meta_path,
	    //     params.fasta_path
	    // )
    }


