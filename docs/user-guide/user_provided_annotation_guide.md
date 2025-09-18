# User Provided Annotation Guide

## Table of Contents
- [Introduction](#introduction)
 - [Using Table2asn (GenBank)](#using-table2asn-genbank)
    - [Gene Annotation Formatting](#gene-annotation-formatting)

## Introduction

GenBank is the database primarily associated with genome annotations. The minimum required files for GenBank include a nucleotide or protein sequence file (FASTA format) and an annotation file (GenBank format). The annotation file typically contains information about features such as genes, coding regions, and other elements in the sequence.

On the other hand, databases like SRA (Sequence Read Archive), BioSample, and Joint BioSample/SRA primarily deal with raw sequence data, metadata about samples, and experimental details. They do not necessarily require genome annotation files.

General information about annotation examples can be found [here](https://www.ncbi.nlm.nih.gov/WebSub/html/annot_examples.html). This documentation provided by NCBI gives information on relevant features based on your sequence/gene type (mRNA, Prokaryote, Eukaryote, Viral, etc.), genomic elements, and types of database submissions that NCBI expects.

## Using Table2asn (GenBank)

A popular method for GenBank submission is to use [table2asn](https://www.ncbi.nlm.nih.gov/genbank/table2asn/). 

Table2asn is a command-line program that creates sequence records for submission to GenBank (.sqn file for every .fsa file). This tool outputs an ASN.1 (Abstract Syntax Notation 1) text file with the same basename and a .sqn suffix as well. 

Required inputs into table2asn are the following (click the name to view required formatting/general information for each input file): 
* [Template File](https://www.ncbi.nlm.nih.gov/genbank/table2asn/#Template) (.sbt)
    * TOSTADAS handles the creation of this based on your metadata information and contents within your submission config file 
* [FASTA File](https://www.ncbi.nlm.nih.gov/books/NBK566986/#qkstrt_Format_Sub.FASTA_Formatting) (.fasta)
* [Genome Annotation File](https://www.ncbi.nlm.nih.gov/books/NBK566986/#qkstrt_Format_Sub.Source_Modifier_Table) (.gff or .tbl)
    * Please note that either a .gff formatted file (GenBank prokaryotic or eukaryotic genomes can use GFF3 files in a GenBank-specific format) or a .tbl formatted file can be used for your annotations
    * Each of these annotation files need to have the same name prefix as its corresponding .fasta file (i.e. helicase.fsa and helicase.tbl) (i.e. helicase.fsa and helicase.gff)

### Gene Annotation Formatting 

In order to successfully submit samples to GenBank using table2asn, specific requirements for formatting and content must be followed. 

The requirements for GFF3 annotation files can be found [here](https://www.ncbi.nlm.nih.gov/genbank/genomes_gff/).









