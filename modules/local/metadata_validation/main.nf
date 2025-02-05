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

    // get absolute path if relative dir passed
    def resolved_output_dir = params.output_dir.startsWith('/') ? params.output_dir : "${baseDir}/${params.output_dir}"

    script:
        """
        validate_metadata.py \
            --meta_path $meta_path \
            --output_dir . \
            --custom_fields_file $params.custom_fields_file \
            --validate_custom_fields $params.validate_custom_fields \
            ${params.fetch_reports_only ? "--find_paths" : ""} \
            ${params.fetch_reports_only ? "--path_to_existing_tsvs ${resolved_output_dir}/${params.val_output_dir}" : ""} \ 
        """

    output:
    path "*/tsv_per_sample/*.tsv", emit: tsv_Files
    // path "*/tsv_per_sample", emit: tsv_dir
    path "*/errors", emit: errors
}