# TOSTADAS — Toolkit for Open Sequence Triage, Annotation and DAta Submission

A portable, open-source Nextflow pipeline that automates pathogen genomic data submission to NCBI public repositories. TOSTADAS reduces the barrier to timely data sharing by handling the error-prone steps of metadata validation, genome annotation, and file submission in a single reproducible workflow.

## What TOSTADAS Does

### 1 — Metadata Validation

Reads your Excel metadata file, checks it against NCBI requirements for your chosen BioSample package, flags problems, and produces cleaned batch TSV files ready for submission. Supports custom BioSample packages and optional LLM-powered error suggestions.

### 2 — Genome Annotation (optional)

Annotates assembled genomes before GenBank submission using whichever tool fits your pathogen:

| Tool | Best for |
|---|---|
| RepeatMasker + Liftoff | Poxviruses (mpox, variola) |
| VADR | Mpox, RSV |
| Bakta | Bacteria |

You can also supply your own pre-annotated GFF/TBL files and skip this step.

### 3 — Submission

Packages files into NCBI-compliant submission bundles, uploads them via FTP/SFTP, waits for processing, fetches `report.xml`, and writes a final accession CSV plus an updated Excel file with accession IDs filled in.

Supports BioSample, SRA, and GenBank. All three can be chained with `--workflow full_submission`.

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/CDCgov/tostadas.git && cd tostadas

# 2. Add NCBI credentials
cp conf/submission_config.yaml conf/my_config.yaml
# Fill in NCBI_username, NCBI_password, NCBI_Namespace, etc.

# 3. Test run (dry-run by default)
nextflow run main.nf \
  -profile test,mpox,singularity \
  --workflow biosample_and_sra \
  --submission_config conf/my_config.yaml
```

See the [Installation Guide](user-guide/installation.md) for full setup instructions.

---

## Quick Links

### General Usage

| [Installation](user-guide/installation.md) | [NCBI Account Setup](user-guide/general_NCBI_submission_guide.md) | [Submission Guide](user-guide/submission_guide.md) | [Parameters](user-guide/parameters.md) | [Outputs](user-guide/outputs.md) | [Profiles](user-guide/profile.md) |
|---|---|---|---|---|---|

### Advanced Usage

| [Custom Metadata](user-guide/custom_metadata_guide.md) | [User-Provided Annotation](user-guide/user_provided_annotation_guide.md) | [Wastewater Submission](user-guide/wastewater_guide.md) | [VADR Installation](user-guide/vadr_install.md) |
|---|---|---|---|

### Help

| [Troubleshooting](user-guide/troubleshooting.md) | [Get in Touch](user-guide/get-in-touch.md) | [Contributors](user-guide/contributions.md) |
|---|---|---|
