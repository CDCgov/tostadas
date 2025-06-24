/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN VADR TRIMMING
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process VADR_TRIM {

    conda(params.vadr_env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/vadr:latest' : 'staphb/vadr:latest' }"

    input:
	tuple val(meta), path(fasta_path), val(fastq1), val(fastq2), val(nnp) // these are vals because the raw files aren't used, they're just placeholders
    // todo: remove them from the input channel later to be cleaner

    output:
    tuple val(meta), path('*.trimmed.fasta') , emit: trimmed_fasta

    script:
    def prefix = task.ext.prefix ?: "${meta.sample_id}"

    """
    fasta-trim-terminal-ambigs.pl \
        --minlen 50 \
        --maxlen 210000 \
        $fasta_path > \
        ${prefix}.trimmed.fasta
    """
}