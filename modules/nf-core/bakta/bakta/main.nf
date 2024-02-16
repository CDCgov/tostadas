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
    def prefix   = task.ext.prefix ?: "${meta.id}"
    def proteins_opt = params.bakta_proteins ? "--proteins ${proteins[0]}" : ""
    def prodigal_tf = params.bakta_prodigal_tf ? "--prodigal-tf ${prodigal_tf[0]}" : ""
    def skip_trna = params.bakta_skip_trna ? "--skip_trna" : ""
    def skip_tmrna = params.bakta_skip_tmrna ? "--skip_tmrna" : ""
    def skip_rrna = params.bakta_skip_rrna ? "--skip_rrna" : ""
    def skip_ncrna = params.bakta_skip_ncrna ? "--skip_ncrna" : ""
    def skip_ncrna_region = params.bakta_skip_ncrna_region ? "--skip_ncrna_region" : ""
    def skip_crispr = params.bakta_skip_crispr ? "--skip_crispr" : ""
    def skip_cds = params.bakta_skip_cds ? "--skip_cds" : ""
    def skip_sorf = params.bakta_skip_sorf ? "--skip_sorf" : ""
    def skip_gap = params.bakta_skip_gap ? "--skip_gap" : ""
    def skip_ori = params.bakta_skip_ori ? "--skip_ori" : ""
    def compliant = params.bakta_compliant ? "--compliant" : ""
    def keep_contig_headers = params.bakta_keep_contig_headers ? "--keep_contig_headers" : ""

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
        --locus $params.bakta_locus \
        --locus-tag $params.bakta_locus_tag \
        --$compliant \
        --$keep_contig_headers \
        --$proteins \
        --$prodigal_tf \
        --$skip_trna \
        --$skip_rrna \
        --$skip_ncrna \
        --$skip_ncrna_region \
        --$skip_crispr \
        --$skip_cds \
        --$skip_sorf \
        --$skip_gap \
        --$skip_ori \
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