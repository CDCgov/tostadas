/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    GET SAMPLES AND PATHS FROM METADATA FOR RAW SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process METADATA_RAW_SUBMISSION {

    label 'main'

    //conda (params.enable_conda ? "conda-forge::python=3.8.3" : null)
    //container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
    //    'https://depot.galaxyproject.org/singularity/python:3.8.3' :
    //    'quay.io/biocontainers/python:3.8.3' }"
    if ( params.run_conda == true ) {
        try {
           conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $params.env_yml")
        }
    }

    publishDir "$params.output_dir", mode: 'copy', overwrite: params.overwrite_output

    // Define input parameters
    input:
    val signal
    path meta_path
    
    script:
    """
    metadata_raw_submission.py --meta_path $meta_path
    """

    // Define output channels
    output:
    val sample_names, emit: sample_names
    val sample_file_paths, emit: sample_paths
}