/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            PREP SUBMISSION ENTRY INPUTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process PREP_SUBMISSION_ENTRY {

    label 'main'

    //errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    //maxRetries 5

    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $parmas.env_yml")
        }
    }

    input:
        val submission_entry_check_signal
        path validated_meta
        path fasta
        path annotated_gff
        path submission_config
        val database
        val update_entry
 
    script:
        """
        submission_utility.py --prep_submission_entry true --update_entry $update_entry --meta_path $validated_meta --fasta_path $fasta --gff_path $annotated_gff \
        --database $database --config $submission_config
        """
     
    output: 
        path "tsv_submit_entry/*", emit: tsv
        path "fasta_submit_entry/*", emit: fasta
        path "gff_submit_entry/*", emit: gff
}