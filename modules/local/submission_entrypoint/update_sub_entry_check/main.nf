/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    CHECK FOR ONLY_UPDATE_SUBMISSION ENTRY POINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process ONLY_UPDATE_SUBMISSION_ENTRY_CHECK {

    errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 5

    exec:
        // check that update_submission specific parameters are specified 
        try {
            assert params.processed_samples
            assert params.processed_samples instanceof String == true 
        } catch (Exception e) {
            throw new Exception("The parameter for the path to the directory containing all the processed samples (gffs, fastas, meta files) must be defined")
        }
    
    output:
        val true
}