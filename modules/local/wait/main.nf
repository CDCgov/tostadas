/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                  WAIT PROCESS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process WAIT {
    tag "wait ${wait_time}s"

    conda(params.env_yml)
    container 'docker.io/staphb/tostadas:latest'

    input:
        val wait_time
    
    output:
        val true

    script:
        """
        echo "Sleeping for ${wait_time} seconds..."
        sleep ${wait_time}
        """

}
