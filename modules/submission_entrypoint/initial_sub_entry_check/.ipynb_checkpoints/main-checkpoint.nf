/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    CHECK FOR ONLY_INITIAL_SUBMISSION ENTRY POINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process ONLY_INITIAL_SUBMISSION_ENTRY_CHECK {

    errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 5
    
    exec:
        // check that certain params are specified 
        try {
            assert params.submission_only_meta
            assert params.submission_only_fasta
            if ( params.submission_database.toLowerCase().replaceAll("\\s","") != 'sra' ) {
                assert params.submission_only_gff
            }
            assert params.submission_output_dir 
            assert params.submission_wait_time
            assert params.req_col_config
            assert params.send_submission_email == true || params.send_submission_email == false
        } catch (Exception e) {
            throw new Exception("Paths to the (1) validated metadata file, (2) split fasta file, and (3) reformatted gff file must be specified, as well as submission output directory and wait time")
        }

        // check that paths are strings
        if ( params.submission_database.toLowerCase().replaceAll("\\s","") != 'sra' ) {
                paths_to_check = [params.submission_only_meta, params.submission_only_fasta, params.submission_only_gff]
        } else {
            paths_to_check = [params.submission_only_meta, params.submission_only_fasta]
        }

        for ( def path : paths_to_check ) {
            if ( path instanceof String == false ) {
                throw new Exception("Value must be of string type: $path used instead")
            }
        }
    
    output:
        val true
}