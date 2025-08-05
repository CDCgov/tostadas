include { FETCH_REPORTS                              } from '../../modules/local/fetch_reports/main'
include { AGGREGATE_REPORTS                          } from '../../modules/local/aggregate_reports/main'

workflow FETCH_ACCESSIONS {
    take:
      submission_dir
      submission_config

    main:
      FETCH_REPORTS(submission_dir, file(submission_config))
      FETCH_REPORTS.out.submission_report
                .collect()
                .set { all_report_csvs }
      AGGREGATE_REPORTS(all_report_csvs)

    // todo: This needs to emit an updated metadata Excel file (too?)
    emit:
      report_csvs = all_report_csvs
}
