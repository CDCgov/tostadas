/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN VADR ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process VADR_ANNOTATION {
    
    conda(params.vadr_env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/vadr:latest' : 'staphb/vadr:latest' }"

    input:
	tuple val(meta), path(fasta_path)
    path vadr_models_dir

    output:
    tuple val(meta), path("${meta.id}_${params.species}"), emit: vadr_outputs

    script:
    """
    v-annotate.pl \
        --split \
        --cpu $task.cpus \
        --glsearch \
        --minimap2 \
        -s \
        -r \
        --nomisc \
        --mkey ${params.species} \
        --r_lowsimok \
        --r_lowsimxd 100 \
        --r_lowsimxl 2000 \
        --alt_pass discontn,dupregin \
        --s_overhang 150 \
        --mdir $vadr_models_dir \
        $fasta_path \
        ${meta.id}_${params.species}
    """
}