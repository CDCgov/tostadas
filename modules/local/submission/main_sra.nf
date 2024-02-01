/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process SUBMISSION {

    label 'main'

    publishDir "$params.output_dir/$params.submission_output_dir/$annotation_name", mode: 'copy', overwrite: params.overwrite_output

    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $params.env_yml")
        }
    }

    input:
    tuple val(meta), path(validated_meta_path)
    path submission_config
    path req_col_config
    val annotation_name

    output:
    path "$params.batch_name.${validated_meta_path.getBaseName()}", emit: submission_files 

    script:
    """
    submission.py \
    --command submit \
    --unique_name $params.batch_name \
    --fasta null \
    --metadata $validated_meta_path \
    --gff null \
    --config $submission_config \
    --req_col_config $req_col_config \
    --send_email $params.send_submission_email \
    --test_or_prod $params.submission_prod_or_test       
    """
}