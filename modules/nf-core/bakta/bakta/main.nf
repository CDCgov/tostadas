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
        --prefix ${fasta_path.getSimpleName()} \
        --output ${fasta_path.getSimpleName()} \
        --genus $params.bakta_genus \
        --species $params.bakta_species \
        --strain $params.bakta_strain 
        --plasmid $params.bakta_plasmid  \
        --complete $params.bakta_complete \
        --prodigal-tf $params.bakta_prodigal+df \
        --translation-table $params.bakta_translation_table \
        --gram $params.bakta_gram \
        --locus $params.bakta_locus \
        --locus-tag $params.bakta_locus-tag \
        --keep-contig-headers $params.bakta_keep_contig_headers \
        --replicons $params.bakta_replicons \
        --proteins $params.bakta_proteins \
        --skip-trna $params.bakta_skip_trna \
        --skip-tmrna $params.bakta_skip_tmrna \
        --skip-rrna $params.bakta_skip_rrna \
        --skip-ncrna $params.bakta_skip_ncrna \
        --skip-ncrna-region $params.bakta_skip_ncrna_region \
        --skip-crispr $params.bakta_skip_crispr \
        --skip-cds $params.bakta_skip_cds \
        --skip-pseudo $params.bakta_skip_pseudo \
        --skip-sorf $params.bakta_skip_sorf \
        --skip-gap $params.bakta_skip_gap \
        --skip-ori $params.bakta_skip_ori \
        --skip-plot $params.bakta_skip_plot \
        --help $params.bakta_help \
        --verbose $params.bakta_verbose
        $fasta_path
    """
    
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