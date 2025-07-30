#!/usr/bin/env nextflow
nextflow.enable.dsl=2

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
						 GET NECESSARY MODULES OR SUBWORKFLOWS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
// get the utility processes / subworkflows
include { validateParameters; paramsSummaryLog; samplesheetToList } from 'plugin/nf-schema'

include { GET_WAIT_TIME                                     } from "../modules/local/general_util/get_wait_time/main"

// get metadata validation processes
include { METADATA_VALIDATION                               } from "../modules/local/metadata_validation/main"

// get submission related process/subworkflows
include { SUBMISSION		                                } from "../subworkflows/local/submission"
include { FETCH_ACCESSIONS		                            } from "../subworkflows/local/fetch_accessions"

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

	// validate input parameters
	validateParameters()

	// print summary of supplied parameters
	log.info paramsSummaryLog(workflow)

	// run metadata validation process
	METADATA_VALIDATION ( file(params.meta_path) )

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
	sample_ch = metadata_batch_ch.flatMap { meta, _files -> 
		def rows = meta.batch_tsv.splitCsv(header: true, sep: '\t')
		return rows.collect { row -> 
			def sample_meta = [
				batch_id : meta.batch_id,
				batch_tsv: meta.batch_tsv,
				sample_id : row.sample_name?.trim()
			]

			def fasta = row.containsKey('fasta_path')        			? trimFile(row.fasta_path)                       : null
			def fq1   = row.containsKey('int_illumina_sra_file_path_1') ? trimFile(row.int_illumina_sra_file_path_1) 	 : null
			def fq2   = row.containsKey('int_illumina_sra_file_path_2') ? trimFile(row.int_illumina_sra_file_path_2)	 : null
			def nnp   = row.containsKey('int_nanopore_sra_file_path_1') ? trimFile(row.int_nanopore_sra_file_path_1)	 : null
			def gff    = row.containsKey('gff_path')           			? trimFile(row.gff_path)                         : null

			return [sample_meta, fasta, fq1, fq2, nnp, gff]
		}
	}

	// Check for valid submission inputs and make batch channel
    submission_batch_ch = sample_ch
		.map { batch_id, samples ->
			def enabledDatabases = [] as Set
			def sraWarnings = [] as List

			samples.each { s ->
				def sid = s.meta.sample_id
				def hasIllumina = s.fq1 && file(s.fq1).exists() && s.fq2 && file(s.fq2).exists()
				def hasNanopore = s.nnp && file(s.nnp).exists()

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
				batch_id: batch_id,
				batch_tsv: samples[0].meta.batch_tsv 
			]
			return tuple(meta, samples, enabledDatabases as List)
		}


	GET_WAIT_TIME(METADATA_VALIDATION.out.tsv_files.collect())
	SUBMISSION(
		submission_batch_ch, // meta: [sample_id, batch_id, batch_tsv], samples: [ [meta, fq1, fq2, nnp], ... ]), enabledDatabases (list)
		params.submission_config, 
		GET_WAIT_TIME.out
	)

    // Fetch accessions
    FETCH_ACCESSIONS(
        SUBMISSION.out.submission_folders,
        params.submission_config, 
		GET_WAIT_TIME.out
        )

	// Append accession_id to TSVs and merge into Excel
	// e.g., ADD_ACCESSIONS_TO_TSV(FETCH_ACCESSIONS.out.accessions, METADATA_VALIDATION.out.tsv_files)
	//       CONCATENATE_TSVS_TO_EXCEL(...)

}
