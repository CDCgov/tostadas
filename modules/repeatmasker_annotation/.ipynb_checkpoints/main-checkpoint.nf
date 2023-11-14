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

	publishDir "$params.output_dir", mode: 'copy', overwrite: params.overwrite_output

	input:
	val signal
	path fasta_path
	path repeat_lib

	script:
	"""
	RepeatMasker -s $fasta_path  -gff  -lib $repeat_lib -dir $params.repeatmasker_output_dir -s
	"""

	output:
	path "$params.repeatmasker_output_dir",   emit: repeatmasker_results

}



