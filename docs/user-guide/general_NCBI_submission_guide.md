# NCBI Databases Overview

## Table of Contents
- [General](#general)
    - [What is NCBI](#what-is-ncbi)
    - [NCBI Center Account](#ncbi-center-account)
    - [Key Components of NCBI](#key-components-of-ncbi)
        - [PubMed](#1-pubmed)
        - [GenBank](#2-genbank)
        - [BLAST](#3-blast)
        - [Entrez](#4-entrez)
        - [SRA](#5-sra)
        - [BioProject / BioSample](#6-bioproject--biosample)
        - [ClinVar](#7-clinvar)
        - [dbSNP](#8-dbsnp)
- [More Information For Each Database](#more-information-for-each-database)

    

## General

TOSTADAS provides users with the ability to submit samples to various NCBI databases with ease. For many of the databases, the pipeline leverages FTP communication to submit samples in an automated manner. TOSTADAS creates many custom log files locally for the submission process and returns valuable information / documents created at the NCBI endpoint as well. Through frequent conversations with personnel from NCBI, TOSTADAS will be continuously updated with any improvments to existing submission mechanisms and/or the implementation of completely new ones from NCBI, in order to provide the best experience for our users.

### What is NCBI?

The National Center for Biotechnology Information (NCBI) is a division of the National Library of Medicine (NLM) at the National Institutes of Health (NIH). NCBI plays a crucial role in advancing bioinformatics, genomics, and computational biology. Its primary mission is to provide access to and facilitate the use of a vast array of biomedical and genomic information.

NCBI continues to evolve, offering a wide range of tools and resources to support researchers, healthcare professionals, and the broader scientific community in accessing and utilizing biological information.

### NCBI Center Account

To submit to NCBI using TOSTADAS, you first need to establish an account with NCBI. If you're submitting on behalf of a group (e.g., a CDC branch, or a state Public Health Lab), you will want to create one account for your center to use.
NCBI has information on how to create an account [here](https://www.nlm.nih.gov/ncbi/workshops/2023-06_organizing-biology-data/supplemental-files/NCBIAccountFlyer.pdf).  You may already have a personal NCBI account, but you should create a Center-level account.  You will need to configure the TOSTADAS submission config file with your NCBI account username and password to facilitate submissions via ftp.

### Key Components of NCBI:

#### 1. **PubMed:**
   - **Description:** PubMed is a comprehensive database of biomedical literature, containing articles, abstracts, and citations from various scientific journals.
   - **URL:** [PubMed](https://pubmed.ncbi.nlm.nih.gov/)

#### 2. **GenBank:**
   - **Description:** GenBank is a DNA sequence database that collects and archives genomic data from researchers worldwide. It plays a pivotal role in the sharing and dissemination of genetic information.
   - **URL:** [General GenBank Docs](https://www.ncbi.nlm.nih.gov/genbank/)
   - **URL2:** [Formatting for GenBank](https://www.ncbi.nlm.nih.gov/books/NBK566986/#qkstrt_Format_Sub.Source_Modifier_Table)

#### 3. **BLAST:**
   - **Description:** BLAST is a powerful tool for comparing biological sequences, allowing researchers to identify similarities between sequences and explore evolutionary relationships.
   - **URL:** [BLAST](https://blast.ncbi.nlm.nih.gov/Blast.cgi)

#### 4. **Entrez:**
   - **Description:** Entrez is an integrated search and retrieval system that provides access to various NCBI databases, including PubMed, GenBank, and others.
   - **URL:** [Entrez](https://www.ncbi.nlm.nih.gov/gquery/)

#### 5. **SRA:**
   - **Description:** SRA is a repository that archives and provides access to raw sequence data, including next-generation sequencing data, facilitating the exploration of genomic datasets.
   - **URL:** [SRA](https://www.ncbi.nlm.nih.gov/sra)

#### 6. **BioProject / BioSample:**
   - **Description:** BioProject and BioSample are databases that organize and store information about biological projects and samples, respectively, providing context for genomic data submissions.
   - **URL:** [BioProject](https://www.ncbi.nlm.nih.gov/bioproject/) / [BioSample](https://www.ncbi.nlm.nih.gov/biosample/)

#### 7. **ClinVar:**
   - **Description:** ClinVar is a resource that aggregates information about genomic variations and their clinical significance, aiding in the interpretation of genetic variants in a clinical context.
   - **URL:** [ClinVar](https://www.ncbi.nlm.nih.gov/clinvar/)

#### 8. **dbSNP:**
   - **Description:** dbSNP is a database that catalogs and classifies variations in the human genome, including single nucleotide polymorphisms (SNPs) and other genomic variations.
   - **URL:** [dbSNP](https://www.ncbi.nlm.nih.gov/snp/)

** **NOTE:** Current NCBI databases that are available through TOSTADAS are the following: 
* SRA
* GenBank
* BioSample

## More Information For Each Database

Each database under NCBI has different functions/use-cases, and therefore each requires a unique set of files, as well as formatting/content properties for each. 

It's important to note that the specific requirements for data submission to these databases can evolve, and it's recommended to refer to the latest guidelines provided by the National Center for Biotechnology Information (NCBI) or the respective databases for the most up-to-date information.


| **Database**                      | **Minimum Required Files**                                       | **Optional Files**                                              | **Required Metadata Fields**                                      | **Optional Metadata Fields**                            | **Current Submission Mechanisms**                                           |
|--------------------------------|--------------------------------------------------------------|-------------------------------------------------------------|-----------------------------------------------------------------|----------------------------------------------------|------------------------------------------------------------------------|
| **SRA (Sequence Read Archive)** | Raw sequence data files (e.g., FASTQ, BAM), XML metadata file                   | Quality control reports, Experimental design details                                      | Sample name, Organism                                                    | Yes (Strain, Sex, Developmental Stage, etc.)                 | Web-based submission portal, Command-line tools (e.g., `SRA Toolkit`), FTP |
| **GenBank**                     | Nucleotide or protein sequence file (FASTA format), Annotation file (GenBank format as a .tbl or .gff)           | Sequencing trace files, Supplementary data files                                         | Organism, Locus tag                                                        | Yes (Strain, Taxonomy ID, etc.)                               | BankIt submission tool, Sequin interactive submission tool, table2asn via FTP or email |
| **BioSample**                   | XML metadata file                                             | Additional sample attributes file                             | Sample name, Organism                                                     | Yes (Strain, Sex, etc.)                                       | Web-based submission portal, Submission through BioProject or other NCBI databases |
| **Joint BioSample/SRA**         | Raw sequence data files (e.g., FASTQ, BAM), XML metadata file (BioSample and SRA metadata combined)                   | Quality control reports, Experimental design details                                    | Sample name, Organism                                                    | Yes (Strain, Sex, Developmental Stage, etc.)                  | Web-based submission portal, Command-line tools (e.g., `SRA Toolkit`), FTP   










