/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN REPEATMASKER ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process REPEATMASKER {

	
	errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
	maxRetries 2

	try {
		container 'quay.io/biocontainers/repeatmasker:4.1.5--pl5321hdfd78af_0'
	} catch (Exception e) {
		System.err.println("WARNING: Cannot pull the Repeatmasker docker container")
	}

// publishDir "$params.output_dir", mode: 'copy', overwrite: params.overwrite_output

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



