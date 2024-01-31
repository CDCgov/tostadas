/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN REPEATMASKER ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process REPEATMASKER {

	
	errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
	maxRetries 2
    
	if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $params.env_yml")
        }
    }

    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/repeatmasker:4.1.5--pl5321hdfd78af_1' :
        'quay.io/biocontainers/repeatmasker:4.1.5--pl5321hdfd78af_0'}"

	input:
	val signal
	path fasta_path
	path repeat_lib

	script:
	"""
	RepeatMasker -s $fasta_path  -gff -lib $repeat_lib -s
	"""

	output:
    path "*.cat", emit: cat
    path "*.masked", emit: masked
    path "*.out",   emit: out
	path "*.gff", emit: gff
    path "*.tbl", emit: tbl
}



