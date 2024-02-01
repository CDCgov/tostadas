#!/usr/bin/env nextflow
nextflow.enable.dsl=2
    
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                         GET NECESSARY MODULES OR SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// get the utility processes / subworkflows
include { CHECK_FILES                                       } from "../modules/local/general_util/check_files/main"
include { RUN_UTILITY                                       } from "../subworkflows/local/utility"
include { GET_WAIT_TIME                                     } from "../modules/local/general_util/get_wait_time/main"

// get metadata validation processes
include { METADATA_VALIDATION                               } from "../modules/local/metadata_validation/main"

// get viral annotation process/subworkflows
include { LIFTOFF                                           } from "../modules/local/liftoff_annotation/main"
include { RUN_REPEATMASKER_LIFTOFF                          } from "../subworkflows/local/repeatmasker_liftoff"
include { RUN_VADR                                          } from "../subworkflows/local/vadr"

// get BAKTA related processes
include { BAKTADBDOWNLOAD                                   } from "../modules/nf-core/bakta/baktadbdownload/main"
include { BAKTA                                             } from "../modules/nf-core/bakta/bakta/main"
include { BAKTA_POST_CLEANUP                                } from "../modules/local/post_bakta_annotation/main"

// get submission related process/subworkflows
include { SUBMISSION                                        } from "../modules/local/submission/main"
include { UPDATE_SUBMISSION                                 } from "../modules/local/update_submission/main"
include { LIFTOFF_SUBMISSION                                } from "../subworkflows/local/submission"
include { REPEAT_MASKER_LIFTOFF_SUBMISSION                  } from "../subworkflows/local/submission"
include { VADR_SUBMISSION                                   } from "../subworkflows/local/submission"
include { BAKTA_SUBMISSION                                  } from "../subworkflows/local/submission"
include { GENERAL_SUBMISSION                                } from "../subworkflows/local/submission"


/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// To Do, create logic to run workflows for virus vs. bacteria
workflow TOSTADAS {
    // To Do, create samplesheet input to initiate this channel instead
    // initialize channels
    fastaCh = Channel.fromPath("$params.fasta_path/*.{fasta}")
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

    // run metadata validation process
    METADATA_VALIDATION ( 
        RUN_UTILITY.out,
        params.meta_path
    ) 
    metadata_ch = METADATA_VALIDATION.out.tsv_Files.flatten()
    .map { 
        def meta = [:] 
        meta['id'] = it.getSimpleName()
        [ meta, it ] 
    }

    // initialize files (stage and change names for files)
    CHECK_FILES (
        RUN_UTILITY.out,
        false,
        false,
        false,
        METADATA_VALIDATION.out.tsv_dir
    )
    fasta_ch = CHECK_FILES.out.fasta_files.flatten()
    .map { 
        def meta = [:] 
        meta['id'] = it.getSimpleName()
        [ meta, it ] 
    }

    // check if the user wants to skip annotation or not
    if ( params.run_annotation == true ) {

        // run liftoff annotation process (deprecated)
        if ( params.run_liftoff == true ) {
            LIFTOFF (
                RUN_UTILITY.out,
                params.meta_path, 
                params.fasta_path, 
                params.ref_fasta_path, 
                params.ref_gff_path 
            )
            liftoff_gff_ch = LIFTOFF.out.gff.collect().flatten()
            .map { 
                def meta = [:] 
                meta['id'] = it.getSimpleName().replaceAll('_reformatted', '')
                [ meta, it ] 
            }
        }

        // run liftoff annotation process + repeatmasker 
        if ( params.run_repeatmasker_liftoff == true ) {

            // run repeatmasker annotation on files
            RUN_REPEATMASKER_LIFTOFF (
                RUN_UTILITY.out, 
                CHECK_FILES.out.fasta_files.sort().flatten()
            )
            repeatmasker_gff_ch = RUN_REPEATMASKER_LIFTOFF.out.gff.collect().flatten()
            .map { 
                def meta = [:] 
                meta['id'] = it.getSimpleName().replaceAll('_reformatted', '')
                [ meta, it ] 
            }
        }

        // run vadr processes
        if ( params.run_vadr == true ) {
            RUN_VADR (
                RUN_UTILITY.out, 
                CHECK_FILES.out.fasta_files.sort().flatten()
            )
            vadr_gff_ch = RUN_VADR.out.collect().flatten()
            .map { 
                def meta = [:] 
                meta['id'] = it.getSimpleName().replaceAll('_reformatted', '')
                [ meta, it ] 
            }
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
            bakta_gff_ch = BAKTA_POST_CLEANUP.out.gff.collect().flatten()
            .map { 
                def meta = [:] 
                meta['id'] = it.getSimpleName().replaceAll('_reformatted', '')
                [ meta, it ] 
            }   
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

                // set the proper channels up
                liftoff_submission_ch = metadata_ch.join(fasta_ch)
                liftoff_submission_ch = liftoff_submission_ch.join(liftoff_gff_ch)

                LIFTOFF_SUBMISSION (
                    liftoff_submission_ch,
                    params.submission_config, 
                    params.req_col_config, 
                    GET_WAIT_TIME.out
                )
            }

            // call the submission workflow for vadr 
            if ( params.run_vadr  == true ) {

                // set the proper channels up
                vadr_submission_ch = metadata_ch.join(fasta_ch)
                vadr_submission_ch = vadr_submission_ch.join(vadr_gff_ch)

                VADR_SUBMISSION (
                    vadr_submission_ch,
                    params.submission_config, 
                    params.req_col_config, 
                    GET_WAIT_TIME.out 
                )
            }

            // call the submission workflow for bakta
            if ( params.run_bakta  == true ) {
            
                // set the proper channels up
                bakta_submission_ch = metadata_ch.join(fasta_ch)
                bakta_submission_ch = bakta_submission_ch.join(bakta_gff_ch)

                BAKTA_SUBMISSION (
                    bakta_submission_ch,
                    params.submission_config,
                    params.req_col_config,
                    GET_WAIT_TIME.out
                )
            }

            // call the submission workflow process for liftoff + repeatmasker 
            if ( params.run_repeatmasker_liftoff == true ) {

                // set the proper channels up
                repeatmasker_submission_ch = metadata_ch.join(fasta_ch)
                repeatmasker_submission_ch = repeatmasker_submission_ch.join(repeatmasker_gff_ch)

                REPEAT_MASKER_LIFTOFF_SUBMISSION (
                    repeatmasker_submission_ch,
                    params.submission_config, 
                    params.req_col_config, 
                    GET_WAIT_TIME.out   
                )
            }  
 
        } else {

            // place the gffs into proper channel
            general_gff_ch = CHECK_FILES.out.gff_files.collect().flatten()
            .map { 
                def meta = [:] 
                meta['id'] = it.getSimpleName().replaceAll('_reformatted', '')
                [ meta, it ] 
            }

            // set the proper channels up
            general_submission_ch = metadata_ch.join(fasta_ch)
            general_submission_ch = general_submission_ch.join(general_gff_ch)

            // call the general submission workflow 
            GENERAL_SUBMISSION (
                general_submission_ch,
                params.submission_config, 
                params.req_col_config, 
                GET_WAIT_TIME.out 
            )

        } 
    }
}
