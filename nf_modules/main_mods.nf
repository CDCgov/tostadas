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
    file "$params.val_output_dir"
    val true

    script:
    """
    python3 $params.validation_script --meta_path $meta_path --fasta_path $fasta_path --output_dir $params.val_output_dir
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
    file "$params.final_liftoff_output_dir"
    val true

    script:
    """
        python3 $params.liftoff_script --fasta_path $fasta_path --meta_path $meta_path --ref_fasta_path $ref_fasta_path \
        --ref_gff_path $ref_gff_path --parallel_processes $params.lift_parallel_processes --final_liftoff_output_dir $params.final_liftoff_output_dir \
        --delete_temp_files $params.lift_delete_temp_files --minimap_path $params.lift_minimap_path --feature_database_name $params.lift_feature_database_name \
        --unmapped_features_file_name $params.lift_unmapped_features_file_name --distance_scaling_factor $params.lift_distance_scaling_factor \
        --copy_threshold $params.lift_copy_threshold --coverage_threshold $params.lift_coverage_threshold --child_feature_align_threshold $params.lift_child_feature_align_threshold \
        --copies $params.lift_copies --flank $params.lift_flank --mismatch $params.lift_mismatch --gap_open $params.lift_gap_open --gap_extend $params.lift_gap_extend
    """
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process SUBMISSION {

    publishDir "$params.output_dir/$params.submission_output_dir", mode: 'copy', overwrite: params.overwrite_output

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
        val signal2
        val validated_meta_path
        val lifted_fasta_path
        val lifted_gff_path
        val entry_flag
    script:
        """
        python3 $projectDir/bin/run_submission.py --validated_meta_path $validated_meta_path --lifted_fasta_path $lifted_fasta_path \
        --lifted_gff_path $lifted_gff_path --launch_dir $launchDir --entry_flag $entry_flag --submission_script $params.submission_script \
        --meta_path $params.meta_path --config $params.submission_config --nf_output_dir $params.output_dir --submission_output_dir $params.submission_output_dir --update false \
        --batch_name $params.batch_name
        """
    output:
        file "*"
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
         python3 $projectDir/bin/run_submission.py --update true
        """
}