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
include { CHECK_VALIDATION_ERRORS							} from "../modules/local/check_validation_errors/main"
include { WRITE_VALIDATED_FULL_TSV                          } from "../modules/local/write_validated_full_tsv/main"
include { REBATCH_METADATA                                  } from "../modules/local/rebatch_metadata/main"
include { UPDATE_SUBMISSION                                 } from "../modules/local/update_submission/main"
include { SUBMISSION		                                } from "../subworkflows/local/submission"

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
									MAIN WORKFLOW
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

workflow BIOSAMPLE_UPDATE {

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
			log.info "Validation failed. Please check ${params.outdir}/${params.metadata_basename}/${params.validation_outdir}/error.txt"
			workflow.abort()
		}
	}

    METADATA_VALIDATION.out.tsv_files
		.collect()
		.set { validated_tsvs_list }

	WRITE_VALIDATED_FULL_TSV ( validated_tsvs_list )

    // rebatch here using params.submission_config/validation_outputs/batched_tsvs/batch_summary.json

    // Step 3: locate old batch_summary.json
    def batch_summary = file("${params.original_submission_outdir}/../${params.validation_outdir}/batched_tsvs/batch_summary.json")
    if (!batch_summary.exists()) {
        log.error "Missing batch_summary.json at: ${batch_summary}"
        workflow.abort()
    }

    // Step 4: rebatch new metadata to match original batch groupings
    REBATCH_METADATA(
        WRITE_VALIDATED_FULL_TSV.out.validated_concatenated_tsv,
        batch_summary
    )

    rebatch_ch = REBATCH_METADATA.out.rebatch_tuple
        .map { tsv_file, json_file ->
            def parsed = new groovy.json.JsonSlurper().parseText(json_file.text)
            parsed.meta.batch_tsv = tsv_file.toString()  // path is guaranteed to exist
            tuple(parsed.meta, parsed.samples, parsed.enabled)
        }

    if (params.dry_run) {
        log.info "Workflow ends here because dry_run is set to true. Please see submission log files for details."
    }

    orig_submission_dir_ch = Channel.fromPath("${params.original_submission_outdir}")


    // Step 5: run update-submission on each rebatch
    UPDATE_SUBMISSION(
        rebatch_ch,
        orig_submission_dir_ch,
        params.submission_config
    )

    emit:
    validated_concatenated_tsv = WRITE_VALIDATED_FULL_TSV.out.validated_concatenated_tsv
    updated_submission_batches = UPDATE_SUBMISSION.out.submission_batch_folder
}