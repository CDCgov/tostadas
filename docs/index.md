# TOSTADAS

**Toolkit for Open Sequence Triage, Annotation and Database Submission**

A portable, open-source pipeline designed to streamline submission of pathogen genomic data to public repositories. Reducing barriers to timely data submission increases the value of public repositories for both public health decision making and scientific research. TOSTADAS facilitates routine sequence submission by standardizing and automating:

- Metadata Validation
- Genome Annotation
- File Submission

TOSTADAS is designed to be flexible, modular, and pathogen agnostic, allowing users to customize their submission of raw read data, assembled genomes, or both. The current release has been tested with sequence data from Poxviruses, RSV, Measles, and select bacteria.

---

## Pipeline Stages

### Metadata Validation

Verifies that user-provided metadata conforms to NCBI standards and matches the sequence data file(s), all of which are organized in an Excel spreadsheet ([example file](https://github.com/CDCgov/tostadas/blob/main/assets/metadata_template.xlsx)). By default, TOSTADAS uses a set of metadata fields appropriate for most pathogen genomic data submissions, but can be configured to accommodate custom metadata fields specific to any use case. See the [Custom Metadata Guide](user-guide/custom_metadata_guide.md) for details.

<div class="flow-arrow">&#9661;</div>

### Gene Annotation

Optional gene calling and feature annotation of assembled genomes (FASTA) using one of the following tools:

- **RepeatMasker + Liftoff** (viral)
    - Optimized for variola and mpox genomes. Combines [RepeatMasker](https://www.repeatmasker.org/) for annotating repeat motifs and [Liftoff](https://github.com/agshumate/Liftoff) for annotating functional regions.
    - Requires a reference genome (FASTA) and feature list (GFF3).

- **VADR** (viral)
    - Annotates genomes using a set of homologous reference models. TOSTADAS comes packaged with support for monkeypox virus, RSV, and measles.
    - A full list of supported pathogens is available from the [VADR GitHub Repository](https://github.com/ncbi/vadr).

- **Bakta** (bacterial)
    - Annotates bacterial genomes and plasmids using [Bakta](https://github.com/oschwengers/bakta).
    - Requires a reference database ([found here](https://zenodo.org/records/10522951)), which can be downloaded at runtime.

All annotation options produce a general feature format file (GFF) and NCBI feature table (TBL) compatible with downstream NCBI submission requirements.

<div class="flow-arrow">&#9661;</div>

### Submission

Prepares necessary submission files for BioSample, SRA, and/or GenBank depending on the provided inputs and performs optional upload to NCBI via FTP. This workflow was adapted from the [SeqSender](https://github.com/CDCgov/seqsender) public database submission pipeline.
