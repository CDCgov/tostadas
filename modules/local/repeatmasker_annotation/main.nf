/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN REPEATMASKER ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process REPEATMASKER {
    
    // conda (params.enable_conda ? "bioconda::repeatmasker=4.1.5 : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/repeatmasker:4.1.5--pl5321hdfd78af_1' :
        'quay.io/biocontainers/repeatmasker:4.1.5--pl5321hdfd78af_0'}"

	input:
	tuple val(meta), path(fasta_path), path(fast1), path(fastq2)
	path repeat_library

	script:
	"""
	RepeatMasker -s $fasta_path  -gff -lib $repeat_library  -s
	"""

	output:
    path "*.cat", emit: cat
    path "*.masked", emit: masked
    path "*.out",   emit: out
	path "*.gff", emit: gff
    path "*.tbl", emit: tbl
}



