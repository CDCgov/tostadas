/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN BAKTA ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process BAKTA {

    label = 'main'

    errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 5
    
    try {
        container "$params.docker_container_bakta"
    } catch (Exception e) {
        System.err.println("WARNING: Cannot pull the following docker container: $params.docker_container_bakta to run BAKTA")
    }

    publishDir "$params.bakta_output_dir", mode: 'copy', overwrite: params.overwrite_output

    input: 

    script:
    """
    """
}