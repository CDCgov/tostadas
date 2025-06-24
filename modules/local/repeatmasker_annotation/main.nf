/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN REPEATMASKER ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process REPEATMASKER {
    
    conda(params.repeatmasker_env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/repeatmasker:4.1.5--pl5321hdfd78af_1' :
        'quay.io/biocontainers/repeatmasker:4.1.5--pl5321hdfd78af_0'}"

	input:
	tuple val(meta), path(fasta_path)
	path repeat_library

	script:
	"""
    echo $fasta_path
    echo $repeat_library
	RepeatMasker -s $fasta_path  -gff -lib $repeat_library  -s
	"""

	output:
    tuple val(meta), path("*.cat"), emit: cat
    tuple val(meta), path("*.masked"), emit: masked
    tuple val(meta), path("*.out"), emit: out
    tuple val(meta), path("*.gff"), emit: gff
    tuple val(meta), path("*.tbl"), emit: tbl
}



