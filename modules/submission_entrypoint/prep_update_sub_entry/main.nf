/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            PREP UPDATE SUBMISSION ENTRY INPUTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process PREP_UPDATE_SUBMISSION_ENTRY {

    label 'main'

    errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    maxRetries 5

    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $parmas.env_yml")
        }
    }

    input: 
        val submission_entry_check_signal
        val update_entry
        path processed_samples
    
    script:
        """
        submission_utility.py --prep_submission_entry true --processed_samples $processed_samples --update_entry $update_entry
        """
    
    output: 
        path "update_entry/*", emit: samples
}