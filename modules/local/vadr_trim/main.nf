/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN VADR TRIMMING
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process VADR_TRIM {

    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/vadr:latest' : 'staphb/vadr:latest' }"

    input:
	tuple val(meta), path(metadata), path(fasta_path), path(fastq1), path(fastq2)

    output:
    tuple val(meta), path('*.trimmed.fasta') , emit: trimmed_fasta

    script:
    def prefix = task.ext.prefix ?: "${meta.id}"

    """
    fasta-trim-terminal-ambigs.pl \
        --minlen 50 \
        --maxlen 210000 \
        $fasta_path > \
        ${prefix}.trimmed.fasta
    """
}