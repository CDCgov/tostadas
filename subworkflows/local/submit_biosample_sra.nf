include { PREP_SUBMISSION                               } from '../../modules/local/prep_submission/main'
include { SUBMIT_SUBMISSION                             } from '../../modules/local/submit_submission/main'
include { WAIT                                          } from '../../modules/local/general_util/wait/main'

workflow SUBMIT_BIOSAMPLE_SRA {
    take:
      submission_ch
      submission_config
      wait_time

    main:
      WAIT(wait_time)
      PREP_SUBMISSION(submission_ch, file(submission_config))        // emits submission_files
      SUBMIT_SUBMISSION(PREP_SUBMISSION.out, file(submission_config)) // emits submission_with_folder

    emit:
      submission_with_folder = SUBMIT_SUBMISSION.out
}
