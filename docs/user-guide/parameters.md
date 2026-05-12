# Parameters

All parameters have defaults in `nextflow.config`. Override any of them on the command line with `--param_name value`, or set them permanently in your own config file.

---

## Input Files

| Parameter | Description | Default |
|---|---|---|
| `--ref_fasta_path` | Reference FASTA file | mpox NC063383 |
| `--meta_path` | Metadata Excel file (`.xlsx`) | mpox template |
| `--ref_gff_path` | Reference GFF for annotation | mpox NC063383 |

---

## Workflow

| Parameter | Description | Default |
|---|---|---|
| `--workflow` | Which workflow to run (see options below) | `biosample_and_sra` |
| `--submission` | Enable/disable submission step | `true` |
| `--annotation` | Enable/disable annotation step | `true` |
| `--dry_run` | Prepare files but skip FTP upload | `false` |
| `--prod_submission` | Submit to Production instead of Test | `false` |

### `--workflow` options

| Value | What it does |
|---|---|
| `biosample_and_sra` | Submit to BioSample and SRA |
| `genbank` | Submit to GenBank (requires BioSample accessions) |
| `fetch_accessions` | Pull `report.xml` and update the metadata Excel file |
| `full_submission` | BioSample + SRA → wait → fetch accessions → GenBank |
| `update_submission` | Re-submit BioSample with an updated metadata file |

---

## Organism / Package

| Parameter | Description | Options |
|---|---|---|
| `--organism_type` | Organism type (controls annotation and GenBank format) | `virus`, `bacteria`, `eukaryote` |
| `--virus_subtype` | Virus subtype (controls VADR models and repeat library) | `mpxv`, `rsv`, `variola` |
| `--biosample_pkg` | Override BioSample package | e.g. `wastewater`, `onehealth` |

---

## Submission

| Parameter | Description | Default |
|---|---|---|
| `--submission_config` | Path to submission config YAML | `conf/submission_config.yaml` |
| `--submission_mode` | Upload protocol | `ftp` (`sftp` also supported) |
| `--biosample` | Submit to BioSample | `true` |
| `--sra` | Submit to SRA | `true` |
| `--batch_size` | Samples per submission batch | `5` |
| `--submission_wait_time` | Seconds to wait before fetching reports (`calc` = 30s × batch_size) | `calc` |
| `--submission_outdir` | Directory for raw submission outputs | `submission_outputs` |
| `--final_submission_outdir` | Directory for reports and updated Excel | `final_submission_outputs` |
| `--original_submission_outdir` | Path to original submission outputs (for `update_submission` workflow) | `""` |
| `--send_submission_email` | Send email notification when GenBank submission completes | `false` |

> **Tip:** We strongly recommend `--batch_size 50` or less for large datasets. NCBI prefers batched submissions over hundreds of individual files.

---

## Validation

| Parameter | Description | Default |
|---|---|---|
| `--validation_outdir` | Output directory for validation results | `validation_outputs` |
| `--date_format_flag` | Date output format: `s` (YYYY-MM), `v` (YYYY-MM-DD), `o` (unchanged) | `s` |
| `--remove_demographic_info` | Replace host_sex, host_age, race, ethnicity with "Not Provided" | `false` |
| `--validate_custom_fields` | Enable validation of custom metadata fields | `false` |
| `--custom_fields_file` | Path to custom fields JSON | example JSON in `assets/` |

---

## LLM Features

| Parameter | Description | Default |
|---|---|---|
| `--use_llm` | Enable OpenAI-powered validation hints and report interpretation | `false` |
| `--llm_model` | OpenAI model to use | `gpt-4o-mini` |

When `--use_llm true` is set, the pipeline:
- Reads validation errors and writes plain-English fix suggestions to `error_llm_suggestions.txt`
- Interprets NCBI `report.xml` results and writes a summary to `<batch_id>_llm_interpretation.txt`

The API key is read from (in order): Nextflow Secret `OPENAI_API_KEY`, `.env` file, environment variable `OPENAI_API_KEY`.

When `--use_llm false` (default), no OpenAI calls are made and behavior is identical to the pre-LLM version.

---

## Annotation

### General

| Parameter | Description | Default |
|---|---|---|
| `--repeatmasker_liftoff` | Use RepeatMasker + Liftoff (poxviruses) | `true` |
| `--vadr` | Use VADR annotation | `false` |
| `--bakta` | Use Bakta annotation (bacteria) | `false` |
| `--final_liftoff_outdir` | Output directory for Liftoff results | `repeatmasker_liftoff_outputs` |
| `--vadr_outdir` | Output directory for VADR results | `vadr_clean_outputs` |
| `--bakta_outdir` | Output directory for Bakta results | `bakta_outputs` |

### Liftoff tuning

| Parameter | Description | Default |
|---|---|---|
| `--lift_parallel_processes` | Parallel processes | `8` |
| `--lift_coverage_threshold` | Min coverage for feature mapping | `0.5` |
| `--lift_child_feature_align_threshold` | Min identity for child features | `0.5` |
| `--lift_copy_threshold` | Min identity to call a gene a copy | `1.0` |
| `--lift_distance_scaling_factor` | Distance scaling factor | `2.0` |
| `--lift_flank` | Flanking fraction of gene length | `0.0` |
| `--lift_overlap` | Max overlap fraction | `0.1` |
| `--lift_mismatch` | Mismatch penalty | `2` |
| `--lift_gap_open` | Gap open penalty | `2` |
| `--lift_gap_extend` | Gap extend penalty | `1` |
| `--lift_unmapped_features_file_name` | Unmapped features output filename | `output.unmapped_features.txt` |
| `--lift_feature_types` | Path to feature types file | `assets/feature_types.txt` |
| `--lift_minimap_path` | Path to minimap2 binary (if not on PATH) | `N/A` |
| `--lift_feature_database_name` | Feature database name (built from GFF if not set) | `N/A` |

### Bakta

All Bakta parameters use the `--bakta_` prefix. See [Bakta docs](https://github.com/oschwengers/bakta) for full details.

| Parameter | Description | Default |
|---|---|---|
| `--bakta_db_type` | Database size | `light` |
| `--bakta_db_path` | Path to existing Bakta database | `""` |
| `--download_bakta_db` | Download Bakta database at runtime | `""` |
| `--bakta_min_contig_length` | Minimum contig length | `5` |
| `--bakta_threads` | CPU threads | `2` |
| `--bakta_gram` | Gram type for signal peptide prediction | `?` |
| `--bakta_genus` | Genus name | `N/A` |
| `--bakta_species` | Species name | `N/A` |
| `--bakta_strain` | Strain name | `N/A` |
| `--bakta_translation_table` | Translation table number | `11` |
| `--bakta_compliant` | Force INSDC-compliant output | `true` |

---

## General / Output

| Parameter | Description | Default |
|---|---|---|
| `--outdir` | Top-level output directory | `results` |
| `--publish_dir_mode` | How Nextflow copies outputs (`copy`, `move`, `link`) | `copy` |
| `--overwrite_output` | Overwrite existing outputs | `true` |
| `--save_reference` | Save the downloaded reference/database | `false` |
