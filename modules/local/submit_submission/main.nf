/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process SUBMIT_SUBMISSION {

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'docker.io/staphb/tostadas:latest' : 'docker.io/staphb/tostadas:latest' }"

    input:
    tuple val(meta), path(submission_files)
    path(submission_config)

    script:
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    def send_submission_email = params.send_submission_email == true ? '--send_email' : ''
    def dry_run = params.dry_run == true ? '--dry_run' : ''

    // Use a clean subdirectory as the output directory
    def outdir = "submission_output_${meta.batch_id}"

    """
    mkdir -p ${outdir} &&
    submission.py \
        --submission_folder ${submission_files} \
        --submission_name ${meta.batch_id} \
        --config_file ${submission_config}  \
        --identifier ${params.metadata_basename} \
        --submission_mode ${params.submission_mode} \
        $test_flag \
        $send_submission_email \
        $dry_run 
    """

    output:
    tuple val(meta), path("${meta.batch_id}"), emit: submission_files
    path("${meta.batch_id}/submission.log"), emit: submission_log, optional: true
}