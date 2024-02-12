# Parameters

Default parameters are given in the nextflow.config file. This table lists the parameters that can be changed to a value, path or true/false. When changing these parameters pay attention to the required inputs and make sure that paths line-up and values are within range. To change a parameter you may change with a flag after the nextflow command or change them within your standard_params.config or standard.yaml file.

 * Please note the correct formatting and the default calculation of submission_wait_time at the bottom of the params table.
## 7.1 Input Files


|Param	     |Description	                                          |Input Required|
|------------|--------------------------------------------------------|-------------|
|--fasta_path|	Path to directory containing single sample fasta files| Yes (path as string)|
|--ref_fasta_path|	Reference Sequence file path|	Yes (path as string)|
|--meta_path|	Meta-data file path for samples|	Yes (path as string)
|--ref_gff_path|	Reference gff file path for annotation|	Yes (path as string)|
|--bakta_db_path|	Path to Bakta reference database|	Yes (path as string)|
|--env_yml|	Path to environment.yml file|	Yes (path as string)|

## 7.2 Run Environment
|Param	|Description	|Input Required|
|-------|---------------|--------------|
|--scicomp	|Flag for whether running on Scicomp or not|	Yes (true/false as bool)|
|--docker_container|	Name of the Docker container|	Yes, if running with docker profile (name as string)|
|--docker_container_vadr|	Name of the Docker container to run VADR annotation|	Yes, if running with docker profile (name as string)|
|--docker_container_bakta|	Name of the Docker container to run Bakta annotation|	Yes, if running with docker profile (name as string)|

## 7.3 General Subworkflow
|Param	|Description	|Input Required|
|-------|---------------|--------------|
|--run_submission	|Toggle for running submission	|Yes (true/false as bool)|
|--run_liftoff	|Toggle for running liftoff annotation	|Yes (true/false as bool)|
|--run_vadr	|Toggle for running vadr annotation	|Yes (true/false as bool)|
|--run_bakta	|Toggle for running Bakta annotation	|Yes (true/false as bool)|
|--cleanup	|Toggle for running cleanup subworkflows	|Yes (true/false as bool)|

## 7.4 Cleanup Subworkflow

|Param	|Description	|Input Required|
|-------|---------------|--------------|
|--clear_nextflow_log	|Clears nextflow work log	|Yes (true/false as bool)|
|--clear_nextflow_dir	|Clears nextflow working directory	|Yes (true/false as bool)|
|--clear_work_dir	|Param to clear work directory created during workflow	|Yes (true/false as bool)|
|--clear_conda_env	|Clears conda environment	|Yes (true/false as bool)|
|--clear_nf_results	|Remove results from nextflow outputs	|Yes (true/false as bool)|

## 7.5 General Output

|Param	|Description	|Input Required|
|-------|---------------|--------------|
|--output_dir	|File path to submit outputs from pipeline	|Yes (path as string)|
|--overwrite_output	|Toggle to overwriting output files in directory	|Yes (true/false as bool)|

## 7.6 Metadata Validation

|Param	|Description	|Input Required|
|-------|---------------|--------------|
|--val_output_dir	|File path for outputs specific to validate sub-workflow	|Yes (folder name as string)|
|--val_date_format_flag	|Flag to change date output	|Yes (-s, -o, or -v as string)|
|--val_keep_pi	|Flag to keep personal identifying info, if provided otherwise it will return an error	|Yes (true/false as bool)|
|--validate_custom_fields	|Toggle checks/transformations for custom metadata fields on/off	|No (true/false as bool)|
|--custom_fields_file	|Path to the JSON file containing custom metadata fields and their information	|No (path as string)|

## 7.7 Liftoff

|Param	|Description	|Input Required|
|-------|---------------|--------------|
|--final_liftoff_output_dir	|File path to liftoff specific sub-workflow outputs	|Yes (folder name as string)|
|--lift_print_version_exit	|Print version and exit the program	|Yes (true/false as bool)|
|--lift_print_help_exit	|Print help and exit the program	|Yes (true/false as bool)|
|--lift_parallel_processes	|Number of parallel processes to use for liftoff	|Yes (integer)|
|--lift_delete_temp_files	|Deletes the temporary files after finishing transfer	|Yes (true/false as string)|
|--lift_child_feature_align_threshold	|Only if its child features usually exons/CDS align with sequence identity ||
|--lift_unmapped_feature_file_name	|Name of unmapped features file name	|Yes (path as string)|
|--lift_copy_threshold	|Minimum sequence identity in exons/CDS for which a gene is considered a copy; must be greater than -s; default is 1.0	|Yes (float)|
|--lift_distance_scaling_factor	|Distance scaling factor; by default D =2.0	|Yes (float)|
|--lift_flank	|Amount of flanking sequence to align as a fraction of gene length	|Yes (float between [0.0-1.0])|
|--lift_overlap	|Maximum fraction of overlap allowed by 2 features	|Yes (float between [0.0-1.0])|
|--lift_mismatch	|Mismatch penalty in exons when finding best mapping; by default M=2	|Yes (integer)|
|--lift_gap_open	|Gap open penalty in exons when finding best mapping; by default GO=2	|Yes (integer)|
|--lift_gap_extend	|Gap extend penalty in exons when finding best mapping; by default GE=1	|Yes (integer)|
|--lift_infer_transcripts	|Use if annotation file only includes exon/CDS features and does not include transcripts/mRNA	|Yes (True/False as string)|
|--lift_copies	|Look for extra gene copies in the target genome	|Yes (True/False as string)|
|--lift_minimap_path	|Path to minimap if you did not use conda or pip	|Yes (N/A or path as string)|
|--lift_feature_database_name	|Name of the feature database, if none, then will use ref gff path to construct one	|Yes (N/A or name as string)|
|--repeat_lib	|Path to repeatmasker library	|No, default is mpox|

## 7.8 VADR

|Param	|Description	|Input Required|
|-------|---------------|--------------|
|--vadr_output_dir	|File path to vadr specific sub-workflow outputs	|Yes (folder name as string)|
|--vadr_models_dir	|File path to models for MPXV used by VADR annotation	|Yes (folder name as string)|

## 7.9 Bakta

|Param	|Description	|Input Required|
|-------|---------------|--------------|
|--bakta_db_path	|Path to Bakta database if user is supplying database	|No (path to database)|
|--download_bakta_db	|Option to download Bakta database	|Yes (true/false)|
|--bakta_db_type	|Bakta database type (light or full)	|Yes (string)|
|--bakta_output_dir	|File path to bakta specific sub-workflow outputs	|Yes (folder name as string)|
|--bakta_min_contig_length	|Minimum contig size	|Yes (integer)|
|--bakta_threads	|Number of threads to use while running annotation	|Yes (integer)|
|--bakta_genus	|Organism genus name	|Yes (N/A or name as string)|
|--bakta_species	|Organism species name	|Yes (N/A or name as string)|
|--bakta_strain	|Organism strain name	|Yes (N/A or name as string)|
|--bakta_plasmid	|Name of plasmid	|Yes (unnamed or name as string)|
|--bakta_locus	|Locus prefix	|Yes (contig or name as string)|
|--bakta_locus_tag	|Locus tag prefix	|Yes (autogenerated or name as string)|
|--bakta_translation_table	|Translation table	|Yes (integer)|
|--bakta_db_path	|Path to Bakta reference database	|Yes (path as string)|
|--bakta_db_type	|Type of database to use for annotation	|Yes (full/light as bool)|
|--download_bakta_db	|Toggle to download Bakta database	|Yes (true/false as bool)|
|--run_bakta	|Toggle for running Bakta annotation	|Yes (true/false as bool)|

## 7.10 Sample Submission

|Param	|Description	|Input Required|
|-------|---------------|--------------|
|--submission_output_dir	|Either name or relative/absolute path for the outputs from submission	|Yes (name or path as string)|
|--submission_prod_or_test	|Whether to submit samples for test or actual production	|Yes (prod or test as string)|
|--submission_config	|Configuration file for submission to public repos	|Yes (path as string)|
|--submission_wait_time	|Calculated based on sample number (3 * 60 secs * sample_num)	|integer (seconds)|
|--batch_name	|Name of the batch to prefix samples with during submission	|Yes (name as string)|
|--send_submission_email	|Toggle email notification on/off	|Yes (true/false as bool)|
|--req_col_config	|Path to the required_columns.yaml file	|Yes (path as string)|
|--processed_samples	|Path to the directory containing processed samples for update only submission entrypoint (containing <batch_name>.<sample_name> dirs)	|Yes (path as string)|

❗ Important note about send_submission_email: An email is only triggered if Genbank is being submitted to AND table2asn is the genbank_submission_type. As for the recipient, this must be specified within your submission config file under 'general' as 'notif_email_recipient'*

## 7.11 Entrypoint and User Provided Annotation

|Param	|Description	|Input Required|
|-------|---------------|--------------|
|--final_split_metas_path	|Full path directly to the directory containing validated metadata file(s) (1 per sample)	|Yes (path as string)|
|--final_annotated_files_path	|Full path directly to the directory containing annotation file(s) (1 per sample)	|Yes (path as string)|
|-- final_split_fastas_path	|Full path directly to the directory containing fasta(s) (1 per sample)	|Yes (path as string)|