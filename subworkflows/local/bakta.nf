#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                ONLY BAKTA ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { BAKTA_BAKTADBDOWNLOAD                             } from "../../modules/nf-core/bakta/baktadbdownload/main"
include { BAKTA_BAKTA                                       } from "../../modules/nf-core/bakta/bakta/main"

workflow RUN_BAKTA {
    take: 
    fasta_ch

    main:
        // Transform meta to include 'id' field expected by BAKTA module
        bakta_input_ch = fasta_ch.map { meta, fasta ->
            def bakta_meta = meta + [id: meta.sample_id]
            return [bakta_meta, fasta]
        }

        // Prepare optional input files
        proteins_file = params.bakta_proteins ? file(params.bakta_proteins) : []
        prodigal_tf_file = params.bakta_prodigal_tf ? file(params.bakta_prodigal_tf) : []


        if ( params.download_bakta_db ) {
            BAKTA_BAKTADBDOWNLOAD (
                )

            BAKTA_BAKTA (
                bakta_input_ch,
                BAKTA_BAKTADBDOWNLOAD.out.db,
                proteins_file,
                prodigal_tf_file
                )
            }
        else {
            BAKTA_BAKTA (
            bakta_input_ch,
            file(params.bakta_db_path),
            proteins_file,
            prodigal_tf_file
            )
        }

        // Transform meta back to original format for outputs
        gff_output = BAKTA_BAKTA.out.gff.map { meta, gff ->
            def original_meta = meta.findAll { key, value -> key != 'id' }
            return [original_meta, gff]
        }
        
        fna_output = BAKTA_BAKTA.out.fna.map { meta, fna ->
            def original_meta = meta.findAll { key, value -> key != 'id' }
            return [original_meta, fna]
        }
        
        emit:
        gff = BAKTA_BAKTA.out.gff
        fna = BAKTA_BAKTA.out.fna
    }


