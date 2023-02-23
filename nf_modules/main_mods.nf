
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

    script:
    """
    validate_metadata.py --meta_path $meta_path --fasta_path $fasta_path --output_dir $params.val_output_dir
    """

    output:
    path "$params.val_output_dir/*/tsv_per_sample/*.tsv", emit: tsv_Files
    path "$params.val_output_dir/*/errors", emit: errors
    val true, emit: meta_signal
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

    script:
    """
        liftoff_submission.py --fasta_path $fasta_path --meta_path $meta_path --ref_fasta_path $ref_fasta_path \
        --ref_gff_path $ref_gff_path --parallel_processes $params.lift_parallel_processes --final_liftoff_output_dir $params.final_liftoff_output_dir \
        --delete_temp_files $params.lift_delete_temp_files --minimap_path $params.lift_minimap_path --feature_database_name $params.lift_feature_database_name \
        --unmapped_features_file_name $params.lift_unmapped_features_file_name --distance_scaling_factor $params.lift_distance_scaling_factor \
        --copy_threshold $params.lift_copy_threshold --coverage_threshold $params.lift_coverage_threshold --child_feature_align_threshold $params.lift_child_feature_align_threshold \
        --copies $params.lift_copies --flank $params.lift_flank --mismatch $params.lift_mismatch --gap_open $params.lift_gap_open --gap_extend $params.lift_gap_extend
    """

    output:
    path "$params.final_liftoff_output_dir/*/fasta/*.fasta", emit: fasta
    path "$params.final_liftoff_output_dir/*/liftoff/*.gff", emit: gff
    path "$params.final_liftoff_output_dir/*/errors/*.txt", emit: errors
    path "$params.final_liftoff_output_dir/*/tbl/*.tbl", emit: tbl
    val true, emit: liftoff_signal
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
    path("${params.vadr_outdir}")
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

    label 'main'
    
    publishDir "$params.output_dir/$params.submission_output_dir", mode: 'copy', overwrite: params.overwrite_output

    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $parmas.env_yml")
        }
    }

    input:
        path validated_meta_path
        path lifted_fasta_path
        path lifted_gff_path
        val entry_flag
        path submission_config
        path req_col_config

    script:
    """
    run_submission.py --submission_database $params.submission_database --unique_name $params.batch_name --lifted_fasta_path $lifted_fasta_path \
    --validated_meta_path $validated_meta_path --lifted_gff_path $lifted_gff_path --config $submission_config --prod_or_test $params.submission_prod_or_test \
    --req_col_config $req_col_config --update false --send_submission_email $params.send_submission_email
    """

    output:
        file '*'
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
        val wait_signal
        path submission_config
        path validated_meta_path

    script:
        """
        run_submission.py --config $submission_config --update true --unique_name $params.batch_name
        """
    
    output:
        file '*'
} 
