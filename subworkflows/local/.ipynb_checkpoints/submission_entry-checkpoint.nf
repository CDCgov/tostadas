 #!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            ONLY SUBMISSION ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

// include { CHECKS_4_SUBMISSION_ENTRY                         } from "./submission_entry_check"
include { CHECK_FILES                                       } from "../../modules/local/general_util/check_files/main"
include { GET_WAIT_TIME                                     } from "../../modules/local/general_util/get_wait_time/main"
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
        // TODO: this currently assumes that the metadata files MUST be passed in... I dont think Genbank needs metadata, but could be wrong
        CHECK_FILES (
            'dummy utility signal',
            false,
            true,
            false,
            params.final_split_metas_path
        )

        // get the wait time
        GET_WAIT_TIME (
            CHECK_FILES.out.meta_files.collect() 
        )

        // place files into proper channels 
        meta_ch = CHECK_FILES.out.meta_files.collect().flatten()
        .map { 
            def meta = [:] 
            meta['id'] = it.getSimpleName()
            [ meta, it ] 
        }
        gff_ch = CHECK_FILES.out.gff_files.collect().flatten()
        .map { 
            def meta = [:] 
            meta['id'] = it.getSimpleName().replaceAll('_reformatted', '')
            [ meta, it ] 
        }
        fasta_ch = CHECK_FILES.out.fasta_files.collect().flatten()
        .map { 
            def meta = [:] 
            meta['id'] = it.getSimpleName()
            [ meta, it ] 
        }
        entry_submission_ch = meta_ch.join(fasta_ch)
        entry_submission_ch = entry_submission_ch.join(gff_ch)
        
        // call the submission workflow
        GENERAL_SUBMISSION (
            entry_submission_ch,
            params.submission_config,
            params.req_col_config,
            GET_WAIT_TIME.out
        )
}