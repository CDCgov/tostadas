/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN CREATE_BATCH_TSVS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process CREATE_BATCH_TSVS {

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'docker.io/staphb/tostadas:latest' : 'docker.io/staphb/tostadas:latest' }"

    input:
    path xlsx_file
    val batch_size

    output:
    path "genbank/*.tsv", emit: tsv_files

    script:
    """
    create_batch_tsvs.py --input $xlsx_file --batch_size $batch_size --output_prefix "genbank"
    """
}

