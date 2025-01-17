
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                  WAIT PROCESS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process WAIT {

    //label 'main'
    
    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"
    

    input:
        //val submission_signal
        val wait_time

    script:
        """
        submission_utility.py --wait true --wait_time $wait_time
        """

    output:
        val true
}

process GET_WAIT_TIME {
    input:
        val meta_signal
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