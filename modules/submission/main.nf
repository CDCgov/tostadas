/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process SUBMISSION {

    label 'main'

    errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 5

    publishDir "$params.output_dir/$params.submission_output_dir/$annotation_name", mode: 'copy', overwrite: params.overwrite_output

    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $params.env_yml")
        }
    }

    input:
    path validated_meta_path
    path lifted_fasta_path
    path lifted_gff_path
    val entry_flag
    path submission_config
    path req_col_config
    val annotation_name

    script:
    """
    run_submission.py --submission_database $params.submission_database --unique_name $params.batch_name --lifted_fasta_path $lifted_fasta_path \
    --validated_meta_path $validated_meta_path --lifted_gff_path $lifted_gff_path --config $submission_config --prod_or_test $params.submission_prod_or_test \
    --req_col_config $req_col_config --update false --send_submission_email $params.send_submission_email --sample_name ${validated_meta_path.getSimpleName()}
    """

    output:
    path "$params.batch_name.${validated_meta_path.getSimpleName()}", emit: submission_files 
}