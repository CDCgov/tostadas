/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN METADATA VALIDATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process METADATA_VALIDATION {

    //label 'main'
    
    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' :
        'staphb/tostadas:latest' }"

    publishDir "$params.output_dir", mode: 'copy', overwrite: params.overwrite_output

    input:
    val signal
    path meta_path

    script:
    """
    validate_metadata.py --meta_path $meta_path --output_dir $params.val_output_dir \
    --custom_fields_file $params.custom_fields_file --validate_custom_fields $params.validate_custom_fields
    """

    output:
    path "$params.val_output_dir/*/tsv_per_sample/*.tsv", emit: tsv_Files
    path "$params.val_output_dir/*/tsv_per_sample", emit: tsv_dir
    path "$params.val_output_dir/*/errors", emit: errors
}