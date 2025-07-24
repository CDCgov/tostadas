include { WAIT                                          } from '../../modules/local/general_util/wait/main'
include { FETCH_SUBMISSION                              } from '../../modules/local/fetch_submission/main'
include { AGGREGATE_REPORTS                             } from '../../modules/local/aggregate_reports/main'

workflow FETCH_ACCESSIONS {
    take:
      submission_dir
      submission_config
      wait_time

    main:
      WAIT(wait_time)
      FETCH_SUBMISSION(wait_time, submission_dir, file(submission_config))
        .out.submission_report.collect().set { all_report_csvs }
      AGGREGATE_REPORTS(all_report_csvs)

    emit:
      report_csvs = all_report_csvs
}
