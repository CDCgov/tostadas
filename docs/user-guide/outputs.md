# Outputs

## Pipeline Overview

The workflow will generate outputs in the following order:

- **Validation**
    - Responsible for QC of metadata
    - Aligns sample metadata .xlsx to sample .fasta
    - Formats metadata into .tsv format
- **Annotation**
    - Extracts features from .gff
    - Aligns features
    - Annotates sample genomes outputting .gff
- **Submission**
    - Formats for database submission
    - In full\_submission mode, the pipeline polls NCBI for reports using exponential backoff before proceeding to GenBank submission.

## Output Directory Formatting

The outputs are recorded in the directory specified within the nextflow.config file and will contain the following:

```
<outdir>/
├── validation/
│   ├── batched_tsvs/
│   │   ├── batch_1.tsv ... batch_N.tsv
│   │   └── batch_summary.json
│   ├── error.txt
│   ├── genbank/
│   │   └── <sample>_cleaned.fsa
│   └── validated_metadata_all_samples.tsv
├── annotation/
│   └── vadr/  (or bakta/ or liftoff/)
│       ├── <sample>/
│       │   ├── gffs/
│       │   ├── tbl/
│       │   └── errors/
│       ├── batch_pass_fail.tsv
│       └── batch_alerts.tsv
├── submission/
│   ├── biosample_sra/
│   │   └── batch_N/
│   │       ├── biosample/
│   │       │   ├── submission.xml
│   │       │   └── submit.ready
│   │       ├── sra/ (if SRA data submitted)
│   │       ├── prep_submission.log
│   │       └── submission.log
│   └── genbank/
│       ├── batch_N/
│       │   └── genbank/
│       │       └── <sample>/
│       │           ├── <sample>.sqn
│       │           ├── <sample>.zip
│       │           ├── <sample>.tbl
│       │           └── sequence.fsa
│       ├── all_pass_sqn/
│       │   └── *.sqn (VADR-passing samples)
│       ├── all_fail_sqn/
│       │   └── *.sqn (VADR-failing samples)
│       ├── submission_qc_report.tsv
│       ├── prep_submission.log
│       └── submission.log
└── accessions/
    ├── batch_N/
    │   └── biosample/
    │       └── report.xml
    ├── submission_report.csv
    └── <metadata_name>_updated.xlsx
```

### QC Report and SQN Sorting

When VADR annotation is enabled, the `QC_REPORT` process sorts SQN files by annotation status and produces a summary report under `submission/genbank/`:

- **`all_pass_sqn/`** contains SQN files for samples that passed VADR annotation with no fatal alerts. These samples are ready for GenBank submission.
- **`all_fail_sqn/`** contains SQN files for samples that triggered VADR alerts such as frameshifts, premature stop codons, or low-similarity regions. These samples were not submitted automatically.
- **`submission_qc_report.tsv`** lists each sample alongside its VADR status (PASS or FAIL), providing a single file for reviewing annotation outcomes across the entire run.

!!! warning
    Samples in `all_fail_sqn/` should be reviewed before submitting to NCBI. Common causes of failure include sequencing errors, low-quality regions, and genuine biological mutations (e.g., frameshifts). Some failures may be resolvable by trimming or correcting the input sequence.

### BioSample Accession Embedding in SQN Files

In `full_submission` mode, the SQN file's DBLink section contains both the BioProject accession and the BioSample accession (SAMN number). This happens automatically because the pipeline merges accessions retrieved from NCBI into the metadata before the GenBank prep step. As a result, the generated SQN files already contain the correct BioSample linkage without manual intervention.

## Understanding Pipeline Outputs

The pipeline outputs include:

- `batch_<n>.tsv` files for each sample (one for each sample batch)
- Separate fasta files for each sample
- Separate gff files for each sample
- Separate tbl files containing feature information for each sample
- Submission log files
    - This output is found in the `submission/` directory within your specified output directory

## Key Output File Descriptions

### Validation Outputs

| File | Description |
|------|-------------|
| `validation/error.txt` | Lists validation errors and warnings for each sample. Errors indicate issues that prevent submission (e.g., missing required fields). Warnings flag potential data quality issues that do not block submission. |
| `validation/batch_*.tsv` | Validated metadata split into submission batches. Each file contains the samples assigned to that batch, with all field names normalized and values cleaned according to NCBI requirements. The number of files depends on `--batch_size`. |

### Annotation Outputs

| File | Description |
|------|-------------|
| `annotation/vadr/batch_pass_fail.tsv` | Per-sample VADR pass/fail status. Each row contains the sample name, pass or fail designation, and the VADR model classification used for annotation. Samples that fail VADR are excluded from GenBank submission. |
| `annotation/vadr/batch_alerts.tsv` | Detailed VADR alert information across all samples. Each row describes a specific alert (e.g., sequence length discrepancy, unexpected feature) with the alert code, severity, and affected sequence region. |

### Submission Outputs

| File | Description |
|------|-------------|
| `submission/batch_*/biosample/submission.xml` | BioSample submission XML for the batch. Contains sample attributes, organization details, and BioSample package information formatted for NCBI upload. |
| `submission/batch_*/genbank/<sample>/<sample>.sqn` | GenBank Sequin file generated by table2asn. Contains the annotated sequence, feature table, and submission metadata in ASN.1 format. This is the primary file used for GenBank submission of annotated viruses. |
| `submission/batch_*/genbank/<sample>/<sample>.zip` | Submission package containing all files needed for GenBank submission: the SQN file, SBT template, FSA (FASTA), SRC (source modifiers), and CMT (structured comments). For email-based submissions, this zip file is sent to NCBI. |

### Accession Outputs

| File | Description |
|------|-------------|
| `accessions/submission_report.csv` | Parsed NCBI accession report. Contains the submission status and assigned accession numbers (BioSample, SRA, GenBank) for each sample, extracted from NCBI report XML files. |
| `accessions/<metadata_name>_updated.xlsx` | Original input metadata augmented with accession IDs retrieved from NCBI. The filename is based on the input metadata file name. This file combines the validated metadata with BioSample accessions, SRA accessions, and any GenBank accessions available at the time of report retrieval. Use this file as input for downstream workflows (e.g., the `genbank` workflow requires `biosample_accession` values). |

## Interpreting VADR Results

When VADR annotation is enabled, the pipeline produces two summary files in the `annotation/vadr/` directory. These files provide a quick overview of annotation quality across all samples in the run.

### batch_pass_fail.tsv

This file contains one row per sample with the following columns:

| Column | Description |
|--------|-------------|
| `sample` | Sample identifier |
| `idx` | Sample index within the batch |
| `model` | VADR model used for annotation |
| `group` | Model group (e.g., the virus family) |
| `subgroup` | Model subgroup (e.g., the specific genotype) |
| `num_seqs` | Number of sequences in the sample |
| `num_pass` | Number of sequences that passed VADR validation |
| `num_fail` | Number of sequences that failed VADR validation |

A sample passes VADR validation when no fatal alerts are raised against any of its sequences. Samples with one or more fatal alerts are marked as failed. Only sequences that pass VADR validation are suitable for GenBank submission.

### batch_alerts.tsv

This file lists every alert raised during VADR annotation, with one row per alert:

| Column | Description |
|--------|-------------|
| `sequence` | Sequence identifier that triggered the alert |
| `model` | VADR model used |
| `feature-type` | Type of feature affected (e.g., CDS, gene) |
| `feature-name` | Name of the specific feature |
| `error` | Alert code (e.g., `mutendcd`, `lowsim5s`) |
| `seq-coords` | Coordinates of the problem region in the query sequence |
| `mdl-coords` | Corresponding coordinates in the reference model |
| `error-description` | Human-readable description of the alert |

### Common VADR alerts

The following alerts appear frequently and are worth understanding:

- **`mutendcd` (early stop codon)** -- A premature stop codon was found in a CDS. This is a fatal alert and prevents GenBank submission. It often indicates a frameshift mutation or a sequencing error.
- **`lowsim5s` / `lowsim3s` / `lowsimis` (low similarity)** -- A region of the sequence has low similarity to the reference model at the 5' end, 3' end, or internally. Non-fatal alerts indicate minor divergence; fatal versions indicate the sequence may not match the expected organism.
- **`cdslene` / `cdslens` (CDS length)** -- The CDS length is not a multiple of three, or differs from the expected length by more than the allowed threshold. This typically indicates an insertion or deletion.
- **`indf5loc` / `indf3loc` (indefinite boundary)** -- The start or end of a feature could not be precisely located. This is common in sequences with low coverage at the termini.

!!! tip
    For a complete list of VADR alert codes and their meanings, see the [VADR alert documentation](https://github.com/ncbi/vadr/blob/master/documentation/alerts.md).
