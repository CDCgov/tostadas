/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    UPDATE SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process UPDATE_SUBMISSION {

    // label 'main'

    // publishDir "$params.output_dir/$params.submission_output_dir/$annotation_name", mode: 'copy', overwrite: true

    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'cdcgov/seqsender-dev' : 'cdcgov/seqsender-dev' }"

    input:   
    val wait_signal
    path submission_config
    path submission_output
    path submission_log
    val annotation_name
    
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
