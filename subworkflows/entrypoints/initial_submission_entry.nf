#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            ONLY INITIAL SUBMISSION ENTRYPOINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
include { CHECK_FILES                                       } from "../../modules/general_util/check_files/main"
include { CHECKS_4_SUBMISSION_ENTRY                         } from "./submission_entry_check"
include { SUBMISSION                                        } from "../../modules/submission/main"
include { MERGE_UPLOAD_LOG                                  } from "../../modules/general_util/merge_upload_log/main"


workflow RUN_INITIAL_SUBMISSION {
    main:        
        // check that certain paths are specified (need to pass in for it to work)
        /*
        CHECKS_4_SUBMISSION_ENTRY (
            'only_initial_submission'
        )
        */

        // get the parameter paths into proper format 
        /*
        PREP_SUBMISSION_ENTRY ( 
            CHECKS_4_SUBMISSION_ENTRY.out,
            params.final_split_metas_path,
            params.final_split_fastas_path,
            params.final_annotated_files_path,
            params.submission_config,
            params.submission_database,
            false
        )
        */

        // check files and initialize 
        CHECK_FILES (
            'dummy utility signal',
            false,
            true,
            false,
            params.final_split_metas_path
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


        // call the initial submission portion only
        SUBMISSION (
            entry_submission_ch, 
            params.submission_config,
            params.req_col_config,
            ''
        )

        // call the merging of the upload log file 
        MERGE_UPLOAD_LOG ( SUBMISSION.out.submission_files.collect(), '' )
}