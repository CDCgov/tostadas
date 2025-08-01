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
	validateParameters()
	log.info paramsSummaryLog(workflow)

	// Run GenBank validation
	GENBANK_VALIDATION(file(params.excel_with_accessions))

	// Construct the per-sample channel with: sample_id, tsv, validated_fasta, validated_gff
	sample_ch = GENBANK_VALIDATION.out.tsv
		.map { tsv_file ->
			def rows = tsv_file.splitCsv(header: true, sep: '\t')
			rows.collect { row ->
				def sample_id = row.sample_name?.trim()
				def tsv = tsv_file
				def fasta = file(row.validated_fasta?.trim())
				def gff   = file(row.validated_gff?.trim())
				[sample_id, tsv, fasta, gff]
			}
		}
		.flatten()

	annotated_ch = sample_ch

	// Optional: run annotation and override fasta/gff if needed
	if (params.annotation) {

		if (params.species in ['mpxv', 'variola', 'rsv', 'virus']) {

			if (params.repeatmasker_liftoff && !params.vadr) {
				REPEATMASKER_LIFTOFF(sample_ch)
				annotated_ch = REPEATMASKER_LIFTOFF.out.annotated_samples
			}

			if (params.vadr) {
				RUN_VADR(sample_ch)
				annotated_ch = RUN_VADR.out.annotated_samples
			}

		} else if (params.species == 'bacteria' && params.bakta) {
			RUN_BAKTA(sample_ch)
			annotated_ch = RUN_BAKTA.out.annotated_samples
		}
	}

	// Now you have: [sample_id, tsv, fasta, gff]
	// You can now re-group these by batch or pass directly to SUBMISSION
	genbank_batch_ch = annotated_ch
		.groupTuple(by: 1)  // group by TSV path
		.map { tsv, sample_tuples ->
			def batch_id = tsv.getBaseName()
			def meta = [batch_id: batch_id, batch_tsv: tsv]
			def samples = sample_tuples.collect { [it[0], it[2], it[3]] }  // sample_id, fasta, gff
			[meta, samples]
		}

	SUBMISSION(genbank_batch_ch, params.submission_config, null)
}



//What I want to do now is test just the BIOSAMPLE_AND_SRA workflow.  I'm like to insert print statements in various places to track my channels' contents. 