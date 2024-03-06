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
include { EXTRACT_INPUTS                                    } from '../modules/local/extract_inputs/main'

// get viral annotation process/subworkflows
include { LIFTOFF                                           } from "../modules/local/liftoff_annotation/main"
include { REPEATMASKER_LIFTOFF                              } from "../subworkflows/local/repeatmasker_liftoff"
include { RUN_VADR                                          } from "../subworkflows/local/vadr"

// get BAKTA subworkflow
include { RUN_BAKTA                                         } from "../subworkflows/local/bakta"

// get submission related process/subworkflows
include { INITIAL_SUBMISSION                                } from "../subworkflows/local/submission"
include { UPDATE_SUBMISSION                                 } from "../modules/local/update_submission/main"
include { MERGE_UPLOAD_LOG                                  } from "../modules/local/general_util/merge_upload_log/main"

include { SUBMISSION_FULL                               } from '../modules/local/initial_submission/main_full'
include { SUBMISSION_SRA                                } from '../modules/local/initial_submission/main_sra'
include { SUBMISSION_GENBANK                            } from '../modules/local/initial_submission/main_genbank'
include { WAIT                                          } from '../modules/local/general_util/wait/main'

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// To Do, create logic to run workflows for virus vs. bacteria
workflow TOSTADAS {
    
    fastq_ch = 
    Channel.fromPath("$params.fastq_path").first()

    fasta_ch = 
    Channel.fromPath("${params.fasta_path}/*.fasta")
    .map { 
         def meta = [:] 
         meta['id'] = it.getSimpleName().replaceAll('_reformatted', '')
         [ meta, it ] 
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
    // todo: the names of these tsv_Files need to be from sample name not fasta file name 
    metadata_ch = METADATA_VALIDATION.out.tsv_Files.flatten()
    .map { 
        def meta = [:] 
        meta['id'] = it.getSimpleName()
        [ meta, it ] 
    }
    .view()
    // Generate the fasta and fastq paths
    METADATA_VALIDATION.out.csv_Files
        | splitCsv(header: true)
        | map { row ->
            meta = [id:row.sequence_name]
            fasta_path = row.fasta_path ? file(row.fasta_path) : null
            fastq1 = row.fastq_path_1 ? file(row.fastq_path_1) : null
            fastq2 = row.fastq_path_2 ? file(row.fastq_path_2) : null
            [meta, fasta_path, fastq1, fastq2]
        }
    | view
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
                    fasta_ch
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
                RUN_BAKTA(
                    RUN_UTILITY.out, 
                    fasta_ch
                )
                // set up submission channels
                bakta_gff_ch = RUN_BAKTA.out.gff3.flatten()
                    .map { 
                        def meta = [:] 
                        meta['id'] = it.getSimpleName()
                        [ meta, it ]
                        }
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
            if (params.sra && params.genbank ) {                     // sra and genbank
                INITIAL_SUBMISSION (
                    submission_ch,  // meta.id, metadata_path, fasta, gff
                    fastq_ch,
                    params.submission_config,  
                    GET_WAIT_TIME.out
                    )
                } 
            else {      
                if (! params.sra && params.genbank ) {               // only genebankk
                    INITIAL_SUBMISSION ( 
                        submission_ch,     // meta.id, metadata_path, fasta, gff
                        fastq_ch,
                        params.submission_config, 
                        GET_WAIT_TIME.out
                        )
                    }
                }
        }
        }
        if ( !params.annotation && params.sra ) {        // no annotation only fastq submission
            // submission_ch = metadata_ch
    
            // SUBMISSION_SRA ( submission_ch, fastq_ch, params.submission_config, params.req_col_config, '' )
            
            // // actual process to initiate wait 
            // WAIT ( SUBMISSION_SRA.out.submission_files.collect(), GET_WAIT_TIME.out )

            // // process for updating the submitted samples
            // UPDATE_SUBMISSION ( WAIT.out, params.submission_config, SUBMISSION_SRA.out.submission_files, SUBMISSION_SRA.out.submission_log, '' )

            // // combine the different upload_log csv files together 
            // MERGE_UPLOAD_LOG ( UPDATE_SUBMISSION.out.submission_files.collect(), '' )


            INITIAL_SUBMISSION (
                metadata_ch,       // metadata_path
                fastq_ch,
                params.submission_config, 
                GET_WAIT_TIME.out
            )
        } 
        if ( !params.annotation && params.genbank ) {
                // todo: make an error msg that follows the rest of the code protocol
                throw new Exception("Cannot submit to GenBank without assembly and annotation files")
        }

        // To Do test update submission
        if ( params.update_submission ) {
            UPDATE_SUBMISSION (
                RUN_UTILITY.out,
                params.submission_config, 
                params.submission_output
            )
        }
        // combine the different upload_log csv files together 
        if ( ! params.update_submission ) {
            MERGE_UPLOAD_LOG ( 
                INITIAL_SUBMISSION.out.submission_files.collect(), INITIAL_SUBMISSION.out.submission_log.collect(), 
                '' )
        }
        else {
            MERGE_UPLOAD_LOG ( 
                UPDATE_SUBMISSION.out.submission_files.collect(), UPDATE_SUBMISSION.out.submission_log.collect(), 
                ''
            )
        }

        // To Do add Genbank / GISAID only submission
    }

