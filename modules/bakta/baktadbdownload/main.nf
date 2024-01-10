process BAKTADBDOWNLOAD {

    conda (params.enable_conda ? "bioconda::bakta==1.9.1" : null)
    container "${ workflow.containerEngine == 'singularity' && !params.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/bakta:1.8.2--pyhdfd78af_0' :
        'quay.io/biocontainers/bakta:1.8.2--pyhdfd78af_0' }"

    input: 
    val signal

    output:
    path "bakta*"           , emit: db

    // when:
    // task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    """
    bakta_db \
        download \
        --type "${params.bakta_db_type}" \
        --output bakta_db

    """
}

