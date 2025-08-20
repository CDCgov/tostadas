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
        submission_ch         // (meta: [batch_id: ..., batch_tsv: ...], samples: [ [meta, fasta, fq1, fq2, nnp, gff], ... ]), enabledDatabases (list)
        submission_config

    main:
        submission_config_file = file(submission_config)

        PREP_SUBMISSION(submission_ch, submission_config_file)

        PREP_SUBMISSION.out.submission_files
            .set { submission_batch_folder }

        SUBMIT_SUBMISSION(submission_batch_folder, submission_config_file)

    emit:
        submission_batch_folder = SUBMIT_SUBMISSION.out.submission_batch_folder
}
