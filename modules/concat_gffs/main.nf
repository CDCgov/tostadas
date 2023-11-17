/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN CONCAT GFFS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process CONCAT_GFFS {

	
	errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
	maxRetries 2

    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $params.env_yml")
        }
    }

    
    publishDir "$params.output_dir/final_annotation_outputs", mode: "copy", overwrite: params.overwrite_output,
        saveAs: { filename ->
                      filename.indexOf('.gff') > 0 ? "gff/${filename}":
                      filename.indexOf('.txt') > 0 ? "errors/${filename}":
                      filename.indexOf('.tbl') > 0 ? "tbl/${filename}":
                      filename
               }

	input:
	val signal
	path ref_gff_path
	path repeatmasker_gff
    path liftoff_gff

	script:
	"""
	repeatmasker_liftoff.py --repeatm_gff $repeatmasker_gff --liftoff_gff $liftoff_gff --refgff $ref_gff_path    
	"""

	output:
    
    path "*.gff", emit: gff
    path "*.txt", emit: errors
    path "*.tbl", emit: tbl

}

