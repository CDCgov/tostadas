/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                CLEANUP FILES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process MERGE_UPLOAD_LOG {

    publishDir "$params.output_dir/$params.submission_output_dir/$annotation_name", mode: 'copy', overwrite: params.overwrite_output

    input:
    path submission_files
    val annotation_name

    script:
    """
    submission_utility.py --merge_upload_log true --batch_name $params.batch_name
    """

    output:
    path "upload_log.csv", emit: upload_log
}