#!/usr/bin/env nextflow
nextflow.enable.dsl=2
    
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                         GET NECESSARY MODULES OR SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// get the utility processes / subworkflows
include { CHECK_FILES                                       } from "../modules/general_util/check_files/main"
// include { INITIALIZE_SUBMISSION_FILES                       } from "../modules/general_util/initialize_submission_files/main"
include { RUN_UTILITY                                       } from "../subworkflows/utility"
include { GET_WAIT_TIME                                     } from "../modules/general_util/get_wait_time/main"

// get the main processes
include { METADATA_VALIDATION                               } from "../modules/metadata_validation/main"
include { SUBMISSION                                        } from "../modules/submission/main"
include { UPDATE_SUBMISSION                                 } from "../modules/update_submission/main"
include { LIFTOFF                                           } from "../modules/liftoff_annotation/main"

// get BAKTA related processes
include { BAKTADBDOWNLOAD                                   } from "../modules/bakta/baktadbdownload/main"
include { BAKTA                                             } from "../modules/bakta/bakta/main"
include { BAKTA_POST_CLEANUP                                } from "../modules/post_bakta_annotation/main"

// get repeat masker related subworkflow
include { RUN_REPEATMASKER_LIFTOFF                          } from "../subworkflows/repeatmasker_liftoff"

// get vadr related subworkflow
include { RUN_VADR                                          } from "../subworkflows/vadr"

// get the subworkflows for submission
include { LIFTOFF_SUBMISSION                                } from "../subworkflows/submission"
include { REPEAT_MASKER_LIFTOFF_SUBMISSION                  } from "../subworkflows/submission"
include { VADR_SUBMISSION                                   } from "../subworkflows/submission"
include { BAKTA_SUBMISSION                                  } from "../subworkflows/submission"
include { GENERAL_SUBMISSION                                } from "../subworkflows/submission"


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow MAIN_WORKFLOW {

    // initialize channels
    fastaCh = Channel.fromPath("$params.fasta_path/*.{fasta, fastq}")
    if (!params.final_annotated_files_path.isEmpty()) {
        annotationCh = Channel.fromPath("$params.final_annotated_files_path/*.gff")
    }


    // check if help parameter is set
    if ( params.help == true ) {
        PRINT_PARAMS_HELP()
        exit 0
    }

    // run utility subworkflow
    RUN_UTILITY()

    // initialize files (stage and change names for files)
    CHECK_FILES (
        RUN_UTILITY.out,
        false,
        params.run_submission
    )

    // run metadata validation process
    METADATA_VALIDATION ( 
        RUN_UTILITY.out,
        params.meta_path
    )

    // check if the user wants to skip annotation or not
    if ( params.run_annotation == true ) {

        // run liftoff annotation process 
        if ( params.run_liftoff == true ) {
            LIFTOFF (
                RUN_UTILITY.out,
                params.meta_path, 
                CHECK_FILES.out.fasta_dir, 
                params.ref_fasta_path, 
                params.ref_gff_path 
            )
        }

        // run liftoff annotation process + repeatmasker 
        if ( params.run_repeatmasker_liftoff == true ) {

            // run repeatmasker annotation on files
            RUN_REPEATMASKER_LIFTOFF (
                RUN_UTILITY.out, 
                CHECK_FILES.out.fasta_files.sort().flatten()
            )
        }

        // run vadr processes
        if ( params.run_vadr == true ) {
            RUN_VADR (
                RUN_UTILITY.out, 
                CHECK_FILES.out.fasta_files.sort().flatten()
            )
        }

        // run bakta annotation process
        if ( params.run_bakta == true ) {
            
            if ( params.download_bakta_db ) {

                BAKTADBDOWNLOAD (
                    RUN_UTILITY.out 
                )

                BAKTA (
                    RUN_UTILITY.out,
                    BAKTADBDOWNLOAD.out.db,
                    CHECK_FILES.out.fasta_files.sort().flatten()
                )

            } else {

                BAKTA (
                    RUN_UTILITY.out,
                    params.bakta_db_path,
                    CHECK_FILES.out.fasta_files.sort().flatten()
                )

            }
        
            BAKTA_POST_CLEANUP (
                BAKTA.out.bakta_results,
                params.meta_path,
                CHECK_FILES.out.fasta_files.sort().flatten()
            )   

        }
    }
  
    // run submission for the annotated samples 
    if ( params.run_submission == true ) {

        // pre submission process + get wait time (parallel)
        GET_WAIT_TIME (
            METADATA_VALIDATION.out.tsv_Files.collect() 
        )

        // check if all annotations are set to false 
        if ( params.run_annotation == true ) {

            // call the submission workflow for liftoff 
            if ( params.run_liftoff == true ) {
                LIFTOFF_SUBMISSION (
                    METADATA_VALIDATION.out.tsv_Files.sort().flatten(), 
                    CHECK_FILES.out.fasta_files.sort().flatten(), 
                    LIFTOFF.out.gff.sort().flatten(),
                    params.submission_config, 
                    params.req_col_config, 
                    GET_WAIT_TIME.out
                )
            }

            // call the submission workflow for vadr 
            if ( params.run_vadr  == true ) {
                VADR_SUBMISSION (
                    METADATA_VALIDATION.out.tsv_Files.sort().flatten(), 
                    CHECK_FILES.out.fasta_files.sort().flatten(), 
                    RUN_VADR.out,
                    params.submission_config, 
                    params.req_col_config, 
                    GET_WAIT_TIME.out 
                )
            }

            // call the submission workflow for bakta
            if ( params.run_bakta  == true ) {
                BAKTA_SUBMISSION (
                    METADATA_VALIDATION.out.tsv_Files.sort().flatten(),
                    CHECK_FILES.out.out.fasta_files.sort().flatten(),
                    BAKTA_POST_CLEANUP.out.gff,
                    params.submission_config,
                    params.req_col_config,
                    GET_WAIT_TIME.out
                )
            }

            // call the submission workflow process for liftoff + repeatmasker 
            if ( params.run_repeatmasker_liftoff == true ) {
                REPEAT_MASKER_LIFTOFF_SUBMISSION (
                    METADATA_VALIDATION.out.tsv_Files.sort().flatten(),
                    CHECK_FILES.out.fasta_files.sort().flatten(),
                    RUN_REPEATMASKER_LIFTOFF.out[1],
                    params.submission_config, 
                    params.req_col_config, 
                    GET_WAIT_TIME.out   
                )
            }  
 
        } else {

            // call the general submission workflow 
            GENERAL_SUBMISSION (
                METADATA_VALIDATION.out.tsv_Files.sort().flatten(),
                CHECK_FILES.out.fasta_files.sort().flatten(),
                CHECK_FILES.out.gff.sort().flatten(),
                params.submission_config, 
                params.req_col_config, 
                GET_WAIT_TIME.out 
            )

        } 
    }
}
