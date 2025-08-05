/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    FETCH SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process FETCH_REPORTS {

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'docker.io/staphb/tostadas:latest' : 'docker.io/staphb/tostadas:latest' }"

    input:
    tuple val(meta), path(submission_folder)
    path(submission_config)

    output:
    path("${submission_folder}/fetch_submission.log"), emit: submission_log, optional: true
    path("${submission_folder}/*.csv"), emit: submission_report

    script:
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    def dry_run_flag = params.dry_run == true ? '--dry_run' : ''

    """
    fetch_submission.py \
        --submission_folder ${submission_folder} \
        --config_file ${submission_config} \
        --identifier ${params.metadata_basename} \
        --batch_id ${meta.batch_id} \
        --submission_mode ${params.submission_mode} \
        ${test_flag} \
        ${dry_run_flag}
    """
}