# Home

## Overview
TOSTADAS is designed to fulfill common sequence submission use cases. The tool runs three sub-processes:

Metadata Validation – This workflow checks if metadata conforms to NCBI standards and matches the input .fasta file(s)
Gene Annotation – This workflow runs gene annotation on fasta-formatted genomes using one of three annotation methods: RepeatMasker and Liftoff, VADR or BAKTA
Submission – This workflow generates the necessary files and information for submission to NCBI and optionally and optionally submit to NCBI.
TOSTADAS is flexible, allowing you to choose which portions of the pipeline to run and which to skip. For example, you can submit .fastq files and metadata without performing gene annotation.

The current distribution has been tested with Pox virus sequences as well as some bacteria. Ongoing development aims to make the pipeline pathogen agnostic.

## Pipeline Summary
### Metadata Validation
The validation workflow checks that user provided metadata conforms to NCBI standards and matches the input data file(s). To allow for easy multi-sample submission, TOSTADAS can split a multi-sample Excel (.xlsx) file into separate tab delimited files (.tsv) for each individual sample.

TOSTADAS can accept custom metadata fields specific to a users' pathogen, sample type, or workflow. Additionally, TOSTADAS offers powerful validation tools for user- created fields, allowing users to specify which samples to apply rules to, replace empty values with user specified replacements, rename existing fields and other operations. These features can be enabled with the validate_custom_fields parameter. Custom fields can be specified using the custom_fields_file parameter.

A full guide to using custom metadata fields can be found here: [Custom Metadata Guide](https://github.com/CDCgov/tostadas/blob/457242fb15973f69cb3578367317a8b5e7c619f7/docs/custom_metadata_guide.md)

### Gene Annotation
TOSTADAS offers three optional annotation options:

#### RepeatMasker and Liftoff

The RepeatMasker and Liftoff workflow annotates fasta-formatted sequences based upon a provided reference and annotation file. This workflow was optimized for variola genome annotation and may require modification for other pathogens. This workflow runs RepeatMasker to annotate repeat motifs, followed by Liftoff to annotate functional regions. These results are combined into a single feature file (.gff3). The Liftoff annotation workflow requires a reference genome (.fasta), reference feature .gff, single sample .fasta files, and metadata in Excel .xlsx format. Be sure to specify the correct database in the params for this option.
[RepeatMasker and Liftoff Example](Link)

#### VADR

The VADR workflow annotates fasta-formatted viral genomes using RefSeq annotation from a set of homologous reference models. This workflow requires single sample fasta files, metadata in .xlsx format, and reference information for the pathogen genome. TOSTADAS comes packaged with support for [monkeypox (mpxv) annotation] (https://github.com/CDCgov/tostadas/tree/master/vadr_files/mpxv-models). You can find information on other supported pathogens at the [VADR GitHub Repository] (https://github.com/ncbi/vadr).
[VADR Example] (Link)

#### Bakta

The Bakta workflow annotates fasta-formatted bacterial genomes & plasmids using the Bakta software. This workflow requires single sample .fasta files, metadata in .xlsx format, and optional reference database for annotation (found here).
[BAKTA Example] (Link)

All annotation workflows produce a general feature format file (.gff3) and NCBI feature table (tbl) compatible with NCBI submission requirements.

## Submission
The TOSTADAS Submission workflow generates the necessary files for Genbank submission, a BioSample ID, then optionally uploads Fastq files via FTP to SRA. This workflow was adapted from SeqSender public database submission pipeline.
