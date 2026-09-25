#!/usr/bin/env nextflow

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION (GENBANK)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { PREP_SUBMISSION   as PREP_GENBANK   } from '../../modules/local/prep_submission/main'
include { SUBMIT_SUBMISSION as SUBMIT_GENBANK } from '../../modules/local/submit_submission/main'

workflow SUBMISSION_GENBANK {
    take:
        submission_ch         // (meta: [batch_id: ..., batch_tsv: ...], samples: [ [meta, fasta, fq1, fq2, nnp, gff], ... ]), enabledDatabases (list)
        submission_config

    main:
        submission_config_file = file(submission_config)

        // Extract batch_tsv as a separate path channel so Nextflow stages
        // the file into the work directory (required for cloud executors)
        batch_tsv_ch = submission_ch.map { meta, _samples, _dbs -> meta.batch_tsv }

        PREP_GENBANK(submission_ch, batch_tsv_ch, submission_config_file)

        PREP_GENBANK.out.submission_files
            .set { submission_batch_folder }

        SUBMIT_GENBANK(submission_batch_folder, submission_config_file)

        // Print message if dry_run is enabled
        if (params.dry_run) {
            log.info "Workflow ends here because dry_run is set to true. Please see submission log files for details."
        }

    emit:
        submission_batch_folder = SUBMIT_GENBANK.out.submission_batch_folder
}
