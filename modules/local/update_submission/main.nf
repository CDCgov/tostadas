/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    UPDATE SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process UPDATE_SUBMISSION {

    publishDir "${params.output_dir}/${params.submission_output_dir}", mode: 'copy', overwrite: params.overwrite_output

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'docker.io/staphb/tostadas:latest' : 'docker.io/staphb/tostadas:latest' }"

    input:
    tuple val(meta), val(samples), val(enabledDatabases)
    path(original_submissions_dir)
    path(submission_config)
    
    output:
    tuple val(meta), path("${meta.batch_id}_biosample_update_[0-9]*"), emit: submission_batch_folder
    path("${meta.batch_id}/update_submission.log"), emit: submission_log, optional: true

    when:
    "sra" in enabledDatabases || "genbank" in enabledDatabases || "biosample" in enabledDatabases

    script:
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    def dry_run = params.dry_run == true ? '--dry_run' : ''

    // Assemble per-sample arguments, quoting paths in case of spaces
    def sample_args_list = samples.collect { sample ->
        def s = ["sample_id=${sample.sample_id}"]   // only sample_id is available
            .join(',')
        return "\"${s}\""
    }
    def sample_args = sample_args_list.collect { "--sample ${it}" }.join(' ')

    """
    submission_update.py \
        --submission_folder ${original_submissions_dir} \
        --submission_name ${meta.batch_id} \
        --config_file ${submission_config}  \
        --metadata_file ${meta.batch_tsv} \
        --identifier ${params.metadata_basename} \
        --outdir  ${meta.batch_id} \
        --submission_mode ${params.submission_mode} \
        $test_flag \
        $dry_run 
    """
}