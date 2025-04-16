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

	// Generate the fasta annd fastq paths
	reads_ch = 
		METADATA_VALIDATION.out.tsv_Files
		.flatten()
		.splitCsv(header: true, sep: "\t")
		.map { row ->
			def trimFile = { path -> path && path.trim() ? file(path.trim()) : [] }

			def meta = [id: row.sample_name?.trim()]
			def fasta_path = trimFile(row.fasta_path)
			def fastq1 = trimFile(row.illumina_sra_file_path_1)
			def fastq2 = trimFile(row.illumina_sra_file_path_2)
			def nanopore = trimFile(row.nanopore_sra_file_path_1)
			def gff = trimFile(row.gff_path)

			return [meta, fasta_path, fastq1, fastq2, gff]
			}



	// Create initial submission channel
	submission_ch = metadata_ch.join(reads_ch)