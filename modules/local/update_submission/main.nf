/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    UPDATE SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process UPDATE_SUBMISSION {

    // label 'main'

    publishDir "$params.output_dir/$params.submission_output_dir/", mode: 'copy', overwrite: true

    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
    val wait_time
    path submission_config
    path submission_output
    path submission_log
    
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    script:
    """
    submission.py check_submission_status \
        --organism $params.organism \
        --submission_dir .  \
        --submission_name $submission_output $test_flag
    """

    output:
    path "$submission_output", emit: submission_files
    path "${submission_output}_submission_log.csv", emit: submission_log
} 
