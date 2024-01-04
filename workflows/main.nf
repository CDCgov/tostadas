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
include { LIFTOFF                                           } from "../modules/liftoff_annotation/main"
include { BAKTA                                             } from "../modules/bakta/bakta/main"

// get BAKTA related processes
include { BAKTADBDOWNLOAD                                   } from "../modules/bakta/baktadbdownload/main"
include { BAKTA_POST_CLEANUP                                } from "../modules/post_bakta_annotation/main"
include { CONCAT_GFFS                                       } from "../modules/concat_gffs/main"

// get repeat masker / variola related subworkflow
include { RUN_REPEATMASKER_LIFTOFF                          } from "../subworkflows/repeatmasker_liftoff"

// get the subworkflows

include { LIFTOFF_SUBMISSION                                } from "../subworkflows/submission"
include { REPEAT_MASKER_LIFTOFF_SUBMISSION                  } from "../subworkflows/submission"
include { VADR_SUBMISSION                                   } from "../subworkflows/submission"
include { BAKTA_SUBMISSION                                  } from "../subworkflows/submission"
include { RUN_UTILITY                                       } from "../subworkflows/utility"

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow MAIN_WORKFLOW {

    // check if help parameter is set
    if ( params.help == true ) {
        PRINT_PARAMS_HELP()
        exit 0
    }

    // run cleanup
    RUN_UTILITY()

    // run metadata validation process
    METADATA_VALIDATION ( 
        RUN_UTILITY.out, 
        params.meta_path, 
        params.fasta_path 
    )
        
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

    // run liftoff annotation process + repeatmasker 
    if ( params.run_repeatmasker_liftoff == true ) {
        RUN_REPEATMASKER_LIFTOFF (
            RUN_UTILITY.out
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

   // run bakta annotation process
    if ( params.run_bakta == true ) {

      if ( params.download_bakta_db ) {
        BAKTADBDOWNLOAD ()
        BAKTA (
            'dummy utility signal',
            BAKTADBDOWNLOAD.out.db,
            params.fasta_path
        )
            }
        else {
            BAKTA (
                'dummy utility signal',
                params.bakta_db_path,
                params.fasta_path
            )
        }
        
	     BAKTA_POST_CLEANUP (
		    BAKTA.out.bakta_results,
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

        // call the submission workflow for bakta
        if ( params.run_bakta  == true ) {
            BAKTA_SUBMISSION (
                METADATA_VALIDATION.out.tsv_Files,
                BAKTA_POST_CLEANUP.out.fasta,
                BAKTA_POST_CLEANUP.out.gff,
                false,
                params.submission_config,
                params.req_col_config,
                GET_WAIT_TIME.out
            )
        }

        // call the submission workflow process for liftoff + repeatmasker 
        if ( params.run_repeatmasker_liftoff == true ) {
            REPEAT_MASKER_LIFTOFF_SUBMISSION(
                METADATA_VALIDATION.out.tsv_Files.sort().flatten(),
                RUN_REPEATMASKER_LIFTOFF.out[0],
                RUN_REPEATMASKER_LIFTOFF.out[1],
                false,
                params.submission_config, 
                params.req_col_config, 
                GET_WAIT_TIME.out   
            )
        }  
    }
}
