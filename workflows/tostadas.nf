#!/usr/bin/env nextflow
nextflow.enable.dsl=2
	
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
						 GET NECESSARY MODULES OR SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// get the utility processes / subworkflows

// include { RUN_UTILITY                                       } from "../subworkflows/local/utility"
include { validateParameters; paramsSummaryLog; samplesheetToList } from 'plugin/nf-schema'

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
include { SUBMISSION                                        } from '../modules/local/initial_submission/main'
include { WAIT                                              } from '../modules/local/general_util/wait/main'

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

	// validate input parameters
    validateParameters()

    // print summary of supplied parameters
    log.info paramsSummaryLog(workflow)

	// run metadata validation process
	METADATA_VALIDATION ( 

		file(params.meta_path)
	)
    metadata_ch = METADATA_VALIDATION.out.tsv_Files
        .flatten()
		.map { 
			meta = [id:it.getBaseName()] 
			[ meta, it ] 
		}

	// Generate the fasta and fastq paths
	reads_ch = 
		METADATA_VALIDATION.out.tsv_Files
		.flatten()
		.splitCsv(header: true, sep: "\t")
		.map { row ->
			fasta_path = row.fasta_path ? file(row.fasta_path) : []
			fastq1 = row.fastq_path_1 ? file(row.fastq_path_1)  : []
			fastq2 = row.fastq_path_2 ? file(row.fastq_path_2)  : []
			meta = [id:row.sequence_name]
			gff = row.gff_path ? file(row.gff_path) : []
			// Return a list with 5 elements
			[meta, fasta_path, fastq1, fastq2, gff]
			}

	// Create initial submission channel
	submission_ch = metadata_ch.join(reads_ch)

	if ( params.fetch_reports_only == false) {
		// check if the user wants to skip annotation or not
		if ( params.annotation ) {
			// Remove user-provided gff, if present, from annotation input channel before performing annotation
			submission_ch = submission_ch.map { elements ->
				elements.take(5)  // Remove the last element (gff)
				}

			if (params.species == 'mpxv' || params.species == 'variola' || params.species == 'rsv' || params.species == 'virus') {
				// run liftoff annotation process + repeatmasker 
				if ( params.repeatmasker_liftoff && !params.vadr ) {
					// run repeatmasker annotation on files
					REPEATMASKER_LIFTOFF (
						submission_ch
					)
					submission_ch = submission_ch.join(REPEATMASKER_LIFTOFF.out.gff)
				}
				// run vadr processes
				// todo: VADR fails when species == virus because it uses that flag to call the vadr_models files
				if ( params.vadr ) {
					RUN_VADR (
						submission_ch
					)
					submission_ch = submission_ch.join(RUN_VADR.out.tbl) // meta.id, tsv, fasta, fastq1, fastq2, tbl
				}
			}
			else if (params.species == 'bacteria') {
			// run bakta annotation process
				if ( params.bakta ) {
					RUN_BAKTA(
						submission_ch
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
	}

	// run submission for the annotated samples 
	if ( params.submission || params.fetch_reports_only ) {
		// pre submission process + get wait time (parallel)
		GET_WAIT_TIME (
			METADATA_VALIDATION.out.tsv_Files.collect() 
		)

		INITIAL_SUBMISSION (
			submission_ch,  // meta.id, tsv, fasta, fastq1, fastq2, gff
			params.submission_config,  
			GET_WAIT_TIME.out
			)

		}
	}

