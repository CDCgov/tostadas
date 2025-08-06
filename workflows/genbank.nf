#!/usr/bin/env nextflow
nextflow.enable.dsl=2

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
						 GET NECESSARY MODULES OR SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// get the utility processes / subworkflows
include { validateParameters; paramsSummaryLog; samplesheetToList 	} from 'plugin/nf-schema'

// get metadata validation processes
include { GENBANK_VALIDATION                               			} from "../modules/local/genbank_validation/main"

// get viral annotation process/subworkflows
include { REPEATMASKER_LIFTOFF                            			} from "../subworkflows/local/repeatmasker_liftoff"
include { RUN_VADR                                          		} from "../subworkflows/local/vadr"

// get BAKTA subworkflow
include { RUN_BAKTA                                         		} from "../subworkflows/local/bakta"

// get submission related process/subworkflows
include { SUBMISSION		                                		} from "../subworkflows/local/submission"
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
	take:
	accession_augmented_xlsx

	main:
	validateParameters()
	log.info paramsSummaryLog(workflow)

	// Run GenBank validation
	// Change this to use sample_id, fasta, gff as inputs [leave tsv out]

	// Convert to TSV
	excel_tsv_ch = Channel.of(accession_augmented_xlsx)
		.map { excel ->
			def tsv = excel.getBaseName() + '.tsv'
			"""
			mlr --icsv --otsv cat "$excel" > "$tsv"
			"""
			return file(tsv)
		}

	// Split TSV into batches
	metadata_batch_ch = excel_tsv_ch
		.splitCsv(header: true, sep: '\t')
		.collate(params.batch_size)
		.map { rows ->
			def batch_id = "batch_" + UUID.randomUUID().toString()[0..7]
			def batch_tsv = file("${batch_id}.tsv")
			
			// Write the batch to TSV
			batch_tsv.text = rows.join('\n')
			
			def meta = [
				batch_id : batch_id,
				batch_tsv: batch_tsv
			]
			return [meta, batch_tsv]
		}

	// Extract FASTA and GFF file paths from metadata batches
	sample_ch = metadata_batch_ch.flatMap { meta, _batch_tsv ->
		def rows = meta.batch_tsv.splitCsv(header: true, sep: '\t')
		return rows.collect { row ->
			def sample_id = row.sample_name?.trim()
			def fasta = row.containsKey('fasta_path') ? trimFile(row.fasta_path) : null
			def gff   = row.containsKey('gff_path')   ? trimFile(row.gff_path)   : null

			def sample_meta = [
				batch_id : meta.batch_id,
				batch_tsv: meta.batch_tsv,
				sample_id: sample_id
			]
			return [sample_meta, fasta, gff]
		}
	}

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
	SUBMISSION(genbank_batch_ch, 
			   params.submission_config)

	emit:
    submission_batch_folder = SUBMISSION.out.submission_batch_folder
}