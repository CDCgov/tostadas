/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                POST VADR CLEANUP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process VADR_POST_CLEANUP {

    // label 'main'
    
    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"


    publishDir "$params.output_dir", mode: 'copy', overwrite: params.overwrite_output

    input:
    path vadr_outputs
    tuple val(meta), path meta_path
	tuple val(meta), path(fasta_path)
    
    script:
    """
    post_vadr_cleanup.py --meta_path $meta_path --vadr_outdir $params.vadr_output_dir --vadr_outputs $vadr_outputs
    """

    output:
    path "$params.vadr_output_dir/*/transformed_outputs/gffs/*.gff", emit: gff
    path "$params.vadr_output_dir/*/transformed_outputs/errors/*.txt", emit: errors
    path "$params.vadr_output_dir/*/transformed_outputs/tbl/*.tbl", emit: tbl
    path "$params.vadr_output_dir/*/original_outputs/*", emit: original_outputs
    path "$params.vadr_output_dir/*/transformed_outputs/*.tbl", emit: concat_table
}