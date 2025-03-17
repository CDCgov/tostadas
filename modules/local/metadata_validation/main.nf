/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN METADATA VALIDATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process METADATA_VALIDATION {

    // label 'main'

    //errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    //maxRetries 5

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
    path meta_path

    // get absolute path if relative dir passed
    def resolved_output_dir = params.output_dir.startsWith('/') ? params.output_dir : "${baseDir}/${params.output_dir}"
    def remove_demographic_info = params.remove_demographic_info == true ? '--remove_demographic_info' : ''
    def validate_custom_fields = params.validate_custom_fields == true ? '--validate_custom_fields' : ''

    // Resolve submission_config path
    def resolved_submission_config = params.submission_config.startsWith('/') ? params.submission_config : "${baseDir}/${params.submission_config}"
    
    script:
        """
        validate_metadata.py \
            --meta_path $meta_path \
            --project_dir $projectDir \
            --output_dir . \
            --custom_fields_file $params.custom_fields_file \
            --validate_custom_fields $params.validate_custom_fields \
            --date_format_flag $params.date_format_flag \
            $remove_demographic_info $validate_custom_fields \
            ${params.fetch_reports_only ? "--find_paths" : ""} \
            ${params.fetch_reports_only ? "--path_to_existing_tsvs ${resolved_output_dir}/${params.val_output_dir}" : ""} \
            --config_file $resolved_submission_config \
            --biosample_fields_key $params.biosample_fields_key
        """
        
    output:
    path "*/tsv_per_sample/*.tsv", emit: tsv_Files
    // path "*/tsv_per_sample", emit: tsv_dir
    path "*/errors", emit: errors
}