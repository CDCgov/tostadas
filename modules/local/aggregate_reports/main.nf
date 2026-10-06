/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            SUMMARIZE SUBMISSION REPORTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process AGGREGATE_REPORTS {
    
    conda(params.env_yml)
    container 'docker.io/staphb/tostadas:latest'

    input:
    path(report_csvs)
    path(metadata_tsv)

    output:
    path("submission_report.csv"), emit: submission_report

    script:
    """
    aggregate_reports.py --metadata_tsv "${metadata_tsv}" $report_csvs
    
    """
}
