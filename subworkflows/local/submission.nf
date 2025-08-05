#!/usr/bin/env nextflow 

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

include { PREP_SUBMISSION       } from '../../modules/local/prep_submission/main'
include { SUBMIT_SUBMISSION     } from '../../modules/local/submit_submission/main'
include { FETCH_SUBMISSION      } from '../../modules/local/fetch_submission/main'
include { AGGREGATE_REPORTS     } from '../../modules/local/aggregate_reports/main'

workflow SUBMISSION {
    take:
        submission_ch         // (meta: [batch_id: ..., batch_tsv: ...], samples: [ [meta, fasta, fq1, fq2, nnp, gff], ... ]), enabledDatabases (list)
        submission_config

    main:
        submission_config_file = file(submission_config)

        PREP_SUBMISSION(submission_ch, submission_config_file)
            .set { submission_files }

        SUBMIT_SUBMISSION(submission_files, submission_config_file)

        // set the channel to only include the log if doing a dry run
        submission_result_ch = params.dry_run 
            ? SUBMIT_SUBMISSION.out.submission_log
            : SUBMIT_SUBMISSION.out.submission_files

        submission_result_ch.set { submission_output_dir_ch }

    emit:
        submission_folders = submission_output_dir_ch //either a batch directory or a submission log
}
