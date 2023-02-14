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
  
        // check paths
        assert params.fasta_path
        assert params.ref_fasta_path
        assert params.ref_gff_path
        assert params.meta_path

        // check script params
        assert params.liftoff_script
        assert params.validation_script
        assert params.submission_script
        assert params.env_yml

        // check batch name 
        assert params.batch_name 

        // check output directory
        assert params.output_dir

        // check liftoff params with int or float values
        assert params.lift_parallel_processes == 0 || params.lift_parallel_processes
        assert params.lift_mismatch
        assert params.lift_gap_open
        assert params.lift_gap_extend

        // check list of params with bool values
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
            "liftoff_script": params.liftoff_script,
            "validation_script": params.validation_script,
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
            "liftoff_script": params.liftoff_script,
            "validation_script": params.validation_script,
            "env_yml": params.env_yml,
            "lift_minimap_path": params.lift_minimap_path,
            "lift_feature_database_name": params.lift_feature_database_name
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
        val wait_time

    script:
        """
        submission_wait.py --wait_time $wait_time
        """

    output:
        val true
}

process GET_WAIT_TIME {
    input:
        val signal
        val validated_meta_path
        val entry_flag
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
process SUBMISSION_ENTRY_CHECK {
    exec:
        // check the different ways to run params
        def check = [params.run_docker, params.run_conda, params.run_singularity].count(true)
        if ( check != 1 && check != 0 ) {
            throw new Exception("More than two profiles between docker, conda, and singularity were passed in. Please pass in only one")
        } else if ( check == 0 ) {
             throw new Exception("Either docker, conda, or singularity must be selected as profile [docker, conda, singularity]. None passed in.")
        }
        
        // check that certain paths are specified
        try {
            assert params.submission_only_meta
            assert params.submission_only_fasta
            assert params.submission_only_gff
        } catch(Exception e) {
            throw new Exception("Paths to the (1) validated metadata file, (2) split fasta file, and (3) reformatted gff file must be specified")
        }
        for ( def path : [params.submission_only_meta, params.submission_only_fasta, params.submission_only_gff] ) {
            if ( path instanceof String == false ) {
                throw new Exception("Value must be of string type: $path used instead")
            }
        }

        // check that batch_name is specified
        try {
            assert params.batch_name
        } catch (Exception e) {
            throw new Exception("Batch name not specified for submission")
        }

    output:
        val true
}

/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                  PRESUBMISSION 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

/*
PRESUBMISSION {

    conda params.env_yml

    input:
        val wait_time

    shell:
        """
        #!/usr/bin/env python

        import time

        time.sleep($wait_time)
        """

}
*/