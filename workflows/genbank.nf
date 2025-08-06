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
include { CREATE_BATCH_TSVS                               			} from "../modules/local/create_batch_tsvs/main"
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

    // Create batches from Excel
    CREATE_BATCH_TSVS(accession_augmented_xlsx, params.batch_size)

    metadata_batch_ch = CREATE_BATCH_TSVS.out.tsv_files
        .flatten()
            .map { batch_tsv ->
                def meta = [
                    batch_id: batch_tsv.getBaseName(),
                    batch_tsv: batch_tsv
                ]
                [meta, batch_tsv]
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

	// Run GenBank validation
	GENBANK_VALIDATION(sample_ch)

	// Construct the per-sample channel with: sample_id, validated_fasta, validated_gff
	validated_ch = GENBANK_VALIDATION.out

    // Run annotation if requested
    if (params.annotation) {
        annotation_ch = validated_ch.map { meta, fasta, gff -> [meta, fasta] }

        if (params.species in ['mpxv', 'variola', 'rsv', 'virus']) {
            if (params.repeatmasker_liftoff && !params.vadr) {
                REPEATMASKER_LIFTOFF(annotation_ch)
                annotation_ch = annotation_ch.join(REPEATMASKER_LIFTOFF.out.gff)
            }

            if (params.vadr) {
                RUN_VADR(annotation_ch)
                annotation_ch = annotation_ch.join(RUN_VADR.out.tbl)
            }

        } else if (params.species == 'bacteria' && params.bakta) {
            RUN_BAKTA(annotation_ch)
            annotation_ch = annotation_ch
                | join(RUN_BAKTA.out.gff)
                | join(RUN_BAKTA.out.fna)
                | map { meta, _orig_fasta, gff, fasta -> [meta, fasta, gff] }
        }

        // Join annotation results back into full sample tuples
        sample_ch = sample_ch.map { meta, _fasta, _gff -> [meta] }
            .join(annotation_ch)
            .map { meta, fasta, gff -> [meta, fasta, gff] }
    } else {
        sample_ch = validated_ch
    }

    // Build final batch-wise submission channel
    submission_batch_ch = sample_ch
        .map { meta, fasta, gff -> [meta.batch_id, [meta: meta, fasta: fasta, gff: gff]] }
        .groupTuple()
        .map { batch_id, samples ->
            def missingFiles = [] as Set

            samples.each { s ->
                def sid = s.meta.sample_id
                if (params.genbank) {
                    if (!s.fasta || !file(s.fasta).exists()) missingFiles << "${sid}:fasta"
                    if (!s.gff   || !file(s.gff).exists())   missingFiles << "${sid}:gff"
                }
            }

            if (missingFiles) {
                log.warn "Skipping batch ${batch_id} due to missing files: ${missingFiles.join(', ')}"
                return null
            }

            def meta = [
                batch_id : batch_id,
                batch_tsv: samples[0].meta.batch_tsv
            ]
			// todo: only add genbank if files not missing
            return tuple(meta, samples, ['genbank'])
        }
        .filter { it != null }


	// Run submission using the batch channel
	SUBMISSION(submission_batch_ch, 
			   params.submission_config)

	emit:
    submission_batch_folder = SUBMISSION.out.submission_batch_folder
}