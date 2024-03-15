/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN BAKTA ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process BAKTA {

    //label 'bakta'

    // errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    //maxRetries 5
    
    conda (params.enable_conda ? "bioconda::bakta==1.9.1" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/bakta:1.9.1--pyhdfd78af_0' :
        'quay.io/biocontainers/bakta:1.9.1--pyhdfd78af_0' }"
    
    publishDir "$params.output_dir/$params.bakta_output_dir", mode: 'copy', overwrite: params.overwrite_output
    
    input:
    path db_path
    tuple val(meta), path(fasta_path), path(fastq1), path(fastq2)
    
    script:
    def args = task.ext.args  ?: ''
    def prefix   = task.ext.prefix ?: "${meta.id}"
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
    def keep_contig_headers = params.bakta_keep_contig_headers ? "--keep-contig-headers" : ""

    """
    bakta --db $db_path  \
        --min-contig-length $params.bakta_min_contig_length \
        --prefix $meta.id \
        --output $meta.id \
        --genus $params.bakta_genus \
        --species $params.bakta_species \
        --strain $params.bakta_strain \
        --plasmid $params.bakta_plasmid  \
        --translation-table $params.bakta_translation_table \
        --gram $params.bakta_gram \
        --locus $params.bakta_locus \
        --locus-tag $params.bakta_locus_tag \
        $complete \
        $compliant \
        $keep_contig_headers \
        $proteins \
        $prodigal_tf \
        $skip_trna \
        $skip_rrna \
        $skip_ncrna \
        $skip_ncrna_region \
        $skip_crispr \
        $skip_cds \
        $skip_sorf \
        $skip_gap \
        $skip_ori \
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