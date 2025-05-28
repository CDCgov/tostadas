process BAKTADBDOWNLOAD {

    conda("bioconda::bakta==1.9.4")
    container "${ workflow.containerEngine == 'singularity' && !params.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/bakta:1.9.4--pyhdfd78af_0' :
        'quay.io/biocontainers/bakta:1.9.4--pyhdfd78af_0' }"

    input: 
    
    output:
    path "bakta_db/*"           , emit: db

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

