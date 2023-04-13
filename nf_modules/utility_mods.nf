/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    VALIDATE PARAMS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process VALIDATE_PARAMS {
    exec:
        // check the different ways to run params
        def check = [params.run_docker, params.run_conda, params.run_singularity].count(true)
        if ( check != 1 && check != 0 ) {
            throw new Exception("More than two profiles between docker, conda, and singularity were passed in. Please pass in only one")
        } else if ( check == 0 ) {
             throw new Exception("Either docker, conda, or singularity must be selected as profile [docker, conda, singularity]. None passed in.")
        }

        // check that at least one annotator is selected 
        assert params.run_vadr == true || params.run_liftoff == true
  
        // check paths
        assert params.fasta_path
        assert params.ref_fasta_path
        assert params.ref_gff_path
        assert params.meta_path

        // check script params
        assert params.env_yml
        assert params.docker_container

        // check batch name 
        assert params.batch_name 

        // check output directories
        assert params.output_dir
        assert params.val_output_dir
        assert params.submission_output_dir
        if ( params.run_liftoff == true ) {
            assert params.final_liftoff_output_dir
        }
        if ( params.run_vadr == true ) {
            assert params.vadr_output_dir
        }

        // check liftoff params with int or float values
        assert params.lift_parallel_processes == 0 || params.lift_parallel_processes
        assert params.lift_mismatch
        assert params.lift_gap_open
        assert params.lift_gap_extend

        // check vadr specific params
        if ( params.run_vadr == true ) {
            assert params.docker_container_vadr
            assert params.docker_container_vadr instanceof String == true 
        }

        // check list of params with bool values
        assert params.scicomp == true || params.scicomp == false
        assert params.clear_nextflow_log == true || params.clear_nextflow_log == false
        assert params.clear_work_dir == true || params.clear_work_dir == false
        assert params.run_submission == true || params.run_submission == false
        assert params.cleanup == true || params.cleanup == false
        assert params.overwrite_output == true || params.overwrite_output == false
        assert params.val_date_format_flag == 's' || params.val_date_format_flag == 'o' || params.val_date_format_flag == 'v'
        assert params.val_keep_pi == true || params.val_keep_pi == false
        assert params.lift_print_version_exit == true || params.lift_print_version_exit == false
        assert params.lift_print_help_exit == true || params.lift_print_help_exit == false
        assert params.lift_infer_transcripts.toLowerCase() == "true" || params.lift_infer_transcripts.toLowerCase() == "false"
        assert params.lift_copies.toLowerCase() == "true" || params.lift_copies.toLowerCase() == "false"

        // check types for inputs
        expected_strings = [
            "fasta_path": params.fasta_path,
            "ref_fasta_path": params.ref_fasta_path,
            "ref_gff_path": params.ref_gff_path,
            "meta_path": params.meta_path,
            "env_yml": params.env_yml,
            "output_dir": params.output_dir,
            "lift_minimap_path": params.lift_minimap_path,
            "lift_feature_database_name": params.lift_feature_database_name
        ]

        expected_integers = [
            "lift_parallel_processes" : params.lift_parallel_processes,
            "lift_mismatch": params.lift_mismatch,
            "lift_gap_open": params.lift_gap_open,
            "lift_gap_extend": params.lift_gap_extend
        ]

        expected_floats = [
            "lift_coverage_threshold": params.lift_coverage_threshold,
            "lift_child_feature_align_threshold": params.lift_child_feature_align_threshold,
            "lift_copy_threshold": params.lift_copy_threshold,
            "lift_distance_scaling_factor": params.lift_distance_scaling_factor,
            "lift_flank": params.lift_flank,
            "lift_overlap": params.lift_overlap
        ]

        expected_strings.each { key, value ->
            if ( expected_strings[key] instanceof String == false ) {
                throw new Exception("Value must be of string type: $value used for $key parameter")
            }
        }

        expected_integers.each { key, value ->
            if ( expected_integers[key] instanceof Integer == false ) {
                throw new Exception("Value must be of integer type: $value used for $key parameter")
            }
        }

        expected_floats.each { key, value ->
            if ( expected_floats[key] instanceof Integer == true || expected_floats[key] instanceof String == true ) {
                throw new Exception("Value must be of float type and not integer or string: $value used for $key parameter")
            }
        }

        // Check input path parameters to see if they exist
        check_path_params = [
            "fasta_path": params.fasta_path,
            "ref_fasta_path": params.ref_fasta_path,
            "ref_gff_path": params.ref_gff_path,
            "meta_path": params.meta_path,
            "env_yml": params.env_yml,
            "lift_minimap_path": params.lift_minimap_path,
            "lift_feature_database_name": params.lift_feature_database_name,
            "vadr_models_dir": params.vadr_models_dir
        ]

        check_path_params.each { key, value ->
            if ( key == "lift_minimap_path" || key == "lift_feature_database_name" ) {
                try {
                    file ( check_path_params[key], checkIfExists: true )
                } catch(Exception e) {
                    if ( check_path_params[key] != "N/A" && check_path_params[key] != "n/a" && check_path_params[key] != "None" ) {
                        throw new Exception("Following path does not exist and is not one of the empty vals (N/A, n/a, or None) for: $value used for $key")
                    }
                }
            } else {
                try {
                    file( check_path_params[key], checkIfExists: true )
                } catch(Exception e) {
                     throw new Exception("Following path does not exist: $value used for $key parameter")
                }
            }
        }
    output:
        val true
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                CLEANUP FILES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process CLEANUP_FILES {
    input:
        val signal
    exec:
        // clear all .nextflow.log files
        if ( params.clear_nextflow_log == true ) {
            dir = file("$projectDir")
            list_of_log_files = dir.listFiles()
            for ( def file : list_of_log_files ) {
                file_stripped = file.getBaseName()
                if( file_stripped == ".nextflow.log" ) {
                    file.setPermissions('rwxr-xr-x')
                    file.delete()
                    try {
                        assert dir.isFile() == false
                    } catch(Exception e) {
                        throw new Exception("Did not properly delete the work directory")
                    }
                }
            }
        }

        // clear all work subdirectories except for conda if present
        dir = file("$workDir")
        if ( params.clear_work_dir == true && dir.isDirectory() == true ) {
            dir.eachFile {
                if ( it.getSimpleName() != 'conda' ) {
                    it.setPermissions('rwxr-xr-x')
                    it.deleteDir()
                }
            }
        }

        // clear conda env inside of work directory
        dir = file("$workDir")
        if ( params.clear_conda_env == true && dir.isDirectory() ) {
            dir.eachFile {
                if ( it.getSimpleName() == 'conda' ) {
                    it.setPermissions('rwxr-xr-x')
                    it.deleteDir()
                }
            }
        }

        // clear nextflow results completely
        dir = file("$params.output_dir")
        if ( params.clear_nf_results == true && dir.isDirectory() == true ) {
            dir.setPermissions('rwxr-xr-x')
            dir.deleteDir()
            try {
                assert dir.isDirectory() == false
            } catch(Exception e) {
                throw new Exception("Nextflow results directory was not properly deleted: $params.output_dir")
            }
        }
    output:
        val true
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                  WAIT PROCESS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process WAIT {

    label 'main'
    
    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $parmas.env_yml")
        }
    }

    input:
        val submission_signal
        val wait_time

    script:
        """
        submission_utility.py --wait true --wait_time $wait_time
        """

    output:
        val true
}

process GET_WAIT_TIME {
    input:
        val meta_signal
        val validated_meta_path
    exec:
        if ( params.submission_wait_time != 'calc' ) {
            submission_wait_time = params.submission_wait_time
        } else {
            i = validated_meta_path.toList().size
            submission_wait_time = 3 * 60 * i
        }
    output:
        val submission_wait_time
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                           CHECK FOR SUBMISSION ENTRY POINT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process GENERAL_SUBMISSION_ENTRY_CHECK {

    exec:
        // check the different ways to run params
        def check = [params.run_docker, params.run_conda, params.run_singularity].count(true)
        if ( check != 1 && check != 0 ) {
            throw new Exception("More than two profiles between docker, conda, and singularity were passed in. Please pass in only one")
        } else if ( check == 0 ) {
            throw new Exception("Either docker, conda, or singularity must be selected as profile [docker, conda, singularity]. None passed in.")
        }

        // check that certain variables are specified
        try {
            assert params.submission_prod_or_test 
            assert params.submission_database 
            assert params.batch_name
            assert params.submission_config
        } catch (Exception e) {
            throw new Exception("Batch name not specified for submission")
        }

    output:
        val true
}

process ONLY_INITIAL_SUBMISSION_ENTRY_CHECK {
    
    exec:
        // check that certain params are specified 
        try {
            assert params.submission_only_meta
            assert params.submission_only_fasta
            assert params.submission_only_gff
            assert params.submission_output_dir 
            assert params.submission_wait_time
            assert params.req_col_config
            assert params.send_submission_email == true || params.send_submission_email == false
        } catch (Exception e) {
            throw new Exception("Paths to the (1) validated metadata file, (2) split fasta file, and (3) reformatted gff file must be specified, as well as submission output directory and wait time")
        }

        // check that paths are strings
        for ( def path : [params.submission_only_meta, params.submission_only_fasta, params.submission_only_gff] ) {
            if ( path instanceof String == false ) {
                throw new Exception("Value must be of string type: $path used instead")
            }
        }
    
    output:
        val true
}

process ONLY_UPDATE_SUBMISSION_ENTRY_CHECK {
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

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            PREP SUBMISSION ENTRY INPUTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process PREP_SUBMISSION_ENTRY {

    label 'main'

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
        val update_entry

    script:
        """
        submission_utility.py --prep_submission_entry true --update_entry $update_entry --meta_path $validated_meta --fasta_path $fasta --gff_path $annotated_gff
        """
     
    output: 
        path "tsv_submit_entry/*", emit: tsv
        path "fasta_submit_entry/*", emit: fasta
        path "gff_submit_entry/*", emit: gff
}

process PREP_UPDATE_SUBMISSION_ENTRY {

    label 'main'

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