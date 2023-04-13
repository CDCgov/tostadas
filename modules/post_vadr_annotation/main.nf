/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                POST VADR CLEANUP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process VADR_POST_CLEANUP {

    label 'main'

    errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 5
    
    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $params.env_yml")
        }
    }

    publishDir "$params.output_dir", mode: 'copy', overwrite: params.overwrite_output

    input:
    path vadr_outputs
    path meta_path
    path fasta_path
    
    script:
    """
    post_vadr_cleanup.py --meta_path $meta_path --fasta_path $fasta_path --vadr_outdir $params.vadr_output_dir --vadr_outputs $vadr_outputs
    """

    output:
    path "$params.vadr_output_dir/*/transformed_outputs/fasta/*.fasta", emit: fasta
    path "$params.vadr_output_dir/*/transformed_outputs/gffs/*.gff", emit: gff
    path "$params.vadr_output_dir/*/transformed_outputs/errors/*.txt", emit: errors
    path "$params.vadr_output_dir/*/transformed_outputs/tbl/*.tbl", emit: tbl
    path "$params.vadr_output_dir/*/original_outputs/*", emit: original_outputs
    path "$params.vadr_output_dir/*/transformed_outputs/*.tbl", emit: concat_table
}