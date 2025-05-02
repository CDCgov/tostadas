/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            SUMMARIZE SUBMISSION REPORTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process AGGREGATE_REPORTS {

    publishDir "${params.output_dir}/${params.submission_output_dir}/${params.metadata_basename}",
        mode: 'copy',
        overwrite: params.overwrite_output

    input:
    path(report_csvs)

    output:
    path("submission_report.csv")

    script:
    """
    set -x
    cat ${report_csvs.join(' ')} | head -n 1 > submission_report.csv
    for f in ${report_csvs.join(' ')}; do
        tail -n +2 "\$f" >> submission_report.csv
    done
    """
}
