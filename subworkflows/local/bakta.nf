#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                ONLY BAKTA ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { BAKTADBDOWNLOAD                                   } from "../../modules/nf-core/bakta/baktadbdownload/main"
include { BAKTA                                             } from "../../modules/nf-core/bakta/bakta/main"

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
            file(params.bakta_db_path),
            fasta_ch
            )
        }
        
        emit:
        gff = BAKTA.out.gff
        fna = BAKTA.out.fna
    }


