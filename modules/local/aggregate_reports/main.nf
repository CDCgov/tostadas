/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            SUMMARIZE SUBMISSION REPORTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process AGGREGATE_REPORTS {

    input:
    path(report_csvs)

    output:
    path("submission_report.csv"), emit: submission_report

    script:
    """
    set -x
    cat ${report_csvs.join(' ')} | head -n 1 > submission_report.csv
    for f in ${report_csvs.join(' ')}; do
        tail -n +2 "\$f" >> submission_report.csv
    done
    """
}
