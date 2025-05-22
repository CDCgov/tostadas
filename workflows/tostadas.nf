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

	// generate metadata batch channel
	metadata_batch_ch = METADATA_VALIDATION.out.tsv_files
		.flatten()
		.map { batch_tsv ->
			def meta = [
				batch_id: batch_tsv.getBaseName(),
				batch_tsv: batch_tsv
			]
			[meta, batch_tsv]
		}

	// Generate the (per-sample) fasta and fastq paths
	sample_ch = metadata_batch_ch
		.flatMap { meta, _ ->
			def rows = meta.batch_tsv.splitCsv(header: true, sep: "\t")
			return rows.collect { row ->
				def sample_meta = [
					batch_id: meta.batch_id,
					batch_tsv: meta.batch_tsv,
					sample_id: row.sample_name?.trim()
				]
				def trimFile = { path -> path?.trim() ? file(path.trim()) : null }

				def fasta = trimFile(row.fasta_path)
				def fq1 = trimFile(row.int_illumina_sra_file_path_1)
				def fq2 = trimFile(row.int_illumina_sra_file_path_2)
				def nnp = trimFile(row.int_nanopore_sra_file_path_1)
				def gff = trimFile(row.gff_path)

				return [sample_meta, fasta, fq1, fq2, nnp, gff]
			}
		}

		// perform annotation if requested
		if ( params.fetch_reports_only == false) {
			if (params.annotation) {
			annotation_ch = sample_ch.map { meta, fasta, fq1, fq2, nnp, gff -> 
				// remove user-provided gff, if present, from annotation input channel before performing annotation
				[meta, fasta, fq1, fq2] 
			}
				if (params.species in ['mpxv', 'variola', 'rsv', 'virus']) {
					// perform viral annotation according to user's choice: liftoff+repeatmasker or vadr
					if (params.repeatmasker_liftoff && !params.vadr) {
						REPEATMASKER_LIFTOFF(annotation_ch)
						annotation_ch = annotation_ch.join(REPEATMASKER_LIFTOFF.out.gff)
					}

					if (params.vadr) {
						RUN_VADR(annotation_ch)
						annotation_ch = annotation_ch.join(RUN_VADR.out.tbl)
					}
				// or perform bacterial annotation using bakta
				} else if (params.species == 'bacteria') {
					if (params.bakta) {
						RUN_BAKTA(annotation_ch)

						annotation_ch = annotation_ch
							| join(RUN_BAKTA.out.gff)
							| map { meta, fasta, fq1, fq2, nnp, gff -> [meta, fq1, fq2, nnp, gff] }
							| join(RUN_BAKTA.out.fna)
							| map { meta, fq1, fq2, nnp, gff, fasta -> [meta, fasta, fq1, fq2, gff] }
					}
				}
			}
		}

	// Assign initial submission channel based on wether annotation was performed or not
	submission_ch = params.annotation ? annotation_ch : sample_ch

	// Create batch initial submission channel, check for existence of files based on selected submission databases
	submission_batch_ch = submission_ch
		.map { meta, fasta, fq1, fq2, nnp, gff ->
			[meta.batch_id, [meta: meta, fasta: fasta, fq1: fq1, fq2: fq2, nnp: nnp, gff: gff]]
		}
		.groupTuple()
		.map { batch_id, samples ->
			def enabledDatabases = [] as Set
			def missingFiles = [] as Set

			samples.each { s ->
				def sid = s.meta.sample_id
				if (params.sra) {
					def illumina_missing = (!s.fq1 || !file(s.fq1).exists()) && (!s.fq2 || !file(s.fq2).exists())
					def nanopore_missing = (!s.nnp || !file(s.nnp).exists())
					if (illumina_missing && nanopore_missing) {
						if (!s.fq1 || !file(s.fq1).exists()) missingFiles << "${sid}:fastq_1"
						if (!s.fq2 || !file(s.fq2).exists()) missingFiles << "${sid}:fastq_2"
						if (!s.nnp || !file(s.nnp).exists()) missingFiles << "${sid}:nanopore"
					} //todo: this doesn't address one or the other, which is difficult to do without an explicit param/flag

					if (
						(s.fq1 && file(s.fq1).exists() && s.fq2 && file(s.fq2).exists()) ||
						(s.nnp && file(s.nnp).exists())
					) {
						enabledDatabases << "sra"
					}
				}
				if (params.genbank) {
					if (!s.fasta || !file(s.fasta).exists()) missingFiles << "${sid}:fasta"
					if (!s.gff || !file(s.gff).exists())   missingFiles << "${sid}:gff"
					else enabledDatabases << "genbank"
				}
				if (params.biosample) {
					enabledDatabases << "biosample"
				}
			}

			if (missingFiles) {
				log.warn "Skipping batch ${batch_id} due to missing files: ${missingFiles.join(', ')}"
				return null
			}
			def meta = [
				batch_id: batch_id,
				batch_tsv: samples[0].meta.batch_tsv 
			]
			return tuple(meta, samples, enabledDatabases as List)
		}
		.filter { it != null }

		// run submission batched samples 
		if ( params.submission || params.fetch_reports_only || params.update_submission ) {
			// pre submission process + get wait time (parallel)
			GET_WAIT_TIME (
				METADATA_VALIDATION.out.tsv_files.collect() 
			)

			INITIAL_SUBMISSION (
				submission_batch_ch,  // meta (batch_id), samples (list of maps, each with sample_id, fasta, fq1, fq2, gff), enabledDatabases (list)
				params.submission_config,  
				GET_WAIT_TIME.out
				)

			}

}
