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
    metadata_ch = METADATA_VALIDATION.out.tsv_Files
        .flatten()
        .map { 
            meta = [id:it.getSimpleName()] 
            [ meta, it ] 
        }

    // Generate the fasta and fastq paths
    reads_ch = 
        METADATA_VALIDATION.out.tsv_Files
        .flatten()
        .splitCsv(header: true, sep: "\t")
        .map { row ->
            fasta_path = row.fasta_path ? file(row.fasta_path) : null
            fastq1 = row.fastq_path_1 ? file(row.fastq_path_1) : null
            fastq2 = row.fastq_path_2 ? file(row.fastq_path_2) : null
            meta = [id:row.sequence_name]
            gff = row.gff_path ? file(row.gff_path) : null
            if (gff == null) {
                [meta, fasta_path, fastq1, fastq2]
            }
            else {
                [meta, fasta_path, fastq1, fastq2, gff]
            }
        }
    // Create initial submission channel
    submission_ch = metadata_ch.join(reads_ch)

    // check if the user wants to skip annotation or not
    if ( params.annotation ) {
        if (params.species == 'mpxv' || params.species == 'variola' || params.species == 'rsv' || params.species == 'virus') {
            // run liftoff annotation process + repeatmasker 
            if ( params.repeatmasker_liftoff && !params.vadr ) {
             // run repeatmasker annotation on files
                REPEATMASKER_LIFTOFF (
                    reads_ch
                )
                submission_ch = submission_ch.join(REPEATMASKER_LIFTOFF.out.gff)
            }
            // run vadr processes
            if ( params.vadr ) {
                RUN_VADR (
                    reads_ch,
                    metadata_ch
                )
                submission_ch = submission_ch.join(RUN_VADR.out.gff) // meta.id, tsv, fasta, fastq1, fastq2, gff
            }
        }
        else if (params.species == 'bacteria' || params.species == 'Cdiphtheriae') {
        // run bakta annotation process
            if ( params.bakta ) {
                RUN_BAKTA(
                    reads_ch
                )
                // set up submission channels
                submission_ch = submission_ch
                | join(RUN_BAKTA.out.gff) // meta.id, tsv, fasta, fastq1, fastq2, gff
                | map { meta, tsv, _, fq1, fq2, gff -> 
                    [meta, tsv, fq1, fq2, gff] } // drop original fasta
                | join(RUN_BAKTA.out.fna) // join annotated fasta
                | map { meta, tsv, fq1, fq2, gff, fasta -> 
                    [meta, tsv, fasta, fq1, fq2, gff] }  // meta.id, tsv, annotated fasta, fastq1, fastq2, gff
            }   
        }
    }

    // run submission for the annotated samples 
    if ( params.submission ) {
        // pre submission process + get wait time (parallel)
        GET_WAIT_TIME (
            METADATA_VALIDATION.out.tsv_Files.collect() 
        )

        INITIAL_SUBMISSION (
            submission_ch,  // meta.id, fasta, fastq1, fastq2, gff
            params.submission_config,  
            GET_WAIT_TIME.out
            )

        }
        // to do remove if not needed
        if ( params.update_submission ) {
            UPDATE_SUBMISSION (
                '',
                params.submission_config, 
                INITIAL_SUBMISSION.out.submission_files,
                INITIAL_SUBMISSION.out.submission_log,
            )
        }
        // combine the different upload_log csv files together 
        if ( ! params.update_submission ) {
            MERGE_UPLOAD_LOG ( 
                INITIAL_SUBMISSION.out.submission_files.collect(), 
                INITIAL_SUBMISSION.out.submission_log.collect(), 
                )
        }
        else {
            MERGE_UPLOAD_LOG ( 
                UPDATE_SUBMISSION.out.submission_files.collect(), 
                UPDATE_SUBMISSION.out.submission_log.collect(), 
            )
        }
        // todo add GISAID only submission
    }

