/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN BAKTA ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process BAKTA {

    label 'bakta'

    // errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 5
    
    conda "bioconda::bakta==1.9.1"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/bakta:1.9.1--pyhdfd78af_0' :
        'quay.io/biocontainers/bakta:1.9.1--pyhdfd78af_0' }"

    input:
    val signal
    path db_path
    path fasta

    script:
    def args = task.ext.args  ?: ''
    """
    bakta --db $db_path  --min-contig-length $params.bakta_min_contig_length --prefix ${fasta.getSimpleName()} \
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