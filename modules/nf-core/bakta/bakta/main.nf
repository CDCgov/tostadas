/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN BAKTA ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process BAKTA {

    // label 'bakta'
    
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
    bakta --db $db_path  \
        --min-contig-length $params.bakta_min_contig_length \
        --prefix $meta.id \
        --output $meta.id \
        --genus $params.bakta_genus \
        --species $params.bakta_species \
        --strain $params.bakta_strain \
        --plasmid $params.bakta_plasmid  \
        --complete $params.bakta_complete \
        --translation-table $params.bakta_translation_table \
        --gram $params.bakta_gram \ 
        --compliant \
        --locus $params.bakta_locus \
        --locus-tag $params.bakta_locus_tag \
        --keep-contig-headers \
        $fasta_path
    """
    // optional args
    // --prodigal-tf $params.bakta_prodigal_tf 
    // --replicons $params.bakta_replicons 
    // --proteins $params.bakta_proteins 
    // --skip-trna  
    // --skip-tmrna 
    // --skip-rrna
    // --skip-ncrna 
    // --skip-ncrna-region 
    // --skip-crispr 
    // --skip-cds 
    // --skip-pseudo
    // --skip-sorf
    // --skip-gap 
    // --skip-ori 
    // --skip-plot


    
    output:
    path "${fasta_path.getSimpleName()}/*.fna",   emit: fna
    path "${fasta_path.getSimpleName()}/*.gff3",   emit: gff3
    path "${fasta_path.getSimpleName()}/*.faa",   emit: faa
    path "${fasta_path.getSimpleName()}/*.embl",   emit: embl
    path "${fasta_path.getSimpleName()}/*.ffn",   emit: ffn
    path "${fasta_path.getSimpleName()}/*.gbff",   emit: gbff
    path "${fasta_path.getSimpleName()}/*.json",   emit: json
    path "${fasta_path.getSimpleName()}/*.log",   emit: log
    path "${fasta_path.getSimpleName()}/*.png",   emit: png
    path "${fasta_path.getSimpleName()}/*.svg",   emit: svg
    path "${fasta_path.getSimpleName()}/*.tsv",   emit: tsv
    path "${fasta_path.getSimpleName()}/*.txt",   emit: txt
}