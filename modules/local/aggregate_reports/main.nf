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

    output:
    path("submission_report.csv"), emit: submission_report

    script:
    """
    aggregate_reports.py $report_csvs
    
    """
}
