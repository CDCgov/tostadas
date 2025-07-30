#!/usr/bin/env nextflow
nextflow.enable.dsl=2

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

	// Input Excel from BIOSAMPLE_AND_SRA with accession IDs
	excel_ch = file(params.excel_with_accessions)

	GENBANK_VALIDATION(excel_ch)

	sample_ch = excel_ch.flatMap { ... }  // parse rows into [meta, fasta] etc.

	if (params.annotation) {
		// same logic for annotation choice (bakta, vadr, repeatmasker_liftoff)
	}

	// build submission batch for genbank only
	genbank_batch_ch = sample_ch -> ... // similar to previous batching logic

	// Submit to GenBank
	SUBMISSION(genbank_batch_ch, params.submission_config, null)

	// Fetch accessions for GenBank
	FETCH_ACCESSIONS(SUBMISSION.out.submission_folders)
}
