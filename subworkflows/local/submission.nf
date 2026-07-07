#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { PREP_SUBMISSION       } from '../../modules/local/prep_submission/main'
include { SUBMIT_SUBMISSION     } from '../../modules/local/submit_submission/main'

workflow SUBMISSION {
    take:
        submission_ch         // tuple(meta, samples, enabledDatabases, batch_tsv, fastas, gffs, fq1s, fq2s, nnps) — file lists are staged into the PREP_SUBMISSION container by declaring them as `path` inputs; sample paths must not be resolved from the raw workDir URI stored in the samples map (fails on cloud executors)
        submission_config

    main:
        submission_config_file = file(submission_config)

        PREP_SUBMISSION(submission_ch, submission_config_file)

        PREP_SUBMISSION.out.submission_files
            .set { submission_batch_folder }

        SUBMIT_SUBMISSION(submission_batch_folder, submission_config_file)

        // Print message if dry_run is enabled
        if (params.dry_run) {
            log.info "Workflow ends here because dry_run is set to true. Please see submission log files for details."
        }

    emit:
        submission_batch_folder = SUBMIT_SUBMISSION.out.submission_batch_folder
}
