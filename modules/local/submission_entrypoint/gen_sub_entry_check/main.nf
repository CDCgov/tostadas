
/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                           CHECK FOR SUBMISSION ENTRY POINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process GENERAL_SUBMISSION_ENTRY_CHECK {

    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"
    
    exec:
        // check the different ways to run params
        def check = [params.run_docker, params.run_conda, params.run_singularity].count(true)
        if ( check != 1 && check != 0 ) {
            throw new Exception("More than two profiles between docker, conda, and singularity were passed in. Please pass in only one")
        } else if ( check == 0 ) {
            throw new Exception("Either docker, conda, or singularity must be selected as profile [docker, conda, singularity]. None passed in.")
        }

        // check that certain variables are specified
        try {
            assert params.submission_prod_or_test 
            assert params.submission_database 
            assert params.batch_name
            assert params.submission_config
        } catch (Exception e) {
            throw new Exception("Batch name not specified for submission")
        }

    output:
        val true
}
