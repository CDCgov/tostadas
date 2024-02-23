/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    UPDATE SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process UPDATE_SUBMISSION {

    label 'main'

    publishDir "$params.output_dir/$params.submission_output_dir/$annotation_name", mode: 'copy', overwrite: true

    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $params.env_yml")
        }
    }

    input:
    tuple val(meta), path(validated_meta_path)    
    val wait_signal
    path submission_config
    path submission_output
    val annotation_name
    
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    script:
    """
    submission.py check_submission_status \
        --organism $params.organism \
        --submission_dir .  \
        --submission_name $meta.id $test_flag
    """

    output:
    path "$params.${submission_output.getExtension()}", emit: submission_files
} 
