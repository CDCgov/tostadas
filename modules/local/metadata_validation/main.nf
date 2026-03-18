/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN METADATA VALIDATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process METADATA_VALIDATION {

    conda(params.env_yml)
    container 'docker.io/staphb/tostadas:latest'

    input:
    path meta_path
    path submission_config

    output:
    path "batched_tsvs/*.tsv", emit: tsv_files
    path "batched_tsvs/batch_summary.json", optional: true, emit: json
    path "error.txt", optional: true, emit: errors

    script:
        def remove_demographic_info = params.remove_demographic_info == true ? '--remove_demographic_info' : ''
        def validate_custom_fields = params.validate_custom_fields == true ? '--validate_custom_fields' : ''
        def fasta_dir = params.fasta_dir ? "--fasta_dir ${params.fasta_dir}" : ''

        """
        validate_metadata.py \
            --meta_path $meta_path \
            --batch_size $params.batch_size \
            --output_dir . \
            --custom_fields_file $params.custom_fields_file \
            --date_format_flag $params.date_format_flag \
            $remove_demographic_info $validate_custom_fields \
            --config_file $submission_config \
            --biosample_fields_key $params.biosample_fields_key \
            $fasta_dir
        """
}