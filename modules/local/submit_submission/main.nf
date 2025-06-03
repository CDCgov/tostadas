/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process SUBMISSION {

    publishDir "${params.output_dir}/${params.submission_output_dir}/${params.metadata_basename}",
           mode: 'copy',
           overwrite: params.overwrite_output

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

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
    submission.py 
        --submission_name ${meta.batch_id} \
        --config_file $submission_config  \
        --identifier ${params.metadata_basename} \
        --submission_mode $params.submission_mode \
        $test_flag \
        $send_submission_email \
        $dry_run \
    """

    output:
    tuple val(meta), path("${meta.batch_id}"), emit: submission_files
}