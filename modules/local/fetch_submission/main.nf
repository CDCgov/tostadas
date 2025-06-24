/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    FETCH SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process FETCH_SUBMISSION {

    publishDir "${params.output_dir}/${params.final_submission_output_dir}/${params.metadata_basename}",
            mode: 'copy',
            overwrite: params.overwrite_output

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
    val(wait_time)
    tuple val(meta), val(samples), val(enabledDatabases), path(submission_folder)
    path(submission_config)

    output:
    tuple val(meta), path("${meta.batch_id}"), emit: submission_files
    path("${meta.batch_id}/fetch_submission.log"), emit: submission_log, optional: true
    path("${meta.batch_id}/${meta.batch_id}.csv"), emit: submission_report

    script:
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    def dry_run_flag = params.dry_run == true ? '--dry_run' : ''

    // Build database argument list
    def databases_flag = enabledDatabases.join(' ')
    def batch_dir = meta.batch_id

    """
    mkdir -p ${batch_dir} && \
    fetch_submission.py \
        --submission_folder ${submission_folder} \
        --config_file ${submission_config} \
        --identifier ${params.metadata_basename} \
        --batch_id ${meta.batch_id} \
        --databases ${databases_flag} \
        --submission_mode ${params.submission_mode} \
        ${test_flag} \
        ${dry_run_flag}
    """
}