/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                POST BAKTA CLEANUP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process BAKTA_POST_CLEANUP {

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
    path bakta_results
    path meta_path
    path fasta_path
    
    script:
    """
    post_bakta_cleanup.py --meta_path $meta_path --fasta_path $fasta_path --bakta_outdir $params.bakta_output_dir --bakta_results $bakta_results
    """

    output:
    path "$params.bakta_output_dir/*/fasta/*.fasta", emit: fasta
    path "$params.bakta_output_dir/*/gff/*.gff", emit: gff
    path "$params.bakta_output_dir/*/tbl/*.tbl", emit: tbl
}
