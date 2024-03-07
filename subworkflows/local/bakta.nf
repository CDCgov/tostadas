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
    utility_signal
    fasta_ch

    main:
        if ( params.download_bakta_db ) {
            BAKTADBDOWNLOAD (
                utility_signal 
                )
            BAKTA (
                utility_signal,
                BAKTADBDOWNLOAD.out.db,
                fasta_ch
                )
            }
        else {
            BAKTA (
            utility_signal,
            params.bakta_db_path,
            fasta_ch
            )
        }
        
        emit:
        gff3 = BAKTA.out.gff3
    }


