include { FETCH_REPORTS                              } from '../../modules/local/fetch_reports/main'
include { AGGREGATE_REPORTS                          } from '../../modules/local/aggregate_reports/main'
include { JOIN_ACCESSIONS_WITH_METADATA              } from '../../modules/local/join_accessions_with_metadata/main'

workflow AGGREGATE_SUBMISSIONS {
    take:
      wait_value // used to enforce ordering in main workflow
      submission_dirs // works for one or more batch_dir(s)
      submission_config
      validated_metadata_tsv

    main:
      FETCH_REPORTS(submission_dirs, file(submission_config))

      // Collect the individual batch submission_reports
      FETCH_REPORTS.out.submission_report
                .collect()
                .set { all_report_csvs }

      // Concatenate batch csvs for all samples
      AGGREGATE_REPORTS(all_report_csvs)

      // Concatenate the batch TSVs, then add the (optional) accession IDs to them
      JOIN_ACCESSIONS_WITH_METADATA(validated_metadata_tsv, AGGREGATE_REPORTS.out.submission_report)

    emit:
      all_report_csvs = all_report_csvs
      accession_augmented_xlsx = JOIN_ACCESSIONS_WITH_METADATA.out.updated_excel
}