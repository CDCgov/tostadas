#!/usr/bin/env nextflow
nextflow.enable.dsl=2

    
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                         GET NECESSARY MODULES OR SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// get the utility processes
include { VALIDATE_PARAMS                                   } from "../modules/general_util/validate_params/main"
include { CLEANUP_FILES                                     } from "../modules/general_util/cleanup_files/main"
include { GET_WAIT_TIME                                     } from "../modules/general_util/get_wait_time/main"
include { PRINT_PARAMS_HELP                                 } from "../modules/general_util/params_help/main"
// get the main processes
include { METADATA_VALIDATION                               } from "../modules/metadata_validation/main"
include { SUBMISSION                                        } from "../modules/submission/main"
include { UPDATE_SUBMISSION                                 } from "../modules/update_submission/main"
include { VADR                                              } from "../modules/vadr_annotation/main"
include { VADR_POST_CLEANUP                                 } from "../modules/post_vadr_annotation/main"
include { REPEATMASKER                                      } from "../modules/repeatmasker_annotation/main"
include { LIFTOFF_CLI                                       } from "../modules/liftoff_cli_annotation/main"
include { CONCAT_GFFS                                       } from "../modules/concat_gffs/main"
include { LIFTOFF                                           } from "../modules/liftoff_annotation/main"
// get the subworkflows
include { LIFTOFF_SUBMISSION                                } from "../subworkflows/submission"
include { REPEAT_MASKER_LIFTOFF_SUBMISSION                  } from "../subworkflows/submission"
include { VADR_SUBMISSION                                   } from "../subworkflows/submission"
include { RUN_UTILITY                                       } from "../subworkflows/utility"

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

// Channel
//      .fromPath(params.fasta_path)
//      .splitFasta( record: [id: true, seqString: true ])
//      .set { ch_fasta }
     
workflow MAIN {

    // check if help parameter is set
    if ( params.help == true ) {
        PRINT_PARAMS_HELP()
    } else {
        // run cleanup
        RUN_UTILITY()

        // run metadata validation process
        METADATA_VALIDATION ( 
            RUN_UTILITY.out, 
            params.meta_path, 
            params.fasta_path 
        )
        
        // run liftoff annotation process 
        if ( params.run_repeatmasker_liftoff == true ) {
            REPEATMASKER (
            RUN_UTILITY.out,
            params.fasta_path,
            params.repeat_lib
            )
            LIFTOFF_CLI ( 
                RUN_UTILITY.out,  
                params.fasta_path, 
                params.ref_fasta_path, 
                params.ref_gff_path 
            )
            CONCAT_GFFS (
            RUN_UTILITY.out,
            params.ref_gff_path,
            REPEATMASKER.out.gff,
            CLI_LIFTOFF.out.gff
            )
        }  
        
        // run liftoff annotation process 
        if ( params.run_liftoff == true ) {
            LIFTOFF ( 
                RUN_UTILITY.out, 
                params.meta_path, 
                params.fasta_path, 
                params.ref_fasta_path, 
                params.ref_gff_path 
            )
        }

        // run vadr processes
        if ( params.run_vadr == true ) {
            VADR (
                RUN_UTILITY.out, 
                params.fasta_path,
                params.vadr_models_dir
            )
            VADR_POST_CLEANUP (
                VADR.out.vadr_outputs,
                params.meta_path,
                params.fasta_path
            )
        }

        // run submission for the annotated samples 
        if ( params.run_submission == true ) {

            // pre submission process + get wait time (parallel)
            GET_WAIT_TIME (
                METADATA_VALIDATION.out.tsv_Files.collect() 
            )

            // call the submission workflow for liftoff 
            if ( params.run_liftoff == true ) {
                LIFTOFF_SUBMISSION (
                    METADATA_VALIDATION.out.tsv_Files.sort().flatten(), 
                    LIFTOFF.out.fasta.sort().flatten(), 
                    LIFTOFF.out.gff.sort().flatten(), 
                    false, 
                    params.submission_config, 
                    params.req_col_config, 
                    GET_WAIT_TIME.out
                )
            }

            // call the submission workflow for vadr 
            if ( params.run_vadr  == true ) {
                VADR_SUBMISSION (
                    METADATA_VALIDATION.out.tsv_Files.sort().flatten(), 
                    VADR_POST_CLEANUP.out.fasta.sort().flatten(), 
                    VADR_POST_CLEANUP.out.gff.sort().flatten(), 
                    false, 
                    params.submission_config, 
                    params.req_col_config, 
                    GET_WAIT_TIME.out 
                )
            }
            
            if ( params.run_repeatmasker_liftoff == true ) {
                REPEAT_MASKER_LIFTOFF_SUBMISSION(
                    METADATA_VALIDATION.out.tsv_Files.sort().flatten(),
                    LIFTOFF_CLI.out.fasta.sort().flatten(),
                    CONCAT_GFFS.out.gff.sort().flatten(),
                    false,
                    params.submission_config, 
                    params.req_col_config, 
                    GET_WAIT_TIME.out   
                )
            }  
        }
    }
} 