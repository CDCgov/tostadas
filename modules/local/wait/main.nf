/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                  WAIT PROCESS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process WAIT {
    tag "wait ${wait_time}s"

    conda(params.env_yml)
    container 'staphb/tostadas:latest'

    input:
        val wait_time

    script:
        """
        submission_utility.py --wait true --wait_time ${wait_time}
        """
    output:
        val true
}
