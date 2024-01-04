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
   // run bakta annotation process
    if (params.download_bakta_db) {
        BAKTADBDOWNLOAD ()
        BAKTA (
            'dummy utility signal',
            BAKTADBDOWNLOAD.out.db,
            params.fasta_path
        )
            }
        else {
            BAKTA (
                'dummy utility signal',
                params.bakta_db_path,
                params.fasta_path
            )
        }
        
	    BAKTA_POST_CLEANUP (
		    BAKTA.out.bakta_results,
		    params.meta_path,
		    params.fasta_path
	    )   
    }

