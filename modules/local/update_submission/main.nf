/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    UPDATE SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process UPDATE_SUBMISSION {

    //label 'main'
    
    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    publishDir "$params.output_dir/$params.submission_output_dir/$annotation_name", mode: 'copy', overwrite: true

    input:
    val wait_signal
    path submission_config
    path submission_output
    val annotation_name
        
    script:
    """
    run_submission.py --config $submission_config --update true --unique_name $params.batch_name --sample_name ${submission_output.getExtension()}
    """

    output:
    path "$params.batch_name.${submission_output.getExtension()}", emit: submission_files
} 
