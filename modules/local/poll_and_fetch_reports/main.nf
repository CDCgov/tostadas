/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                              POLL AND FETCH SUBMISSION REPORTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process POLL_AND_FETCH_REPORTS {
    tag "${meta.batch_id}"

    conda(params.env_yml)
    container 'docker.io/staphb/tostadas:latest'

    errorStrategy 'retry'
    maxRetries 3

    input:
    tuple val(meta), path(submission_folder)
    path(submission_config)

    output:
    path("${submission_folder}/fetch_submission.log"), emit: submission_log
    path("${submission_folder}/*.csv"), emit: submission_report, optional: true
    path("${submission_folder}/**/report.xml"), emit: report_xml, optional: true

    script:
    def test_flag = params.prod_submission == false ? '--test' : ''
    def dry_run_flag = params.dry_run == true ? '--dry_run' : ''
    """
    poll_and_fetch_reports.py \
        --submission_folder ${submission_folder} \
        --config_file ${submission_config} \
        --identifier ${params.metadata_basename} \
        --batch_id ${meta.batch_id} \
        --submission_mode ${params.submission_mode} \
        --initial_interval ${params.poll_initial_interval} \
        --max_interval ${params.poll_max_interval} \
        --timeout ${params.poll_timeout} \
        ${test_flag} \
        ${dry_run_flag}
    """
}
