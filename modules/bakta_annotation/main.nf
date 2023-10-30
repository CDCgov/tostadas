/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN BAKTA ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process BAKTA {

    label = 'bakta'

    errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 5
    
    try {
        container "$params.docker_container_bakta"
    } catch (Exception e) {
        System.err.println("WARNING: Cannot pull the following docker container: $params.docker_container_bakta to run BAKTA")
    }

    // publishDir "$params.output_dir/$params.bakta_output_dir", mode: 'copy', overwrite: params.overwrite_output


    input:
    val signal
    path db_path
    path fasta

    script:
    def args = task.ext.args  ?: ''
    """
    bakta  --db $db_path  --min-contig-length $params.bakta_min_contig_length --prefix ${fasta.getSimpleName()} \
    --output ${fasta.getSimpleName()} --threads $params.bakta_threads \
    --genus $params.bakta_genus --species $params.bakta_species --strain $params.bakta_strain \
    --plasmid $params.bakta_plasmid  --locus $params.bakta_locus --locus-tag $params.bakta_locus_tag \
    --translation-table $params.bakta_translation_table \
    $args \
    $fasta
    """
    
    output:
    path "${fasta.getSimpleName()}",   emit: bakta_results
}
