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
include { METADATA_RAW_SUBMISSION                           } from "../modules/local/metadata_raw_submission/main"

// get viral annotation process/subworkflows
include { LIFTOFF                                           } from "../modules/local/liftoff_annotation/main"
include { REPEATMASKER_LIFTOFF                              } from "../subworkflows/local/repeatmasker_liftoff"
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
    // todo: the names of these tsv_Files need to be from sample name not fasta file name 
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
    // todo: check fasta_ch ids against metadata sample name, don't require fasta file name in metadata
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
                        CHECK_FILES.out.fasta_files.sort().flatten()
                    )
                }
                else {
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
                // set up submission channels for raw fastqs + metadata (sample_name)
                METADATA_RAW_SUBMISSION (
                    RUN_UTILITY.out,
                    params.meta_path
                )
                // Combine sample_names_ch (METADATA_RAW_SUBMISSION.out.sample_names) with sample_file_paths_ch (METADATA_RAW_SUBMISSION.out.sample_file_paths)
                def combined_ch = METADATA_RAW_SUBMISSION.out.sample_names
                    .map { sample_name ->
                        METADATA_RAW_SUBMISSION.out.sample_file_paths
                            .collect { file_paths ->
                                [sample_name, file_paths]
                            }
                        }.flatten()
                // Create a new channel that mimics the structure of fasta_ch
                fastq_ch = combined_ch.map { sample_name, file_paths ->
                    def meta = [:]
                    meta['id'] = sample_name
                    [meta, file_paths]
                }
                // Create the gff_placeholder channel (so we can reuse the same submission module)
                // todo: this part is a bit hacky
                gff_placeholder = METADATA_RAW_SUBMISSION.out.sample_names
                    .map { sample_name ->
                        def meta = [:]
                        meta['id'] = sample_name
                        [meta, 'none']
                    }
                submission_ch = metadata_ch.join(fastq_ch)
                submission_ch = submission_ch.join(gff_placeholder)
                
                FULL_SUBMISSION (
                    submission_ch,
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
