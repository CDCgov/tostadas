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
include { REPEATMASKER_LIFTOFF                          } from "../subworkflows/local/repeatmasker_liftoff"
include { RUN_VADR                                          } from "../subworkflows/local/vadr"

// get BAKTA related processes
include { BAKTADBDOWNLOAD                                   } from "../modules/nf-core/bakta/baktadbdownload/main"
include { BAKTA                                             } from "../modules/nf-core/bakta/bakta/main"
include { BAKTA_POST_CLEANUP                                } from "../modules/local/post_bakta_annotation/main"

// get submission related process/subworkflows
include { FULL_SUBMISSION                                   } from "../subworkflows/local/full_submission"
include { SRA_SUBMISSION                                    } from "../subworkflows/local/sra_submission"
include { UPDATE_SUBMISSION                                 } from "../modules/local/update_submission/main"

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// To Do, create logic to run workflows for virus vs. bacteria
workflow TOSTADAS {
    
    // To Do, maybe? create samplesheet input to initiate this channel instead

    // initialize channels
    // fastaCh = Channel.fromPath("$params.fasta_path/*.{fasta}")
    // if (!params.final_annotated_files_path.isEmpty()) {
    //     annotationCh = Channel.fromPath("$params.final_annotated_files_path/*.gff")
    // }

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
    if ( params.annotation ) {
        if ( params.virus && !params.bacteria ) {
        // To Do remove liftoff only annotation from pipeline
        // run liftoff annotation process (deprecated)
            if ( params.liftoff ) {
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
            if ( params.repeatmasker_liftoff ) {
             // run repeatmasker annotation on files
                REPEATMASKER_LIFTOFF (
                    RUN_UTILITY.out, 
                    fasta_ch
                )
                repeatmasker_gff_ch = REPEATMASKER_LIFTOFF.out.gff.collect().flatten()
                .map { 
                    def meta = [:] 
                    meta['id'] = it.getSimpleName().replaceAll('_reformatted', '')
                    [ meta, it ] 
                }

            // set up submission channels
            submission_ch = metadata_ch.join(fasta_ch)
            submission_ch = submission_ch.join(repeatmasker_gff_ch)
            }
    
            // run vadr processes
            if ( params.vadr ) {
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
        }
        if ( params.bacteria ) {
        // run bakta annotation process
            if ( params.bakta == true ) {
                if ( params.download_bakta_db ) {
                    BAKTADBDOWNLOAD (
                    RUN_UTILITY.out 
                )
                    BAKTA (
                        RUN_UTILITY.out,
                        BAKTADBDOWNLOAD.out.db,
                        fasta_ch
                    )
                }
                else {
                    BAKTA (
                        RUN_UTILITY.out,
                        params.bakta_db_path,
                        fasta_ch
                    )
                    bakta_gff_ch = BAKTA.out.gff3.flatten()
                    .map { 
                        def meta = [:] 
                        meta['id'] = it.getSimpleName()
                        [ meta, it ]
                        }
                }
                // set up submission channels
                submission_ch = metadata_ch.join(fasta_ch)
                submission_ch = submission_ch.join(bakta_gff_ch)
            }   
        }
    }

    // run submission for the annotated samples 
    if ( params.submission ) {

        // pre submission process + get wait time (parallel)
        GET_WAIT_TIME (
            METADATA_VALIDATION.out.tsv_Files.collect() 
        )

        // check if annotation is set to true 
        if ( params.annotation ) {
            if ( params.genbank && params.sra ) {
            
                FULL_SUBMISSION (
                    submission_ch,
                    params.submission_config, 
                    params.req_col_config, 
                    GET_WAIT_TIME.out   
                )
            } 
        } 
        if ( params.annotation == false ) {
            if ( params.sra ) {
                SRA_SUBMISSION (
                    metadata_ch,
                    params.submission_config, 
                    params.req_col_config, 
                    GET_WAIT_TIME.out
                )
            } 
        }
        // To Do test update submission
        if ( params.update_submission ) {
            UPDATE_SUBMISSION ()
        }
    }
}
        // To Do add Genbank / GISAID only submission

