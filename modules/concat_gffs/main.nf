/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN CONCAT GFFS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process CONCAT_GFFS {

	
	errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
	maxRetries 2

    conda (params.enable_conda ? "conda-forge::python=3.8.3 conda-forge::pandas" : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/pandas:1.1.5' :
        'quay.io/biocontainers/pandas:1.5.2' }"
   
    publishDir "$params.output_dir/repeatmasker_liftoff_outputs", mode: "copy", overwrite: params.overwrite_output,
        saveAs: { filename ->
                      filename.indexOf('.gff') > 0 ? "gff/${filename}":
                      filename.indexOf('.txt') > 0 ? "errors/${filename}":
                      filename.indexOf('.tbl') > 0 ? "tbl/${filename}":
                      filename
               }

	input:
	path ref_gff_path
	path repeatmasker_gff
    path liftoff_gff
    path fasta_path

	script:
	"""
	repeatmasker_liftoff.py --repeatm_gff $repeatmasker_gff --liftoff_gff $liftoff_gff --refgff $ref_gff_path --fasta $fasta_path   
	"""

	output:
    
    path "*.gff", emit: gff
    path "*.txt", emit: errors
    path "*.tbl", emit: tbl

}

