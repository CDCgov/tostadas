# NCBI Databases Overview

TOSTADAS submits genomic data to three NCBI public repositories: BioSample, SRA, and GenBank. This page explains what each database is and how to set up an NCBI account for automated submission.

---

## NCBI Center Account

To use TOSTADAS's automated FTP submission, you need an **NCBI Center Account** — this is different from a personal NCBI login. If you're submitting on behalf of a lab, department, or public health program, one Center Account should serve your entire group.

**To create a Center Account,** email `sra@ncbi.nlm.nih.gov` with:

- Suggested center abbreviation (16 characters max)
- Center full name, URL, and mailing address
- Phone number
- Contact person name and email (ideally a monitored service account)
- Whether you'll submit via FTP or Aspera

NCBI will create a test area and a production area for you and send connection details by email. You'll use these credentials in your `submission_config.yaml`.

---

## Databases TOSTADAS supports

### BioSample

BioSample stores structured metadata about biological specimens. Every NCBI submission starts here — BioSample accessions (`SAMN########`) are required before you can submit to GenBank.

TOSTADAS handles BioSample submission via XML + FTP. The BioSample package (e.g., `Pathogen.cl.1.0`) determines which metadata fields are required.

- [BioSample documentation](https://www.ncbi.nlm.nih.gov/biosample/docs/)
- [Available BioSample packages](https://www.ncbi.nlm.nih.gov/biosample/docs/packages/)

### SRA (Sequence Read Archive)

SRA stores raw sequencing reads (FASTQ, BAM). TOSTADAS uploads your FASTQ files via FTP alongside an XML manifest.

Both Illumina and Nanopore data are supported. Mixed sequencing types are split into separate submission XMLs automatically.

- [SRA documentation](https://www.ncbi.nlm.nih.gov/sra/docs/)

### GenBank

GenBank stores assembled genome sequences with annotation. GenBank submission requires:
1. A BioSample accession (from a prior BioSample submission)
2. Annotated sequence files (FASTA + GFF/TBL, produced by TOSTADAS's annotation step)

TOSTADAS uses `table2asn` to produce ASN.1 submission files and uploads them via FTP (bacteria/eukaryotes) or email (viruses).

- [GenBank documentation](https://www.ncbi.nlm.nih.gov/genbank/)
- [GenBank submission formatting](https://www.ncbi.nlm.nih.gov/books/NBK566986/)

---

## Submission mechanics

| Database | Submission method | File format |
|---|---|---|
| BioSample | FTP | XML |
| SRA | FTP | XML + FASTQ |
| GenBank (bacteria/eukaryote) | FTP | ASN.1 (`.sqn`) from table2asn |
| GenBank (virus) | Email | ASN.1 (`.sqn`) from table2asn |

TOSTADAS deposits files into your NCBI submission directory, then polls for `report.xml` to retrieve accession IDs. The `--submission_wait_time` parameter (default: `calc` = 30s × batch_size) controls how long to wait before polling.

---

## SPUID — the key identifier

NCBI uses **SPUIDs** (Submitter Provided Unique Identifiers) to link records across databases. Your metadata file has two SPUID columns:
- `ncbi-spuid` — links BioSample records
- `ncbi-spuid-sra` — links SRA records to the corresponding BioSample

These must be unique per sample and consistent across submission and update runs. TOSTADAS uses them (not `sample_name`) when matching records for `update_submission`.

---

## BioProject

Before submitting samples, create a BioProject at [submit.ncbi.nlm.nih.gov](https://submit.ncbi.nlm.nih.gov/subs/bioproject/) to organize your submissions. Link related BioProjects to umbrella projects where applicable (e.g., NWSS wastewater: `PRJNA747181`).

Add your BioProject accession to your metadata file in the `bioproject_accession` column.
