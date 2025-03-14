# Home

## Overview

### T O S T A D A S

Toolkit for Open Sequence Triage, Annotation, and DAtabase Submission

A portable, open-source pipeline designed to streamline submission of pathogen genomic data to public repositories. Reducing barriers to timely data submission increases the value of public repositories for both public health decision making and scientific research. TOSTADAS facilitates routine sequence submission by standardizing:

*   Metadata Validation
*   Genome Annotation
*   File submission The current release is tested with sequence data from Poxviruses and select bacteria but TOSTADAS is designed to be flexible, modular, and pathogen agnostic, allowing users to customize their submission of raw read data, assembled genomes, or both.

## Pipeline Summary

### (1) Metadata Validation

Verifies that user-provided metadata conforms to NCBI standards and match the sequence data file(s), all of which are organized in an Excel spreadsheet ([example file](https://github.com/CDCgov/tostadas/blob/dev/assets/metadata_template.xlsx)). By default, TOSTADAS uses a set of metadata fields appropriate for most pathogen genomic data submissions, but can be configured to accommodate custom metadata fields specific to any use case. A full guide to using custom metadata fields can be found here: [Custom Metadata Guide](https://github.com/CDCgov/tostadas/blob/457242fb15973f69cb3578367317a8b5e7c619f7/docs/custom_metadata_guide.md)

### (2) Gene Annotation

Optional gene calling and feature annotation of assembled genomes (FASTA) using one of the following:

(1) RepeatMasker + Liftoff (viral)

*   Optimized for variola and mpox genomes, this workflow combines [RepeatMasker](https://www.repeatmasker.org/) for annotating repeat motifs and [Liftoff](https://github.com/agshumate/Liftoff) to annotate functional regions. Execution requires a reference genome (FASTA) and feature list (GFF3) definition. Modifications likely necessary for use with other pathogens.

(2) VADR (viral)

*   Annotates genomes using a set of homologous reference models. TOSTADAS comes packaged with support for [monkeypox virus](https://github.com/CDCgov/tostadas/tree/master/vadr_files/mpxv-models) and a full list of supported pathogens is available from [VADR GitHub Repository](https://github.com/ncbi/vadr).

(3) Bakta (bacterial)

*   Annotates bacterial genomes and plasmids using [Bakta](https://github.com/CDCgov/tostadas/tree/master#gene-annotation). Execution requires a reference database ([found here](https://zenodo.org/records/10522951)), which can be downloaded at runtime. All annotation options produce a general feature format file (GFF) and NCBI feature table (TBL) compatible with downstream NCBI submission requirements.

### (3) Submission

Prepare necessary submission files for BioSample, SRA, and/or GenBank depending on the provided inputs and perform optional upload to NCBI via ftp. This workflow was adapted from the [SeqSender](https://github.com/CDCgov/seqsender) public database submission pipeline.
