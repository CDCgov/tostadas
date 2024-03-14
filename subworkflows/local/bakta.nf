#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                ONLY BAKTA ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { BAKTA                                             } from "../../modules/nf-core/bakta/bakta/main"
include { BAKTADBDOWNLOAD                                   } from "../../modules/nf-core/bakta/baktadbdownload/main"
// get BAKTA related processes

workflow RUN_BAKTA {
    take: 
    fasta_ch

    main:
        if ( params.download_bakta_db ) {
            BAKTADBDOWNLOAD (
                )
            BAKTA (
                BAKTADBDOWNLOAD.out.db,
                fasta_ch
                )
            }
        else {
            BAKTA (
            params.bakta_db_path,
            fasta_ch
            )
        }
        
        emit:
        gff3 = BAKTA.out.gff3
    }


