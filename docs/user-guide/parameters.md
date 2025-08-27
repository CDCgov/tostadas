# Parameters

Default parameters are given in the nextflow.config file. This table lists the parameters that can be changed to a value, path or true/false. When changing these parameters pay attention to the required inputs and make sure that paths line-up and values are within range. To change a parameter you may change with a flag after the nextflow command or change them within your nextflow.config file.

*   Please note the correct formatting and the default calculation of submission_wait_time at the bottom of the params table.

## Input Files

| Param | Description | Input Required |
| --- | --- | --- |
| --ref_fasta_path | Reference Sequence file path | Yes (path as string) |
| --meta_path | Meta-data file path for samples | Yes (path as string) |
| --ref_gff_path | Reference gff file path for annotation | Yes (path as string) |

## General Subworkflow

| Param | Description | Input Required |
| --- | --- | --- |
| --submission | Toggle for running submission | Yes (true/false as bool) |
| --annotation | Toggle for running annotation | Yes (true/false as bool) |
| --cleanup | Toggle for running cleanup subworkflows | Yes (true/false as bool) |
| --dry_run | Simulate submission and print a log. | No (true/false) |
| --workflow | Specifies the workflow to execute, allowing users to choose the appropriate processing method. | Yes (string) |

#### Workflow Options

The following workflows are available for the `--workflow` parameter:

- **biosample_and_sra**: Runs a submission to BioSample and SRA.
- **genbank**: Runs a GenBank submission.
- **fetch_accessions**: Fetches reports and updates the metadata file.
- **full_submission**: Executes BioSample and SRA submissions, waits 60 seconds multiplied by `params.batch_size`, fetches reports, updates the metadata file with accession IDs, and then performs the GenBank submission.

**Note**: The GenBank submission cannot complete without a BioSample accession ID.

## General Settings

| Param | Description | Input Required |
| --- | --- | --- |
| --date_format_flag | Flag to specify the date format. Options: s (default, YYYY-MM), v (verbose, YYYY-MM-DD), o (original, unchanged) | Yes (string) |
| --publish_dir_mode | Mode for publishing directory, e.g., 'copy' or 'move' | Yes (string) |
| --remove_demographic_info | Flag to remove demographic info. If true, values in host_sex, host_age, race, ethnicity are set to 'Not Provided' | Yes (true/false) |
| --batch_size | The number of samples to prepare in one submission file. | No (integer) |
| --processed_samples | Directory where processed samples are stored. | No (string or list) |

## Cleanup Subworkflow

| Param | Description | Input Required |
| --- | --- | --- |
| --clear_nextflow_log | Clears nextflow work log | Yes (true/false as bool) |
| --clear_work_dir | Param to clear work directory created during workflow | Yes (true/false as bool) |
| --clear_conda_env | Clears conda environment | Yes (true/false as bool) |
| --clear_nf_results | Remove results from nextflow outputs | Yes (true/false as bool) |

## General Output

| Param | Description | Input Required |
| --- | --- | --- |
| --outdir | File path to submit outputs from pipeline | Yes (path as string) |
| --overwrite_output | Toggle to overwriting output files in directory | Yes (true/false as bool) |
| --final_submission_output_dir | Either name or relative/absolute path for the final outputs from submission report fetching | No (string or path) |

## Validation

| Param | Description | Input Required |
| --- | --- | --- |
| --val_output_dir | File path for outputs specific to validate sub-workflow | Yes (folder name as string) |
| --validate_custom_fields | Toggle checks/transformations for custom metadata fields on/off | No (true/false as bool) |
| --custom_fields_file | Path to the JSON file containing custom metadata fields and their information | No (path as string) |

## Liftoff

| Param | Description | Input Required |
| --- | --- | --- |
| --final_liftoff_output_dir | File path to liftoff specific sub-workflow outputs | Yes (folder name as string) |
| --lift_print_version_exit | Print version and exit the program | Yes (true/false) |
| --lift_print_help_exit | Print help and exit the program | Yes (true/false) |
| --lift_parallel_processes | Number of parallel processes to use for liftoff | Yes (integer) |
| --lift_child_feature_align_threshold | Map only if its child features align with sequence identity greater than this value | Yes (float) |
| --lift_unmapped_features_file_name | Name of unmapped features file | Yes (path as string) |
| --lift_copy_threshold | Minimum sequence identity in exons/CDS for which a gene is considered a copy; default is 1.0 | Yes (float) |
| --lift_distance_scaling_factor | Distance scaling factor; default is 2.0 | Yes (float) |
| --lift_flank | Amount of flanking sequence to align as a fraction of gene length | Yes (float between 0.0 and 1.0) |
| --lift_overlap | Maximum fraction of overlap allowed by two features | Yes (float between 0.0 and 1.0) |
| --lift_mismatch | Mismatch penalty in exons when finding best mapping; default is 2 | Yes (integer) |
| --lift_gap_open | Gap open penalty in exons when finding best mapping; default is 2 | Yes (integer) |
| --lift_gap_extend | Gap extend penalty in exons when finding best mapping; default is 1 | Yes (integer) |
| --lift_minimap_path | Path to minimap if you did not use conda or pip | Yes (N/A or path as string) |
| --lift_feature_database_name | Name of the feature database, if none, will use ref gff path to construct one | Yes (N/A or name as string) |
| --lift_feature_types | Path to the file containing feature types | Yes (path as string) |
| --lift_coverage_threshold | Minimum coverage threshold for feature mapping | Yes (float) |
| --repeatmasker_liftoff | Flag to enable or disable RepeatMasker and Liftoff steps | Yes (true/false) |

## VADR

| Param | Description | Input Required |
| --- | --- | --- |
| --vadr | Toggle for running VADR annotation | Yes (true/false as bool) |
| --vadr_output_dir | File path to vadr specific sub-workflow outputs | Yes (folder name as string) |
| --vadr_models_dir | File path to models for MPXV used by VADR annotation | Yes (folder name as string) |

## BAKTA

Controlling Bakta within TOSTADAS uses parameters of the same name with prefix `--bakta_`. For more details, visit the [Bakta GitHub page](https://github.com/oschwengers/bakta).

| Param | Description | Input Required |
| --- | --- | --- |
| --bakta | Toggle for running Bakta annotation | Yes (true/false as bool) |
| --bakta_db_path | Path to Bakta database if user is supplying database | No (path to database) |
| --download_bakta_db | Option to download Bakta database | Yes (true/false) |
| --bakta_db_type | Bakta database type (light or full) | Yes (string) |
| --bakta_output_dir | File path to bakta specific sub-workflow outputs | Yes (folder name as string) |
| --bakta_min_contig_length | Minimum contig size | Yes (integer) |
| --bakta_threads | Number of threads to use while running annotation | Yes (integer) |
| --bakta_genus | Organism genus name | Yes (N/A or name as string) |
| --bakta_species | Organism species name | Yes (N/A or name as string) |
| --bakta_strain | Organism strain name | Yes (N/A or name as string) |
| --bakta_plasmid | Name of plasmid | Yes (unnamed or name as string) |
| --bakta_locus | Locus prefix | Yes (contig or name as string) |
| --bakta_locus_tag | Locus tag prefix | Yes (autogenerated or name as string) |
| --bakta_translation_table | Translation table | Yes (integer) |
| --bakta_gram | Gram type for signal peptide predictions | No ('+' '-' '?') |
| --save_reference | Option to save the downloaded Bakta database | No (true/false) |

## Sample Submission

| Param | Description | Input Required |
| --- | --- | --- |
| --genbank | Submit to GenBank | Yes (true/false as bool) |
| --sra | Submit to SRA | Yes (true/false as bool) |
| --biosample | Submit to Biosample | Yes (true/false as bool) |
| --gisaid | Submit to GISAID | Yes (true/false as bool) |
| --submission_outdir | Either name or relative/absolute path for the outputs from submission | Yes (name or path as string) |
| --submission_prod_or_test | Whether to submit samples for test or actual production | Yes (prod or test as string) |
| --submission_config | Configuration file for submission to public repos | Yes (path as string) |
| --submission_wait_time | Calculated based on sample number (3 \* 60 secs \* sample_num) | integer (seconds) |
| --send_submission_email | Toggle email notification on/off | Yes (true/false as bool) |
| --submission_mode | Mode of submission | Yes (string) |
| --update_submission | Flag to enable or disable updating existing submissions | Yes (true/false as bool) |

❗ Important note about `send_submission_email`: An email is only triggered if Genbank is being submitted to AND `table2asn` is the `genbank_submission_type`. As for the recipient, this must be specified within your submission config file under 'general' as `notif_email_recipient`.

