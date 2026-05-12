# Outputs

## Directory structure

All outputs land under `--outdir` (default: `results/`), organized by step:

```
results/
└── <metadata_file_name>/
    ├── validation_outputs/          # Metadata QC (configurable: --validation_outdir)
    │   ├── errors/                  # Validation error reports
    │   │   ├── errors.txt           # Structured error list
    │   │   └── error_llm_suggestions.txt   # (if --use_llm) Plain-English fix suggestions
    │   ├── fasta/                   # Per-sample FASTA files
    │   └── tsv_per_sample/          # Formatted metadata TSVs for submission
    │
    ├── repeatmasker_liftoff_outputs/  # Liftoff annotation (configurable: --final_liftoff_outdir)
    │   ├── errors/
    │   ├── fasta/
    │   ├── liftoff/                 # Raw Liftoff GFF output
    │   └── tbl/                     # Feature tables for GenBank
    │
    ├── vadr_clean_outputs/           # VADR annotation (configurable: --vadr_outdir)
    │   ├── fasta/
    │   ├── gffs/
    │   └── tbl/
    │
    ├── bakta_outputs/                # Bakta annotation (configurable: --bakta_outdir)
    │   ├── fasta/
    │   ├── gff/
    │   └── tbl/
    │
    ├── submission_outputs/           # Per-batch submission bundles (configurable: --submission_outdir)
    │   └── batch_<n>/
    │       ├── biosample/           # BioSample XML submission files
    │       ├── sra/                 # SRA submission files + FASTQ manifest
    │       ├── genbank/             # GenBank ASN.1 / table2asn files
    │       └── submission.log       # Upload log for this batch
    │
    └── final_submission_outputs/    # Reports and updated metadata (configurable: --final_submission_outdir)
        ├── <sample_name>_updated.xlsx    # Metadata Excel with accession IDs filled in
        ├── submission_report.csv         # Summary of all submitted samples and accessions
        └── batch_<n>_llm_interpretation.txt  # (if --use_llm) Plain-English report summary
```

---

## Key output files

### Validation outputs

| File | Description |
|---|---|
| `errors/errors.txt` | All metadata validation errors, one per line |
| `errors/error_llm_suggestions.txt` | OpenAI-generated suggestions for fixing each error (only if `--use_llm true`) |
| `tsv_per_sample/*.tsv` | Cleaned, formatted metadata TSVs ready for NCBI |

### Submission outputs

| File | Description |
|---|---|
| `batch_<n>/biosample/*.xml` | BioSample submission XML |
| `batch_<n>/sra/` | SRA submission package |
| `batch_<n>/genbank/*.sqn` or `*.asn` | GenBank submission files (from table2asn) |
| `batch_<n>/submission.log` | FTP/SFTP upload log with timestamps |

### Final submission outputs

| File | Description |
|---|---|
| `*_updated.xlsx` | Your original metadata file with `biosample_accession`, `sra_accession`, `genbank_accession` columns filled in |
| `submission_report.csv` | Flat CSV of all accessions — useful for downstream analysis |
| `batch_<n>_llm_interpretation.txt` | Plain-English interpretation of NCBI `report.xml` (only if `--use_llm true`) |

---

## Understanding accession IDs

| Database | Accession format | Example |
|---|---|---|
| BioSample | `SAMN########` | `SAMN12345678` |
| SRA | `SRR#######` | `SRR1234567` |
| GenBank | `OQ######` or organism-specific | `OQ123456` |

The `*_updated.xlsx` file is the canonical record — it contains all accessions in the same format as your input, ready for sharing with collaborators or uploading to reporting systems.

---

## Annotation outputs

If you ran annotation, per-sample GFF and TBL files are produced alongside the FASTAs. These are the inputs to the GenBank submission step — you generally don't need to inspect them directly unless debugging an annotation problem.

For VADR, any sequences that fail VADR validation are reported in `vadr_clean_outputs/errors/`. Review these before proceeding to GenBank submission.
