process BAKTADBDOWNLOAD {
    label 'process_single'

        conda (params.enable_conda ? conda_env : null)
    container "${ workflow.containerEngine == 'singularity' && !params.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/bakta:1.8.2--pyhdfd78af_0' :
        'quay.io/biocontainers/bakta:1.8.2--pyhdfd78af_0' }"


    output:
    path "bakta*"              , emit: db
    path "versions.yml"     , emit: versions

    when:
    task.ext.when == null || task.ext.when

    script:
    def args = task.ext.args ?: ''
    """
    bakta_db \\
        download \\
        --type "${params.bakta_db_type}" \\
        --output bakta

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        bakta: \$(echo \$(bakta_db --version) 2>&1 | cut -f '2' -d ' ')
    END_VERSIONS
    """

    stub:
    def args = task.ext.args ?: ''
    """
    echo "bakta_db \\
        download \\
        $args"

    mkdir db

    cat <<-END_VERSIONS > versions.yml
    "${task.process}":
        bakta: \$(echo \$(bakta_db --version) 2>&1 | cut -f '2' -d ' ')
    END_VERSIONS
    """
}
