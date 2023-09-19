/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN BAKTA ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process BAKTA {

    label = 'main'

    errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 5
    
    try {
        container "$params.docker_container_bakta"
    } catch (Exception e) {
        System.err.println("WARNING: Cannot pull the following docker container: $params.docker_container_bakta to run BAKTA")
    }

    publishDir "$params.bakta_output_dir", mode: 'copy', overwrite: params.overwrite_output


    input:
    val signal
    path meta_path
    path fasta_path
    path db_path 

    script:
    """
    bakta  --db $db_path  --meta_path $meta_path  --min-contig-length $params.bakta_min_contig_length  --prefix $params.bakta_prefix \
    --output $params.bakta_output_dir  --threads $params.bakta_threads  --replicons $params.bakta_replicons  --proteins $params.bakta_proteins \
    --prodigal-tf $params.bakta_prodigal_tf  --genus $params.bakta_genus  --species $params.bakta_species  --strain $params.bakta_strain \
    --plasmid $params.bakta_plasmid  --complete $params.bakta_complete  --locus $params.bakta_locus  --locus-tag $params.bakta_locus_tag \
    --translation-table $params.bakta_translation_table   --gram $params.bakta_gram \
    --compliant $params.bakta_compliant  --keep-contig-headers $params.bakta_keep_contig_headers  --meta $params.bakta_meta \
    --skip-trna $params.bakta_skip_trna  --skip-tmrna $params.bakta_skip_tmrna  --skip-rrna $params.bakta_skip_rrna \
    --skip-ncrna $params.bakta_skip_ncrna  --skip-ncrna-region $params.bakta_skip_ncrna_region \ 
    --skip-crispr $params.bakta_skip_crispr  --skip-cds $params.bakta_skip_cds  --skip-pseudo $params.bakta_skip_pseudo   --skip-sorf $params.bakta_skip_sorf  --skip-gap $params.bakta_skip_gap \
    --skip-ori $params.bakta_skip_ori  --skip-plot $params.bakta_skip_plot  --verbose $params.bakta_verbose --version $params.bakta_version \
    $fasta_path \

    """
    
    output:
        
    path "$params.bakta_output_dir/*/bakta/*.tsv",               emit: tsv
    path "$params.bakta_output_dir/*/bakta/*.gff3",              emit: gff3
    path "$params.bakta_output_dir/*/bakta/*.gbff",              emit: gbff
    path "$params.bakta_output_dir/*/bakta/*.embl",              emit: embl
    path "$params.bakta_output_dir/*/bakta/*.fna",               emit: fna
    path "$params.bakta_output_dir/*/bakta/*.ffn",               emit: ffn
    path "$params.bakta_output_dir/*/bakta/*.faa",               emit: faa
    path "$params.bakta_output_dir/*/bakta/*.hypotheticals_tsv", emit: hypotheticals_tsv
    path "$params.bakta_output_dir/*/bakta/*.hypotheticals_faa", emit: hypotheticals_faa
    path "$params.bakta_output_dir/*/bakta/*.json",              emit: json
    path "$params.bakta_output_dir/*/bakta/*.txt",               emit: txt
    path "$params.bakta_output_dir/*/bakta/*.png",               emit: png
    path "$params.bakta_output_dir/*/bakta/*.svg",               emit: svg
}
