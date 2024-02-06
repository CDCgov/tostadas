/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN BAKTA ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process BAKTA {

    label 'bakta'

    // errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 5
    
    conda (params.enable_conda ? "bioconda::bakta==1.9.1" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/bakta:1.9.1--pyhdfd78af_0' :
        'quay.io/biocontainers/bakta:1.9.1--pyhdfd78af_0' }"
    
    publishDir "$params.output_dir/$params.bakta_output_dir", mode: 'copy', overwrite: params.overwrite_output
    
    input:
    val signal
    path db_path
    tuple val(meta), path(fasta_path)

    script:
    def args = task.ext.args  ?: ''
    """
    bakta --db $db_path  --min-contig-length $params.bakta_min_contig_length --prefix ${fasta_path.getSimpleName()} \
    --output ${fasta_path.getSimpleName()} --threads $params.bakta_threads \
    --genus $params.bakta_genus --species $params.bakta_species --strain $params.bakta_strain --compliant \
    --plasmid $params.bakta_plasmid  --locus $params.bakta_locus --locus-tag $params.bakta_locus_tag \
    --translation-table $params.bakta_translation_table \
    $args \
    $fasta_path
    """
    
    output:
    path "${fasta_path.getSimpleName()}",   emit: bakta_results
    //path "*.fna",   emit: fna
    //path "*.gff3",   emit: gff3
    //path "*.faa",   emit: faa
    //path "*.embl",   emit: embl
    //path "*.ffn",   emit: ffn
    //path "*.gbff",   emit: gbff
    //path "*.json",   emit: json
    //path "*.log",   emit: log
    //path "*.png",   emit: png
    //path "*.svg",   emit: svg
    //path "*.tsv",   emit: tsv
    //path "*.txt",   emit: txt
}