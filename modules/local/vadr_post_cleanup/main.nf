/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                POST VADR CLEANUP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process VADR_POST_CLEANUP {
    
    conda(params.vadr_env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
    tuple val(meta), path(vadr_outputs)
    
    output:
    tuple val(meta), path('*/transformed_outputs/gffs/*.gff'), emit: gff
    tuple val(meta), path('*/transformed_outputs/errors/*.txt'), emit: errors
    tuple val(meta), path('*/transformed_outputs/tbl/*.tbl'), emit: tbl

    script:
    """
    post_vadr_cleanup.py \
        --sample_id $meta.sample_id \
        --vadr_outdir '.' \
        --vadr_outputs $vadr_outputs
    """
}