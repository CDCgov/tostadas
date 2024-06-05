/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                POST VADR CLEANUP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process VADR_POST_CLEANUP {
    
    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
    tuple val(meta), path(meta_path), path(fasta_path), path(fastq1), path(fastq2), path(vadr_outputs)
    
    output:
    tuple val(meta), path('*/transformed_outputs/gffs/*.gff'), emit: gff
    tuple val(meta), path('*/transformed_outputs/errors/*.txt'), emit: errors
    tuple val(meta), path('*/transformed_outputs/tbl/*.tbl'), emit: tbl

    script:
    """
    post_vadr_cleanup.py \
        --meta_path $meta_path \
        --vadr_outdir '.' \
        --vadr_outputs $vadr_outputs
    """
}