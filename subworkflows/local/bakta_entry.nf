#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                ONLY BAKTA ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { BAKTA                                             } from "../../modules/nf-core/bakta/bakta/main"
include { BAKTADBDOWNLOAD                                   } from "../../modules/nf-core/bakta/baktadbdownload/main"
include { BAKTA_POST_CLEANUP                                } from "../../modules/local/post_bakta_annotation/main"

workflow RUN_BAKTA {
    take: 
    run_utility
    fasta

    main:
    if ( params.download_bakta_db ) {
        BAKTADBDOWNLOAD (
            run_utility
        )
    
        BAKTA (
            run_utility,
            BAKTADBDOWNLOAD.out.db,
            fasta
        )
            }

        else {
            BAKTA (
                run_utility,
                params.bakta_db_path,
                fasta
            )
        }
        
	    BAKTA_POST_CLEANUP (
		    BAKTA.out.bakta_results,
		    params.meta_path,
		    fasta
	    )   
        
        emit:
        cleaned_fasta = BAKTA_POST_CLEANUP.out.fasta
        cleaned_gff = BAKTA_POST_CLEANUP.out.gff

    }


