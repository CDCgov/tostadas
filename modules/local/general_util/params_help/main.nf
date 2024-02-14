/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            PRINT PARAMS HELP STATEMENT
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process PRINT_PARAMS_HELP {

    exec:
        log.info """
            Usage:
            The general command for running nextflow with values set in config:
            nextflow run main.nf

            To pass in arguments and override params in config:
            nextflow run main.nf --<param name> <param value>

            To access a specific sub-workflow via entrypoint:
            nextflow run main.nf -entry <name of sub workflow>

            Mandatory Arguments (either set in config of passed through command line):
            --meta_path                            Path to the metadata file (accepts string)
            --fasta_path                           Path to the fasta file (accepts string)
            --ref_fasta_path                       Path to the reference fasta file (accepts string)
            --ref_gff_path                         Path to the reference gff file (accepts string)

            --scicomp                              Flag for whether running on scicomp server or not (accepts bool: true/false)
            --docker_container                     Name of the docker container (accepts string)
            --docker_container_vadr                Name of the docker container to run VADR annotation (accepts string)

            --run_submission                       Flag for whether to run submission portion or not (accepts bool: true/false)
            --run_vadr                             Flag for whether to run VADR annotation or not (accepts bool: true/false)
            --run_liftoff                          Flag for whether to run LIFTOFF annotation or not (accepts bool: true/false)
            --cleanup                              Flag for whether to run the cleanup process (accepts bool: true/false)

            --clear_nextflow_log                   Defines the cleanup process further: whether to clear the nextflow log files (accepts bool: true/false)
            --clear_work_dir                       Defines the cleanup process further: whether to clear the work directory (accepts bool: true/false)
            --clear_conda_env                      Defines the cleanup process further: whether to clear the conda environment (accepts bool: true/false)
            --clear_nf_results                     Defines the cleanup process further: whether to clear the previous generated results (accepts bool: true/false)

            --env_yml                              Path to the .yml file for building the cond environment from (accepts string)
            --output_dir                           Name of the output directory for the results from nextflow (accepts string)
            --overwrite_output                     Flag for whether to overwrite the existing files in the output directory (accepts bool: true/false)
            --final_liftoff_output_dir             Name of the output directory for the annotation pipeline (accepts string)
            --val_output_dir                       Name of the output directory for the validation pipeline (accepts string)

            --val_date_format_flag                 Flag corresponding to format for date, possible options are 's', 'o', 'v'. Please consult documentation for more info.
            --val_keep_pi                          Flag to keep personal information or not (accepts bool: true/false)

            --lift_print_version_exit              Flag to print out the version of liftoff and exit (accepts bool: true/false)
            --lift_print_help_exit                 Flag to print out the help message for liftoff and exit (accepts bool: true/false)
            --lift_parallel_processes              Number of parallel processes to run when running liftoff (accepts integer)
            --lift_delete_temp_files               Flag to delete temporary files generated during annotation (accepts bool: true/false)
            --lift_coverage_threshold              Designate a feature mapped only if it aligns with coverage ≥A
            --lift_child_feature_align_threshold   Designate a feature mapped only if its child features usually exons/CDS align with sequence identity ≥S
            --lift_unmapped_features_file_name     Name of unmapped features file name
            --lift_copy_threshold                  Minimum sequence identity in exons/CDS for which a gene is considered a copy; must be greater than -s; default is 1.0
            --lift_distance_scaling_factor         Alignment nodes separated by more than a factor of D in the target genome will not be connected in the graph; by default D=2.0
            --lift_flank                           Amount of flanking sequence to align as a fraction [0.0-1.0] of gene length. This can improve gene alignment where gene structure differs between target and reference; by default F=0.0
            --lift_overlap                         Maximum fraction [0.0-1.0] of overlap allowed by 2 features; by default O=0.1
            --lift_mismatch                        Mismatch penalty in exons when finding best mapping; by default M=2
            --lift_gap_open                        Gap open penalty in exons when finding best mapping; by default GO=2
            --lift_gap_extend                      Gap extend penalty in exons when finding best mapping; by default GE=1
            --lift_infer_transcripts               Use if annotation file only includes exon/CDS features and does not include transcripts/mRNA
            --lift_copies                          Look for extra gene copies in the target genome
            --lift_minimap_path                    Path to minimap if you did not use conda or pip
            --lift_feature_database_name           Name of the feature database, if none, then will use ref gff path to construct one

            --vadr_output_dir                      Name of output directory for results from VADR annotation (accepts string)
            --vadr_models_dir                      Name of directory containing necessary model information to complete VADR annotation (accepts string; default is tostadas/vadr_files/mpxv-models)

            --submission_only_meta                 Path to the validated metadata directory if calling submission entrypoint (accepts string)
            --submission_only_gff                  Path to the reformatted gff directory if calling submission entrypoint (accepts string)
            --submission_only_fasta                Path to the split fasta files directory if calling submission entrypoint (accepts string)
            --processed_samples                    Path to the directory containing processed samples <batch_name>.<sample name> for update only entrypoint (accepts string)
            --submission_config                    Path to the configuration file used for the submission process (accepts string)
            --req_col_config                       Path to the required_columns.yaml file (accepts string)
            --submission_prod_or_test              Denotes whether to submit as a test or production (accepts string: test/prod)
            --batch_name                           Prefixes the sample names to group together certain samples during submission
            --send_submission_email                Flag for whether or not to send a notification email (specified in submission config) during genbank/table2asn submission (accepts bool: true/false)
            --submission_database                  Name of database for sample submissions; by default is 'submit' (accepts string: submit/genbank/sra/gisaid/biosample/joint_sra_biosample/all)

            Optional arguments:
            --submission_wait_time                  Overwrites the default calculation of (3 * 60 * num samples) in seconds for wait time after initial submission
            --help                                  Flag to call in help statements mentioned in this block
            """
}
