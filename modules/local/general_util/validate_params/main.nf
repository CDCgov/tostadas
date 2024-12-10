/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                      VALIDATE PARAMS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

// Include the plugin
include { validateParameters; paramsSummaryLog; samplesheetToList } from 'plugin/nf-schema'

// Validate input parameters
validateParameters()

// Print summary of supplied parameters
log.info paramsSummaryLog(workflow)


process VALIDATE_PARAMS {

    exec:
        // check that metadata file is provided
        assert params.meta_path

        // check annotation paths
        if ( params.annotation ) {
            if ( params.repeatmasker_liftoff ) {
                assert params.ref_fasta_path
                assert params.ref_fasta_path
                assert params.ref_gff_path
                assert params.repeat_library
            }
            if ( params.vadr ) {
                assert params.vadr_models_dir
            }
            if ( params.bakta ) {
                if ( !params.download_bakta_db ) {
                    assert params.bakta_db_path
                }
            }
        }

        // check output directories
        // assert params.output_dir
        // assert params.val_output_dir
        // assert params.submission_output_dir

        // if ( params.liftoff == true ) {
        //    assert params.final_liftoff_output_dir
        // }
        // if ( params.vadr == true ) {
        //    assert params.vadr_output_dir
        // }
        // if ( params.bakta == true ) {
        //    assert params.bakta_output_dir
        // }

        // check liftoff params with int or float values
        if ( params.repeatmasker_liftoff == true ) {
            // Check whether populated or not 
            assert params.lift_parallel_processes == 0 || params.lift_parallel_processes
            assert params.lift_mismatch
            assert params.lift_gap_open
            assert params.lift_gap_extend 
            assert params.lift_print_version_exit == true || params.lift_print_version_exit == false
            assert params.lift_print_help_exit == true || params.lift_print_help_exit == false

            // Check data types 
            expected_liftoff_strings = [
                "lift_minimap_path": params.lift_minimap_path,
                "lift_feature_database_name": params.lift_feature_database_name  
            ]

            expected_liftoff_integers = [
                "lift_parallel_processes" : params.lift_parallel_processes,
                "lift_mismatch": params.lift_mismatch,
                "lift_gap_open": params.lift_gap_open,
                "lift_gap_extend": params.lift_gap_extend
            ]

            expected_liftoff_floats = [
                "lift_coverage_threshold": params.lift_coverage_threshold,
                "lift_child_feature_align_threshold": params.lift_child_feature_align_threshold,
                "lift_copy_threshold": params.lift_copy_threshold,
                "lift_distance_scaling_factor": params.lift_distance_scaling_factor,
                "lift_flank": params.lift_flank,
                "lift_overlap": params.lift_overlap
            ]

            expected_liftoff_strings.each { key, value ->
                if ( expected_liftoff_strings[key] instanceof String == false ) {
                    throw new Exception("Value must be of string type: $value used for $key parameter")
                }
            }

            expected_liftoff_integers.each { key, value ->
                if ( expected_liftoff_integers[key] instanceof Integer == false ) {
                    throw new Exception("Value must be of integer type: $value used for $key parameter")
                }
            }

            expected_liftoff_floats.each { key, value ->
                if ( expected_liftoff_floats[key] instanceof Integer == true || expected_liftoff_floats[key] instanceof String == true ) {
                    throw new Exception("Value must be of float type and not integer or string: $value used for $key parameter")
                }
            } 
        }

        // check bakta specific params 
        if ( params.bakta == true ) {
            assert params.meta_path
            assert params.bakta_min_contig_length
            assert params.bakta_translation_table
            assert params.bakta_genus
            assert params.bakta_species
            assert params.bakta_strain
            assert params.bakta_plasmid
            assert params.bakta_locus
            assert params.bakta_locus_tag
        }

        // check list of params with bool values
        assert params.clear_nextflow_log == true || params.clear_nextflow_log == false
        assert params.clear_work_dir == true || params.clear_work_dir == false
        assert params.submission == true || params.submission == false
        assert params.cleanup == true || params.cleanup == false
        assert params.overwrite_output == true || params.overwrite_output == false
        assert params.val_date_format_flag == 's' || params.val_date_format_flag == 'o' || params.val_date_format_flag == 'v'
        assert params.val_keep_pi == true || params.val_keep_pi == false

        // check types for inputs
        expected_strings = [
            "ref_fasta_path": params.ref_fasta_path,
            "ref_gff_path": params.ref_gff_path,
            "meta_path": params.meta_path,
            "output_dir": params.output_dir,   
        ]
        expected_strings.each { key, value ->
            if (!(value instanceof String || value instanceof org.codehaus.groovy.runtime.GStringImpl)) {
                throw new Exception("Value must be of string type: $value used for $key parameter")
            }
        }

    output:
        val true
}
