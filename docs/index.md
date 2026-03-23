# TOSTADAS -- Toolkit for Open Sequence Triage, Annotation and Database Submission

## Pathogen Annotation and Submission Pipeline

A portable, open-source pipeline designed to streamline submission of pathogen genomic data to public repositories. Reducing barriers to timely data submission increases the value of public repositories for both public health decision making and scientific research. TOSTADAS facilitates routine sequence submission by standardizing and automating:

+ Metadata Validation
+ Genome Annotation
+ File submission

TOSTADAS is designed to be flexible, modular, and pathogen agnostic, allowing users to customize their submission of raw read data, assembled genomes, or both. The current release has been tested with sequence data from Poxviruses, RSV, Measles, and select bacteria.

## Pipeline Summary

### (1) Metadata Validation

Verifies that user-provided metadata conforms to NCBI standards and match the sequence data file(s), all of which are organized in an Excel spreadsheet ([example file](https://github.com/CDCgov/tostadas/blob/main/assets/metadata_template.xlsx)). By default, TOSTADAS uses a set of metadata fields appropriate for most pathogen genomic data submissions, but can be configured to accommodate custom metadata fields specific to any use case. A full guide to using custom metadata fields can be found here: [Custom Metadata Guide](user-guide/custom_metadata_guide.md)

### (2) Gene Annotation

Optional gene calling and feature annotation of assembled genomes (FASTA) using one of the following:

(1) RepeatMasker + Liftoff (viral)

*   Optimized for variola and mpox genomes, this workflow combines [RepeatMasker](https://www.repeatmasker.org/) for annotating repeat motifs and [Liftoff](https://github.com/agshumate/Liftoff) to annotate functional regions. Execution requires a reference genome (FASTA) and feature list (GFF3) definition. Modifications likely necessary for use with other pathogens.

(2) VADR (viral)

*   Annotates genomes using a set of homologous reference models. TOSTADAS comes packaged with support for [monkeypox virus](https://github.com/CDCgov/tostadas/tree/main/vadr_files/mpxv-models), RSV, and measles. A full list of supported pathogens is available from the [VADR GitHub Repository](https://github.com/ncbi/vadr).

(3) Bakta (bacterial)

*   Annotates bacterial genomes and plasmids using [Bakta](https://github.com/CDCgov/tostadas/tree/main#gene-annotation). Execution requires a reference database ([found here](https://zenodo.org/records/10522951)), which can be downloaded at runtime. All annotation options produce a general feature format file (GFF) and NCBI feature table (TBL) compatible with downstream NCBI submission requirements.

### (3) Submission

Prepare necessary submission files for BioSample, SRA, and/or GenBank depending on the provided inputs and perform optional upload to NCBI via ftp. This workflow was adapted from the [SeqSender](https://github.com/CDCgov/seqsender) public database submission pipeline.

---

## Quick Links

### General Usage

| [Overview](index.md) | [Installation](user-guide/installation.md#environment-setup) | [General NCBI Guide](user-guide/general_NCBI_submission_guide.md#ncbi-center-account) | [Submission Guide](user-guide/submission_guide.md) | [Output](user-guide/outputs.md) | [Parameters](user-guide/parameters.md) | [Submission Details](user-guide/profile.md) |
| --- | --- | --- | --- | --- | --- | --- |

### Advanced Usage

| [Custom Metadata](user-guide/custom_metadata_guide.md) | [User Provided Annotation](user-guide/user_provided_annotation_guide.md) | [VADR Installation](user-guide/vadr_install.md) | [Wastewater Submission](user-guide/wastewater_guide.md) |
| --- | --- | --- | --- |

### CDC-Specific Usage

| [CDC User Guide](user-guide/cdc-user-guide.md#cdc-user-guide) |
| --- |

### Help and Support

| [Get in Touch](user-guide/get-in-touch.md) | [Contributions](user-guide/contributions.md) | [Troubleshooting](user-guide/troubleshooting.md) |
| --- | --- | --- |
