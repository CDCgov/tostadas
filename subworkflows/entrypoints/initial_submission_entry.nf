#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            ONLY INITIAL SUBMISSION ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { CHECKS_4_SUBMISSION_ENTRY                         } from "./submission_entry_check"
include { PREP_SUBMISSION_ENTRY                             } from "../../modules/submission_entrypoint/prep_sub_entry/main"
include { SUBMISSION                                        } from "../../modules/submission/main"
include { MERGE_UPLOAD_LOG                                  } from "../../modules/general_util/merge_upload_log/main"


workflow RUN_INITIAL_SUBMISSION {
    main:        
        // check that certain paths are specified (need to pass in for it to work)
        CHECKS_4_SUBMISSION_ENTRY (
            'only_initial_submission'
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

        // call the initial submission portion only
        SUBMISSION (
            PREP_SUBMISSION_ENTRY.out.tsv.sort().flatten(),
            PREP_SUBMISSION_ENTRY.out.fasta.sort().flatten(),
            PREP_SUBMISSION_ENTRY.out.gff.sort().flatten(), 
            true,
            params.submission_config,
            params.req_col_config,
            ''
        )

        // call the merging of the upload log file 
        MERGE_UPLOAD_LOG ( SUBMISSION.out.submission_files.collect(), '' )
}