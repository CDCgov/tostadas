#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    SUBWORKFLOW FOR VALIDATION --> SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { GET_WAIT_TIME                                     } from "../../modules/general_util/get_wait_time/main"
include { METADATA_VALIDATION                               } from "../../modules/metadata_validation/main"
include { SUBMISSION                                        } from "../../modules/submission/main"
include { GENERAL_SUBMISSION                                } from "../submission"


workflow RUN_VALIDATION_AND_SUBMISSION {

    // Get the channel for the annotation files
    if (!params.final_annotated_files_path.isEmpty()) {
        annotationCh = Channel.fromPath("$params.final_annotated_files_path/*.gff")
    }

    take:
        utility_signal
        is_it_only_initial

    main:

        // initialize files (stage and change names for files)
        /*
        INITIALIZE_FASTA_FILES (
            utility_signal
        )
        */

        // run metadata validation process
        METADATA_VALIDATION ( 
            utility_signal,
            params.meta_path
        )

        if ( is_it_only_initial == false ) {

            // pre submission process + get wait time (parallel)
            GET_WAIT_TIME (
                METADATA_VALIDATION.out.tsv_Files.collect() 
            )

            // call the general submission workflow 
            GENERAL_SUBMISSION (
                METADATA_VALIDATION.out.tsv_Files.sort().flatten(),
                INITIALIZE_FASTA_FILES.out.fasta_files.sort().flatten(),
                annotationCh,
                params.submission_config, 
                params.req_col_config, 
                GET_WAIT_TIME.out 
            )

        } else {

            // call submission process directly 
            SUBMISSION (
                METADATA_VALIDATION.out.tsv_Files.sort().flatten(),
                INITIALIZE_FASTA_FILES.out.fasta_files.sort().flatten(),
                annotationCh, 
                params.submission_config,
                params.req_col_config,
                'entry'
            )
            
        }
}