include { WAIT } from "$projectDir/nf_modules/utility_mods"

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN METADATA VALIDATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process METADATA_VALIDATION {

    label 'main'

    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $parmas.env_yml")
        }
    }

    publishDir "$params.output_dir", mode: 'copy', overwrite: params.overwrite_output

    input:
    val signal
    path meta_path
    path fasta_path

    output:
    path "/.*.tsv"
    val true

    script:
    """
    validate_metadata.py --meta_path $meta_path --fasta_path $fasta_path --output_dir $output_Val
    """
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN LIFTOFF ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process LIFTOFF {

    label 'main'
    
    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $parmas.env_yml")
        }
    }

    publishDir "$params.output_dir", mode: 'copy', overwrite: params.overwrite_output

    input:
    val signal
    path meta_path
    path fasta_path
    path ref_fasta_path
    path ref_gff_path

    output:
    path "lifted_fasta_path/*.fasta" 
    path "lifted_gff_path/*.gff"
    val true
    val true

    script:
    """
        liftoff_submission.py --fasta_path $fasta_path --meta_path $meta_path --ref_fasta_path $ref_fasta_path \
        --ref_gff_path $ref_gff_path --parallel_processes $params.lift_parallel_processes --final_liftoff_output_dir $params.final_liftoff_output_dir \
        --delete_temp_files $params.lift_delete_temp_files --minimap_path $params.lift_minimap_path --feature_database_name $params.lift_feature_database_name \
        --unmapped_features_file_name $params.lift_unmapped_features_file_name --distance_scaling_factor $params.lift_distance_scaling_factor \
        --copy_threshold $params.lift_copy_threshold --coverage_threshold $params.lift_coverage_threshold --child_feature_align_threshold $params.lift_child_feature_align_threshold \
        --copies $params.lift_copies --flank $params.lift_flank --mismatch $params.lift_mismatch --gap_open $params.lift_gap_open --gap_extend $params.lift_gap_extend
    """
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN VADR ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process VADR {

    label 'main'

    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $parmas.env_yml")
        }
    }

    publishDir "$params.output_dir", mode: 'copy', overwrite: params.overwrite_output

    input:
    val signal
    path fasta_path

    output:
    file "$params.vadr_outdir"
    val true

    script:
    """
     $params.vadr_script --vadr_loc $params.vadr_loc --fasta_path $params.fasta_path --vadr_outdir $params.vadr_outdir --mpxv_models_dir $projectDir/mpxv-models
    """
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process SUBMISSION {

    publishDir "$params.submission_output_dir", mode: 'copy', overwrite: params.overwrite_output

    label 'main'
    
    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $parmas.env_yml")
        }
    }

    input:
        val lift_signal
        val vadr_signal
        val val_signal
        path "output_val/*.tsv" 
        path lifted_fasta_path 
        path lifted_gff_path 
        val entry_flag

    script:
        """
        run_submission.py --validated_meta_path "$output_Val/*.tsv" --lifted_fasta_path "$lifted_fasta_path/*.fasta \
        --lifted_gff_path $lifted_gff_path/*.gff --launch_dir $launchDir --entry_flag $entry_flag --submission_script $params.submission_script \
        --meta_path $params.meta_path --config $params.submission_config --nf_output_dir $params.output_dir --submission_output_dir $params.submission_output_dir --update false \
        --batch_name $params.batch_name --prod_or_test $params.submission_prod_or_test --project_dir $projectDir
        """

    output:
        val true
}

process UPDATE_SUBMISSION {

    label 'main'
    
    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $parmas.env_yml")
        }
    }

    input:
        val signal
    script:
        """
         run_submission.py --update true --submission_script $params.submission_script --submission_output_dir $params.submission_output_dir \
         --nf_output_dir $params.output_dir --launch_dir $launchDir 
        """
} 
