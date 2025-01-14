/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN METADATA VALIDATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process METADATA_VALIDATION {

    // label 'main'

    //errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    //maxRetries 5

    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
    path meta_path

    def remove_demographic_info = params.remove_demographic_info == true ? '--remove_demographic_info' : ''
    def validate_custom_fields = params.validate_custom_fields == true ? '--validate_custom_fields' : ''

    script:
    """
    validate_metadata.py \
        --meta_path $meta_path \
        --output_dir . \
        --custom_fields_file $params.custom_fields_file \
        --date_format_flag $params.date_format_flag \
        $remove_demographic_info $validate_custom_fields
    """

    output:
    path "*/tsv_per_sample/*.tsv", emit: tsv_Files
    // path "*/tsv_per_sample", emit: tsv_dir
    path "*/errors", emit: errors
}