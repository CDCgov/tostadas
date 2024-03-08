#!/usr/bin/env nextflow
nextflow.enable.dsl=2
    
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                         GET NECESSARY MODULES OR SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// get the utility processes / subworkflows
// include { CHECK_FILES                                       } from "../modules/local/general_util/check_files/main"
// include { RUN_UTILITY                                       } from "../subworkflows/local/utility"
include { VALIDATE_PARAMS                                   } from '../modules/local/general_util/validate_params/main'

include { GET_WAIT_TIME                                     } from "../modules/local/general_util/get_wait_time/main"

// get metadata validation processes
include { METADATA_VALIDATION                               } from "../modules/local/metadata_validation/main"
include { EXTRACT_INPUTS                                    } from '../modules/local/extract_inputs/main'

// get viral annotation process/subworkflows
// include { LIFTOFF                                           } from "../modules/local/liftoff_annotation/main"
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
    
    // check if help parameter is set
    if ( params.help == true ) {
        PRINT_PARAMS_HELP()
        exit 0
    }

    // validate params
    VALIDATE_PARAMS()
    
    // run metadata validation process
    METADATA_VALIDATION ( 
        params.meta_path
    )
    // todo: the names of these tsv_Files need to be from sample name not fasta file name 
    metadata_ch = METADATA_VALIDATION.out.tsv_Files.flatten()
    .map { 
        def meta = [:] 
        meta['id'] = it.getSimpleName()
        [ meta, it ] 
    }

    // Generate the fasta and fastq paths
    fasta_ch = 
        METADATA_VALIDATION.out.csv_Files.flatten()
        | splitCsv(header: true)
        | map { row ->
            meta = [id:row.sequence_name]
            fasta_path = row.fasta_path ? file(row.fasta_path) : null
            [meta, fasta_path]
        }

    fastq_ch = 
        METADATA_VALIDATION.out.csv_Files.flatten()
        | splitCsv(header: true)
        | map { row ->
            meta = [id:row.sequence_name]
            fastq1 = row.fastq_path_1 ? file(row.fastq_path_1) : null
            fastq2 = row.fastq_path_2 ? file(row.fastq_path_2) : null
            [meta, fastq1, fastq2]
        }
    // Create initial submission channel
    submission_ch = metadata_ch.join(fasta_ch)
    submission_ch = submission_ch.join(fastq_ch)
    // check if the user wants to skip annotation or not
    if ( params.annotation ) {
        if ( params.virus && !params.bacteria ) {

            // run liftoff annotation process + repeatmasker 
            if ( params.repeatmasker_liftoff ) {
             // run repeatmasker annotation on files
                REPEATMASKER_LIFTOFF (
                    fasta_ch
                )
                repeatmasker_gff_ch = REPEATMASKER_LIFTOFF.out.gff.collect().flatten()
                .map { 
                    def meta = [:] 
                    meta['id'] = it.getSimpleName().replaceAll('_reformatted', '')
                    [ meta, it ] 
                }

            // set up submission channels
            // submission_ch = metadata_ch.join(fasta_ch)
            submission_ch = submission_ch.join(repeatmasker_gff_ch) // meta.id, fasta, fastq1, fastq2, gff
            }
    
            // run vadr processes
            if ( params.vadr ) {
                RUN_VADR (
                    fasta_ch
                )
                vadr_gff_ch = RUN_VADR.out.gff.collect().flatten()
                .map { 
                    def meta = [:] 
                    meta['id'] = it.getSimpleName().replaceAll('_reformatted', '')
                    [ meta, it ] 
                }
                submission_ch = submission_ch.join(vadr_gff_ch) // meta.id, fasta, fastq1, fastq2, gff
            }
        }
        if ( params.bacteria ) {
        // run bakta annotation process
            if ( params.bakta == true ) {
                RUN_BAKTA(
                    fasta_ch
                )
                // set up submission channels
                bakta_gff_ch = RUN_BAKTA.out.gff3.flatten()
                    .map { 
                        def meta = [:] 
                        meta['id'] = it.getSimpleName()
                        [ meta, it ]
                        }
                // submission_ch = metadata_ch.join(fasta_ch)
                submission_ch = submission_ch.join(bakta_gff_ch) // meta.id, fasta, fastq1, fastq2, gff
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
                    submission_ch,  // meta.id, fasta, fastq1, fastq2, gff
                    params.submission_config,  
                    GET_WAIT_TIME.out
                    )
                } 
            else {      
                if (! params.sra && params.genbank ) {               // only genebankk
                    INITIAL_SUBMISSION ( 
                        submission_ch,     // meta.id, fasta, "", "", gff
                        params.submission_config, 
                        GET_WAIT_TIME.out
                        )
                    }
                }
        }
        }
        if ( !params.annotation && params.sra ) {        // no annotation only fastq submission

            INITIAL_SUBMISSION (
                submission_ch,       // meta.id, "", fastq1, fastq2, gff
                params.submission_config, 
                GET_WAIT_TIME.out
            )
        } 
        if ( !params.annotation && params.genbank ) {
                // todo: make an error msg that follows the rest of the code protocol
                throw new Exception("Cannot submit to GenBank without assembly and annotation files")
        }

        // todo test update submission
        if ( params.update_submission ) {
            UPDATE_SUBMISSION (
                params.submission_config, 
                INITIAL_SUBMISSION.out.submission_files
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

        // todo add GISAID only submission
    }

