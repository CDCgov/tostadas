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

    // Todo: We need to run GENBANK_VALIDATION per sample not per batch

    // Flatten metadata into per-sample tuples
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

    // Run GenBank validation only on the fasta
    genbank_validated_ch = sample_ch.map { meta, fasta, _gff -> [meta, fasta] } | GENBANK_VALIDATION

    // Replace the original fasta with the validated one
    validated_sample_ch = sample_ch
        .map { meta, fasta, gff -> [meta.sample_id, meta, fasta, gff] }
        .join(
            genbank_validated_ch.map { meta, validated_fasta -> [meta.sample_id, validated_fasta] }
        )
        .map { _sample_id, meta, _original_fasta, gff, validated_fasta -> [meta, validated_fasta, gff] }

    // Run annotation if requested
    if (params.annotation) {
        annotation_input_ch = validated_sample_ch.map { meta, fasta, gff -> [meta, fasta, gff] }

        if (params.organism_type == 'virus') {
            if (params.repeatmasker_liftoff && !params.vadr) {
                REPEATMASKER_LIFTOFF(annotation_input_ch.map { meta, fasta, _gff -> [meta, fasta] })
                annotation_input_ch = annotation_input_ch
                    .map { meta, fasta, _gff -> [meta.sample_id, meta, fasta] }
                    .join(REPEATMASKER_LIFTOFF.out.gff.map { meta, gff -> [meta.sample_id, gff] })
                    .map { _sample_id, meta, fasta, new_gff -> [meta, fasta, new_gff] }
            }

            if (params.vadr) {
                RUN_VADR(annotation_input_ch.map { meta, fasta, _gff -> [meta, fasta] })
                annotation_input_ch = annotation_input_ch
                    .map { meta, fasta, _gff -> [meta.sample_id, meta, fasta] }
                    .join(RUN_VADR.out.tbl.map { meta, tbl -> [meta.sample_id, tbl] })
                    .map { _sample_id, meta, fasta, new_tbl -> [meta, fasta, new_tbl] }
            }

        } else if (params.organism_type == 'bacteria' && params.bakta) {
            RUN_BAKTA(annotation_input_ch.map { meta, fasta, _gff -> [meta, fasta] })
            annotation_input_ch = annotation_input_ch
                .map { meta, _fasta, _gff -> [meta.sample_id, meta] }
                .join(RUN_BAKTA.out.gff.map { meta, gff -> [meta.sample_id, gff] })
                .join(RUN_BAKTA.out.fna.map { meta, fna -> [meta.sample_id, fna] })
                .map { _sample_id, meta, new_gff, new_fasta -> [meta, new_fasta, new_gff] }
        }

        sample_ch = annotation_input_ch
    } else {
        sample_ch = validated_sample_ch
    }

    if (params.submission) {
        // Build final batch-wise submission channel
        submission_batch_ch = sample_ch
            .map { meta, fasta, gff -> [meta.batch_id, [meta: meta, fasta: fasta, gff: gff]] }
            .groupTuple()
            .map { batch_id, samples ->
                def missingFasta = samples.any { s ->
                    !s.fasta || !file(s.fasta).exists()
                }
                def meta = [
                    batch_id : batch_id,
                    batch_tsv: samples[0].meta.batch_tsv
                ]
                def enabledDatabases = missingFasta ? [] : ['genbank'] 
                return tuple(meta, samples, enabledDatabases)
            }
        }
        

        // Run submission using the batch channel
        SUBMISSION(submission_batch_ch, // meta: [sample_id, batch_id, batch_tsv], samples: [ [meta, fq1, fq2, nnp], ... ]), enabledDatabases (list)
                params.submission_config)

	emit:
    submission_batch_folder = params.submission ? SUBMISSION.out.submission_batch_folder : null
}