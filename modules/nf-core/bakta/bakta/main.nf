/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN BAKTA ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process BAKTA {

    conda("bioconda::bakta==1.11.0")
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/1.11.0--pyhdfd78af_0' :
        'quay.io/biocontainers/bakta:1.11.0--pyhdfd78af_0' }"
    
    input:
    path db_path
    tuple val(meta), path(fasta_path), path(fastq1), path(fastq2)

    output:
    tuple val(meta), path("${meta.sample_id}/*.fna"), emit: fna
    tuple val(meta), path("${meta.sample_id}/*.gff3"), emit: gff
    tuple val(meta), path("${meta.sample_id}/*.faa"), emit: faa
    tuple val(meta), path("${meta.sample_id}/*.embl"), emit: embl
    tuple val(meta), path("${meta.sample_id}/*.ffn"), emit: ffn
    tuple val(meta), path("${meta.sample_id}/*.gbff"), emit: gbff
    tuple val(meta), path("${meta.sample_id}/*.json"), emit: json
    tuple val(meta), path("${meta.sample_id}/*.log"), emit: log
    tuple val(meta), path("${meta.sample_id}/*.tsv"), emit: tsv
    tuple val(meta), path("${meta.sample_id}/*.txt"), emit: txt
        
    script:
    def args = task.ext.args  ?: ''
    def prefix   = task.ext.prefix ?: "${meta.sample_id}"
    def proteins = params.bakta_proteins ? "--proteins ${proteins[0]}" : ""
    def prodigal_tf = params.bakta_prodigal_tf ? "--prodigal-tf ${prodigal_tf[0]}" : ""
    def skip_trna = params.bakta_skip_trna ? "--skip-trna" : ""
    def skip_tmrna = params.bakta_skip_tmrna ? "--skip-tmrna" : ""
    def skip_rrna = params.bakta_skip_rrna ? "--skip-rrna" : ""
    def skip_ncrna = params.bakta_skip_ncrna ? "--skip-ncrna" : ""
    def skip_ncrna_region = params.bakta_skip_ncrna_region ? "--skip-ncrna-region" : ""
    def skip_crispr = params.bakta_skip_crispr ? "--skip-crispr" : ""
    def skip_cds = params.bakta_skip_cds ? "--skip-cds" : ""
    def skip_sorf = params.bakta_skip_sorf ? "--skip-sorf" : ""
    def skip_gap = params.bakta_skip_gap ? "--skip-gap" : ""
    def skip_ori = params.bakta_skip_ori ? "--skip-ori" : ""
    def compliant = params.bakta_compliant ? "--compliant" : ""
    def complete = params.bakta_complete ? "--complete" : ""
    def skip_plot = params.bakta_skip_plot ? "--skip-plot" : ""
    def keep_contig_headers = params.bakta_keep_contig_headers ? "--keep-contig-headers" : ""
    def locus_tag_param = params.bakta_locus_tag ? "--locus-tag ${params.bakta_locus_tag}" : ""

    """"
    bakta --db $db_path  \
        --min-contig-length $params.bakta_min_contig_length \
        --prefix $meta.sample_id \
        --output $meta.sample_id \
        --genus $params.bakta_genus \
        --species $params.bakta_species \
        --strain $params.bakta_strain \
        --plasmid $params.bakta_plasmid  \
        --translation-table $params.bakta_translation_table \
        --gram $params.bakta_gram \
        --locus $params.bakta_locus \
        ${locus_tag_param} \
        $complete $compliant $keep_contig_headers $proteins $prodigal_tf $skip_trna $skip_rrna \
        $skip_ncrna $skip_ncrna_region $skip_crispr $skip_cds $skip_sorf $skip_gap $skip_ori $skip_plot \
        $fasta_path 
    """
}