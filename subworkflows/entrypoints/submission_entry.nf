 #!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            ONLY SUBMISSION ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

// include { CHECKS_4_SUBMISSION_ENTRY                         } from "./submission_entry_check"
include { CHECK_FILES                                       } from "../../modules/general_util/check_files/main"
include { GET_WAIT_TIME                                     } from "../../modules/general_util/get_wait_time/main"
include { GENERAL_SUBMISSION                                } from "../submission"

workflow RUN_SUBMISSION {

    main:
        // check that certain paths are specified (need to pass in for it to work)
        // TODO: need to update this submission check, just for checking certain params, generalize it
        /*
        CHECKS_4_SUBMISSION_ENTRY (
            'only_submission'
        )
        */

        // check files and initialize 
        CHECK_FILES (
            'dummy utility signal'
            false,
            true
        )

        // get the wait time
        // TODO: need to get individual TSV files for metadata somehow
        // adapt the general script where if meta is missing then has to be entrypoint 
        // if entrypoint + missing then creates dummy metadata files, else ensures that multiple .tsv are present
        GET_WAIT_TIME (
            CHECK_FILES.out.meta.collect() 
        )
        
        // call the submission workflow
        GENERAL_SUBMISSION (
            CHECK_FILES.out.meta.sort().flatten(),
            CHECK_FILES.out.fasta_files.sort().flatten(),
            CHECK_FILES.out.gff.sort().flatten(), 
            params.submission_config,
            params.req_col_config,
            GET_WAIT_TIME.out
        )
}