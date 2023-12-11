/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN BAKTA ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process BAKTA {

    label = 'bakta'

    errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 5
    
    //conda "bioconda::bakta==1.9.1"
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/bakta:1.9.1--pyhdfd78af_0' :
        'quay.io/biocontainers/bakta:1.9.1--pyhdfd78af_0' }"


    // publishDir "$params.output_dir/$params.bakta_output_dir", mode: 'copy', overwrite: params.overwrite_output


    input:
    //
    //fasta

    script:
    def args = task.ext.args  ?: ''
    """
    bakta  --db ${params.bakta_db_path}  --min-contig-length ${params.bakta_min_contig_length} --prefix ${params.fasta_path} \
    --output ${params.fasta_path} --threads ${params.bakta_threads} \
    --genus ${params.bakta_genus} --species ${params.bakta_species} --strain ${params.bakta_strain} \
    --plasmid ${params.bakta_plasmid}  --locus ${params.bakta_locus} --locus-tag ${params.bakta_locus_tag} \
    --translation-table ${params.bakta_translation_table} \
    $args \
    ${params.fasta_path}
    """
    
    output:
    path "${params.fasta_path}",   emit: bakta_results
}