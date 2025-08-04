#!/usr/bin/env nextflow
nextflow.enable.dsl=2

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
						 GET NECESSARY MODULES OR SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// get the utility processes / subworkflows
include { validateParameters; paramsSummaryLog; samplesheetToList 	} from 'plugin/nf-schema'

include { GET_WAIT_TIME                                    			} from "../modules/local/general_util/get_wait_time/main"

// get metadata validation processes
include { GENBANK_VALIDATION                               			} from "../modules/local/genbank_validation/main"

// get viral annotation process/subworkflows                                          } from "../modules/local/liftoff_annotation/main"
include { REPEATMASKER_LIFTOFF                            			} from "../subworkflows/local/repeatmasker_liftoff"
include { RUN_VADR                                          		} from "../subworkflows/local/vadr"

// get BAKTA subworkflow
include { RUN_BAKTA                                         		} from "../subworkflows/local/bakta"

// get submission related process/subworkflows
include { SUBMISSION		                                		} from "../subworkflows/local/submission"
include { FETCH_ACCESSIONS		                            		} from "../subworkflows/local/fetch_accessions"

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
									MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

// Global method to trim white space from file paths
def trimFile(path) {
    return path?.trim() ? file(path.trim()) : null
}

workflow GENBANK {
	main:
	validateParameters()
	log.info paramsSummaryLog(workflow)

	// Run GenBank validation
	// Change this to use sample_id, fasta, gff as inputs [leave tsv out]

	// need to parse meta_path into Channel with sample_id, fasta, gff 
	// GENBANK_VALIDATION(file(params.excel_with_accessions)) //this is wrong
	GENBANK_VALIDATION(sample_ch)

	// Construct the per-sample channel with: sample_id, validated_fasta, validated_gff
	validated_fasta_map_ch = GENBANK_VALIDATION.out.fasta
		.map { f -> 
			def sid = f.getBaseName().replaceFirst(/\.f(ast)?a$/, '') 
			[sid, f] 
		}

	validated_gff_map_ch = GENBANK_VALIDATION.out.gff
		.map { g -> 
			def sid = g.getBaseName().replaceFirst(/\.gff3?$/, '') 
			[sid, g] 
		}

	sample_ch = validated_fasta_map_ch
		.join(validated_gff_map_ch)
		.map { sid, fasta, gff ->
			def meta = [id: sid]
			def out  = [meta, fasta, gff]
			out
		}

	// Run annotation and override fasta/gff if needed
	if (params.annotation) {
		if (params.species in ['mpxv', 'variola', 'rsv', 'virus']) {

			if (params.repeatmasker_liftoff && !params.vadr) {
				REPEATMASKER_LIFTOFF(sample_ch)
				sample_ch = sample_ch
					| join(REPEATMASKER_LIFTOFF.out.gff)
					| map { sample_id, tsv, fasta, gff -> [sample_id, tsv, fasta, gff] }
			}

			if (params.vadr) {
				RUN_VADR(sample_ch)
				sample_ch = sample_ch
					| join(RUN_VADR.out.tbl)
					| map { sample_id, tsv, fasta, tbl -> [sample_id, tsv, fasta, tbl] }
			}

		} else if (params.species == 'bacteria' && params.bakta) {
			RUN_BAKTA(sample_ch)
			sample_ch = sample_ch
				| join(RUN_BAKTA.out.gff)
				| join(RUN_BAKTA.out.fna)
				| map { sample_id, tsv, _orig_fasta, gff, fasta -> [sample_id, tsv, fasta, gff] }
		}
	}

	// Recreate the same batches from BIOSAMPLE_AND_SRA workflow
	def batched_tsv_dir = file("${params.metadata_dir}/batched_tsvs")
	def batch_summary_json = file("${batched_tsv_dir}/batch_summary.json")

	batch_summary_ch = Channel
		.fromPath(batch_summary_json)
		.map { json_file ->
			def data = new groovy.json.JsonSlurper().parseText(json_file.text)
			// data: [ "batch_1.tsv": ["IL0005", ...], ... ]
			data.collectEntries { k, v ->
				def batch_id = k.replaceFirst(/\.tsv$/, '')
				def batch_tsv = batched_tsv_dir.resolve(k).toAbsolutePath()
				[batch_id, [tsv: batch_tsv, sample_ids: v]]
			}
		}

	// Create a lookup map for sample_id to fasta and gff
	annotated_sample_map_ch = sample_ch
			.collect()
			.map { samples ->
				samples.collectEntries { row ->
					def sample_id = row[0]
					def fasta     = row[1]
					def gff       = row[2]
					[(sample_id): [fasta, gff]]
				}
			}

	// Combine batch meta info with per-sample info to create the submission channel
	genbank_batch_ch = batch_summary_ch
		.combine(annotated_sample_map_ch)
		.map { batch_map, sample_map ->

			batch_map.collect { batch_id, info ->
				def batch_tsv = file(info.tsv)
				def sample_ids = info.sample_ids

				def meta = [batch_id: batch_id, batch_tsv: batch_tsv]

				def samples = sample_ids.collect { sid ->
					def pair = sample_map[sid]
					if (!pair) throw new IllegalStateException("Missing annotated sample: $sid")
					[sid, pair[0], pair[1]]  // [sample_id, fasta, gff]
				}

				[meta, samples]
			}
		}
		.flatten()

	// Run submission using the batch channel
	SUBMISSION(genbank_batch_ch, params.submission_config)

	emit:
    submission_folders = SUBMISSION.out.submission_folders
}