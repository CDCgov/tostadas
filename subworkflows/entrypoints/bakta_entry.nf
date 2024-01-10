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
    take: 
    run_utility

    main:
    // run bakta annotation on single fasta files
    // run bakta annotation process
    if ( params.download_bakta_db ) {
        BAKTADBDOWNLOAD (
            run_utility
        )
    
        BAKTA (
            run_utility,
            BAKTADBDOWNLOAD.out.db,
            params.fasta_path
        )
            }

        else {
            BAKTA (
                run_utility,
                params.bakta_db_path,
                params.fasta_path
            )
        }
        
	    BAKTA_POST_CLEANUP (
		    BAKTA.out.bakta_results,
		    params.meta_path,
		    params.fasta_path
	    )   
        
        emit:
        cleaned_fasta = BAKTA_POST_CLEANUP.out.fasta
        cleaned_gff = BAKTA_POST_CLEANUP.out.gff

    }


