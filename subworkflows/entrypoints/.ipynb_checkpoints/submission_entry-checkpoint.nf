#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            ONLY SUBMISSION ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { CHECKS_4_SUBMISSION_ENTRY                         } from "./submission_entry_check"
include { PREP_SUBMISSION_ENTRY                             } from "../../modules/submission_entrypoint/prep_sub_entry/main"
include { GET_WAIT_TIME                                     } from "../../modules/general_util/get_wait_time/main"
include { ENTRY_SUBMISSION                                  } from "../submission"

workflow RUN_SUBMISSION {
    main:
        // check that certain paths are specified (need to pass in for it to work)
        CHECKS_4_SUBMISSION_ENTRY (
            'only_submission'
        )

        // get the parameter paths into proper format 
        PREP_SUBMISSION_ENTRY ( 
            CHECKS_4_SUBMISSION_ENTRY.out,
            params.submission_only_meta, 
            params.submission_only_fasta, 
            params.submission_only_gff, 
            params.submission_config,
            params.submission_database,
            false
        )

        // get the wait time
        GET_WAIT_TIME (
            PREP_SUBMISSION_ENTRY.out.tsv.collect() 
        )
        
        // call the submission workflow
        ENTRY_SUBMISSION (
            PREP_SUBMISSION_ENTRY.out.tsv.sort().flatten(),
            PREP_SUBMISSION_ENTRY.out.fasta.sort().flatten(),
            PREP_SUBMISSION_ENTRY.out.gff.sort().flatten(), 
            true,
            params.submission_config,
            params.req_col_config,
            GET_WAIT_TIME.out
        )
}