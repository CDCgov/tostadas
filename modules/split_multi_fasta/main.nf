/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                SPLIT MULTI FASTA FOR RUNNING BAKTA
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process SPLIT_FASTA {
    label 'main'
    
    
    errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 3
    
    publishDir "$params.output_dir/$params.split_output_dir", mode: 'copy', overwrite: params.overwrite_output
    
    
   input:
   val signal
   path fasta_path
   
   script:
   
   """
   awk '/^>/ {OUT=substr( \$0,2) ".fasta";print " ">OUT}; OUT{print >OUT}' $fasta_path
   """
   
   output:
	path '*.fasta', emit: fasta_files
}

    
