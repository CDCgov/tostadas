/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                POST BAKTA CLEANUP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process BAKTA_POST_CLEANUP {

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

    // publishDir "$params.output_dir", mode: 'copy', overwrite: params.overwrite_output

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
