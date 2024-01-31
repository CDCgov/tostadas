/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    UPDATE SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process UPDATE_SUBMISSION {

    label 'main'

    errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 5

    publishDir "$params.output_dir/$params.submission_output_dir/$annotation_name", mode: 'copy', overwrite: true

    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $params.env_yml")
        }
    }

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
