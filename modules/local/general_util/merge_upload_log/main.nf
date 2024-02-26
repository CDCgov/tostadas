/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                CLEANUP FILES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process MERGE_UPLOAD_LOG {

    //label 'main'
    container 'staphb/tostadas:latest'

    publishDir "$params.output_dir/$params.submission_output_dir/$annotation_name", mode: 'copy', overwrite: params.overwrite_output

    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $params.env_yml")
        }
    }

    input:
    path submission_files
    path submission_log
    val annotation_name

    script:
    """
    merge_submission_logs.py --submission_dir .
    #submission_utility.py --merge_upload_log true --batch_name $params.batch_name
    """

    output:
    path "submission_log.csv", emit: submission_log
}