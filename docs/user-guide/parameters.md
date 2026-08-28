# Parameters

Default parameters are given in the nextflow.config file. This table lists the parameters that can be changed to a value, path or true/false. When changing these parameters pay attention to the required inputs and make sure that paths line-up and values are within range. To change a parameter you may change with a flag after the nextflow command or change them within your nextflow.config file.

!!! note
    Please note the correct formatting of parameter values. The `--submission_wait_time` parameter is deprecated; see the smart polling parameters (`--poll_initial_interval`, `--poll_max_interval`, `--poll_timeout`) in the Submission section.

## Input Files

| Param | Description | Input Required |
|---|---|---|
| `--ref_fasta_path` | Reference Sequence file path | Yes (path as string) |
| `--meta_path` | Metadata file path (.xlsx, .csv, .tsv, or .src) | Yes (path as string) |
| `--fasta_dir` | Directory of FASTA files; auto-populates `fasta_path` by matching `sample_name` to filenames (.fasta, .fa, .fna, .fas) | No (path as string) |
| `--ref_gff_path` | Reference gff file path for annotation | Yes (path as string) |

## General Subworkflow

| Param | Description | Input Required |
|---|---|---|
| `--submission` | Toggle for running submission | No (boolean, default: true) |
| `--annotation` | Toggle for running annotation (only runs in genbank workflow) | No (boolean, default: true) |
| `--dry_run` | Simulate submission and print a log | No (boolean, default: false) |
| `--workflow` | Specifies the workflow to execute, allowing users to choose the appropriate processing method | No (string, default: biosample_and_sra) |
| `--genbank_only` | Skip BioSample/SRA-specific validation; use when generating SQN files for GenBank only | No (boolean, default: false) |
| `--sbt` | Path to an existing .sbt template file for table2asn (bypasses auto-generation from submission_config.yaml) | No (path as string) |

### Workflow Options

The following workflows are available for the `--workflow` parameter:

- **biosample_and_sra** -- Runs a submission to BioSample and SRA.
- **genbank** -- Runs a GenBank submission.
- **fetch_accessions** -- Fetches reports and updates the metadata file.
- **full_submission** -- Executes BioSample and SRA submissions, polls NCBI for reports using exponential backoff (30s--120s intervals, 30min timeout), updates the metadata file with accession IDs, and then performs the GenBank submission.
- **update_submission** -- Executes a BioSample submission using an updated metadata Excel file.

!!! note
    The GenBank submission cannot complete without a BioSample accession ID.

## General Settings

| Param | Description | Input Required |
|---|---|---|
| `--date_format_flag` | Flag to specify the date format. Options: s (default, YYYY-MM), v (verbose, YYYY-MM-DD), o (original, unchanged), n (NCBI short month, Mon.YY) | No (string, default: s) |
| `--publish_dir_mode` | Mode for publishing directory, e.g., 'copy' or 'move' | No (string, default: copy) |
| `--remove_demographic_info` | Flag to remove demographic info. If true, values in host_sex, host_age, race, ethnicity are set to 'Not Provided' | No (boolean, default: false) |
| `--batch_size` | The number of samples to prepare in one submission file | No (integer, default: 5) |
| `--organism_type` | Used for annotation and to choose GenBank workflow. Options: bacteria, virus, eukaryote | No (string) |
| `--virus_subtype` | Used for VADR annotation. Options: mpxv, rsv, mev | No (string) |
| `--mol_type` | Molecule type passed to table2asn (e.g., "genomic", "viral cRNA"). Used by measles and RSV profiles | No (string, default: "genomic") |
| `--biosample_pkg` | BioSample package type (e.g., wastewater, onehealth) | No (string, default: null) |
| `--genome_representation` | WGS genome representation. Accepted values are Full or Partial | No (string, default: "Full") |
| `--expected_final_version` | WGS expected final version. Accepted values are Yes or No | No (string, default: "Yes") |
| `--strip_pub_block` | Removes publication citation and DBLink blocks from .sqn files per NCBI preference. Used by the measles profile | No (boolean, default: false) |

## General Output

| Param | Description | Input Required |
|---|---|---|
| `--outdir` | File path to submit outputs from pipeline | No (path as string, default: results) |
| `--overwrite_output` | Toggle to overwriting output files in directory | No (boolean, default: true) |
| `--annotation_outdir` | Base directory name for annotation outputs (vadr, bakta, liftoff subdirectories) | No (folder name as string, default: "annotation") |
| `--accessions_outdir` | Either name or relative/absolute path for the final outputs from submission report fetching | No (string or path, default: "accessions") |
| `--updated_meta_path` | Path to accession-augmented metadata Excel from a prior BioSample/SRA run. Required for standalone genbank workflow; auto-detected in full_submission mode. | No (path, default: auto-detected) |

## Validation

| Param | Description | Input Required |
|---|---|---|
| `--validation_outdir` | File path for outputs specific to validate sub-workflow | No (folder name as string, default: "validation") |
| `--validate_custom_fields` | Toggle checks/transformations for custom metadata fields on/off | No (boolean, default: false) |
| `--custom_fields_file` | Path to the JSON file containing custom metadata fields and their information | No (path as string) |

## Liftoff

| Param | Description | Input Required |
|---|---|---|
| `--annotation_outdir` | Base directory name for annotation outputs (liftoff outputs go to annotation/liftoff/) | No (folder name as string, default: "annotation") |
| `--lift_print_version_exit` | Print version and exit the program | No (boolean, default: false) |
| `--lift_print_help_exit` | Print help and exit the program | No (boolean, default: false) |
| `--lift_parallel_processes` | Number of parallel processes to use for liftoff | No (integer, default: 8) |
| `--lift_child_feature_align_threshold` | Map only if its child features align with sequence identity greater than this value | No (float, default: 0.5) |
| `--lift_unmapped_features_file_name` | Name of unmapped features file | No (string, default: output.unmapped_features.txt) |
| `--lift_copy_threshold` | Minimum sequence identity in exons/CDS for which a gene is considered a copy; default is 1.0 | No (float, default: 1.0) |
| `--lift_distance_scaling_factor` | Distance scaling factor; default is 2.0 | No (float, default: 2.0) |
| `--lift_flank` | Amount of flanking sequence to align as a fraction of gene length | No (float, default: 0.0) |
| `--lift_overlap` | Maximum fraction of overlap allowed by two features | No (float, default: 0.1) |
| `--lift_mismatch` | Mismatch penalty in exons when finding best mapping; default is 2 | No (integer, default: 2) |
| `--lift_gap_open` | Gap open penalty in exons when finding best mapping; default is 2 | No (integer, default: 2) |
| `--lift_gap_extend` | Gap extend penalty in exons when finding best mapping; default is 1 | No (integer, default: 1) |
| `--lift_minimap_path` | Path to minimap if you did not use conda or pip | No (path, default: N/A) |
| `--lift_feature_database_name` | Name of the feature database, if none, will use ref gff path to construct one | No (string, default: N/A) |
| `--lift_feature_types` | Path to the file containing feature types | No (path, default: assets/feature_types.txt) |
| `--lift_coverage_threshold` | Minimum coverage threshold for feature mapping | No (float, default: 0.5) |
| `--repeatmasker_liftoff` | Flag to enable or disable RepeatMasker and Liftoff steps | No (boolean, default: false) |
| `--repeat_library` | Path to custom repeats library for RepeatMasker annotation | No (path) |

## VADR

| Param | Description | Input Required |
|---|---|---|
| `--vadr` | Toggle for running VADR annotation | No (boolean, default: false) |
| `--annotation_outdir` | Base directory name for annotation outputs (VADR outputs go to annotation/vadr/) | No (folder name as string, default: "annotation") |
| `--vadr_models_dir` | Directory containing VADR models for the target virus subtype | No (path, default: vadr_files/rsv-models) |
| `--vadr_opts` | Additional flags passed to VADR annotation (e.g., "-r --xnocomp" for RSV) | No (string, default: empty) |
| `--vadr_cm_url` | URL to download a VADR covariance model if one is not present locally | No (string, default: empty) |

## BAKTA

Controlling Bakta within TOSTADAS uses parameters of the same name with prefix `--bakta_`. For more details, visit the [Bakta GitHub page](https://github.com/oschwengers/bakta).

| Param | Description | Input Required |
|---|---|---|
| `--bakta` | Toggle for running Bakta annotation | No (boolean, default: false) |
| `--bakta_db_path` | Path to Bakta database if user is supplying database | No (path to database) |
| `--download_bakta_db` | Option to download Bakta database. Default is empty string; the bacteria profile sets it to true | No (true/false or empty string) |
| `--bakta_db_type` | Bakta database type (light or full) | No (string, default: light) |
| `--annotation_outdir` | Base directory name for annotation outputs (Bakta outputs go to annotation/bakta/) | No (folder name as string, default: "annotation") |
| `--bakta_min_contig_length` | Minimum contig size | No (integer, default: 5) |
| `--bakta_threads` | Number of threads to use while running annotation | No (integer, default: 2) |
| `--bakta_genus` | Organism genus name | No (string, default: N/A) |
| `--bakta_species` | Organism species name | No (string, default: N/A) |
| `--bakta_strain` | Organism strain name | No (string, default: N/A) |
| `--bakta_plasmid` | Name of plasmid | No (string, default: unnamed) |
| `--bakta_locus` | Locus prefix | No (string, default: contig) |
| `--bakta_locus_tag` | Locus tag prefix assigned by NCBI under your BioProject. Required for WGS GenBank submissions; without it the submission may be rejected | No (string, default: empty) |
| `--bakta_translation_table` | Translation table | No (integer, default: 11) |
| `--bakta_gram` | Gram stain type for signal peptide predictions: '+' (gram-positive), '-' (gram-negative), '?' (unknown) | No (string, default: ?) |
| `--bakta_skip_pseudo` | Skip pseudogene detection in Bakta annotation | No (string) |
| `--bakta_compliant` | Enable Bakta compliant mode for INSDC-compatible output | No (boolean, default: true) |
| `--bakta_skip_plot` | Skip generation of annotation plots | No (boolean, default: true) |
| `--save_reference` | Option to save the downloaded Bakta database | No (boolean, default: false) |

## Submission

| Param | Description | Input Required |
|---|---|---|
| `--biosample` | Submit to BioSample | No (boolean, default: true) |
| `--sra` | Submit to SRA | No (boolean, default: true) |
| `--submission_outdir` | Either name or relative/absolute path for the outputs from submission | No (name or path as string, default: "submission") |
| `--accessions_outdir` | Either name or relative/absolute path for the final outputs from submission report fetching | No (string or path, default: "accessions") |
| `--prod_submission` | Submit to NCBI production server. Set to true for real submissions. | No (boolean, default: false) |
| `--submission_config` | Configuration file for submission to public repos | No (path, default: conf/submission_config.yaml) |
| `--submission_wait_time` | **Deprecated.** Replaced by smart polling parameters below. Ignored if set | No (deprecated) |
| `--poll_initial_interval` | Initial polling interval in seconds for fetching NCBI reports | No (integer, default: 30) |
| `--poll_max_interval` | Maximum polling interval in seconds (backoff cap) | No (integer, default: 120) |
| `--poll_timeout` | Maximum total time in seconds to poll before giving up | No (integer, default: 1800) |
| `--send_submission_email` | Toggle email notification on/off | No (boolean, default: false) |
| `--submission_mode` | Transfer protocol for NCBI submission: ftp (default) or sftp | No (string, default: ftp) |

## Update Submission

| Param | Description | Input Required |
|---|---|---|
| `--original_submission_outdir` | Either name or relative/absolute path for the outputs from original submission (the one being updated) | Yes (name or path as string) |

!!! warning "About `--send_submission_email`"
    Email submission is triggered when GenBank sequences are submitted via email (virus pathway). The recipient address is specified in `submission_config.yaml` as `table2asn_email`.
