#!/usr/bin/env nextflow
nextflow.enable.dsl=2

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
						 GET NECESSARY MODULES OR SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// get the utility processes / subworkflows
include { validateParameters; paramsSummaryLog; samplesheetToList } from 'plugin/nf-schema'
include { METADATA_VALIDATION                               } from "../modules/local/metadata_validation/main"
include { CHECK_VALIDATION_ERRORS							} from "../modules/local/check_validation_errors/main.nf"
include { WRITE_VALIDATED_FULL_TSV                          } from "../modules/local/write_validated_full_tsv/main"
include { SUBMISSION		                                } from "../subworkflows/local/submission"

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
									MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

// Global method to trim white space from file paths
def trimFile(path) {
    return path?.trim() ? file(path.trim()) : null
}

workflow BIOSAMPLE_AND_SRA {
	main:
	// Validate input parameters
	validateParameters()

	// Print summary of supplied parameters
	log.info paramsSummaryLog(workflow)

	// Run metadata validation process
	METADATA_VALIDATION ( file(params.meta_path) )

	// Enforce error checking before anything else continues
    CHECK_VALIDATION_ERRORS(METADATA_VALIDATION.out.errors)

    // Get status from the check
	CHECK_VALIDATION_ERRORS.out.status.subscribe { status ->
		if (status == "ERROR") {
			println "Validation failed. Please check ${params.outdir}/${params.metadata_basename}/${params.val_output_dir}/error.txt"
			workflow.abort()
		}
	}

	metadata_batch_ch = METADATA_VALIDATION.out.tsv_files
		.flatten()
		.map { batch_tsv ->
			def meta = [
				batch_id: batch_tsv.getBaseName(),
				batch_tsv: batch_tsv
			]
			[meta, batch_tsv]
		}

	// Aggregate the tsvs for concatenation
	METADATA_VALIDATION.out.tsv_files
		.collect()
		.set { validated_tsvs_list }

	WRITE_VALIDATED_FULL_TSV ( validated_tsvs_list )
		
	// Generate the (per-sample) fasta and fastq paths
	sample_ch = metadata_batch_ch.flatMap { meta, _files -> 
		def rows = meta.batch_tsv.splitCsv(header: true, sep: '\t')
		return rows.collect { row -> 
			def sample_id = row.sample_name?.trim()
			def fq1   = row.containsKey('int_illumina_sra_file_path_1') ? trimFile(row.int_illumina_sra_file_path_1) : null
			def fq2   = row.containsKey('int_illumina_sra_file_path_2') ? trimFile(row.int_illumina_sra_file_path_2) : null
			def nnp   = row.containsKey('int_nanopore_sra_file_path_1') ? trimFile(row.int_nanopore_sra_file_path_1) : null

			def sample_meta = [
				batch_id  : meta.batch_id,
				batch_tsv: meta.batch_tsv,
				sample_id: sample_id
			]
			return [sample_meta, fq1, fq2, nnp]
		}
	}

	// Check for valid submission inputs and make batch channel
	submission_batch_ch = sample_ch
		.map { meta, fq1, fq2, nnp ->
			[meta.batch_id, [meta: meta, fq1: fq1, fq2: fq2, nanopore: nnp]]
		}
		.groupTuple()
		.map { batch_id, sample_maps ->

			def enabledDatabases = [] as Set
			def sraWarnings = [] as List

			sample_maps.each { sample ->
				def sid = sample.meta.sample_id
				def fq1Exists = sample.fq1 && file(sample.fq1).exists()
				def fq2Exists = sample.fq2 && file(sample.fq2).exists()
				def nnpExists = sample.nanopore && file(sample.nanopore).exists()

				def hasIllumina = fq1Exists && fq2Exists
				def hasNanopore = nnpExists

				//log.info "Sample ${sid} | fq1: ${sample.fq1} (exists: ${fq1Exists}) | fq2: ${sample.fq2} (exists: ${fq2Exists}) | nnp: ${sample.nanopore} (exists: ${nnpExists})"

				if (params.sra && (hasIllumina || hasNanopore)) {
					enabledDatabases << "sra"
				}
				if (params.sra && !(hasIllumina || hasNanopore)) {
					sraWarnings << sid
				}
				if (params.biosample) {
					enabledDatabases << "biosample"
				}
			}

			if (sraWarnings) {
				log.warn "SRA submission will be skipped for batch ${batch_id} due to missing data for samples: ${sraWarnings.join(', ')}"
			}

			def meta = [
				batch_id : batch_id,
				batch_tsv: sample_maps[0].meta.batch_tsv
			]

			return tuple(meta, sample_maps, enabledDatabases as List)
		}

	SUBMISSION(
		submission_batch_ch, // meta: [sample_id, batch_id, batch_tsv], samples: [ [meta, fq1, fq2, nnp], ... ]), enabledDatabases (list)
	 	params.submission_config
	)

	emit:
	validated_concatenated_tsv = WRITE_VALIDATED_FULL_TSV.out.validated_concatenated_tsv // contains data for all batches of samples
    submission_batch_folder = SUBMISSION.out.submission_batch_folder // one batch submission folder 
}
