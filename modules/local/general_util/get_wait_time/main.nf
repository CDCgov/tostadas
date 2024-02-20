process GET_WAIT_TIME {

    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
        val validated_meta_path
    exec:
        if ( params.submission_wait_time != 'calc' ) {
            submission_wait_time = params.submission_wait_time
        } else {
            i = validated_meta_path.toList().size
            submission_wait_time = 3 * 60 * i
        }
    output:
        val submission_wait_time
}
