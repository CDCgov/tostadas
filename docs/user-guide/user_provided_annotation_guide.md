# User-Provided Annotation Guide

If you have already-annotated genomes, you can skip TOSTADAS's built-in annotation steps and provide your own GFF or TBL files directly for GenBank submission.

---

## When to use this

- You have annotation files from a previous pipeline run or external tool
- Your pathogen isn't supported by RepeatMasker/Liftoff, VADR, or Bakta
- You're re-submitting previously annotated sequences

---

## Required files

GenBank submission via `table2asn` requires three files per sample, all sharing the same basename:

| File | Extension | Description |
|---|---|---|
| Sequence | `.fasta` | Assembled genome sequence |
| Annotation | `.gff` or `.tbl` | Feature annotations |
| Template | `.sbt` | Submitter info (TOSTADAS generates this from your submission config) |

TOSTADAS generates the `.sbt` template automatically. You supply the `.fasta` and annotation files.

**Naming requirement:** The FASTA and annotation files must share the same prefix. For example:
- `sample001.fasta` + `sample001.tbl`
- `sample001.fasta` + `sample001.gff`

---

## Annotation file formats

### GFF3

Use NCBI's GenBank-specific GFF3 format. Requirements:
- `##gff-version 3` header
- Features anchored to the sequence IDs in your FASTA
- CDS features must have `protein_id` or `locus_tag` attributes

Full GFF3 spec for GenBank: [NCBI GFF3 documentation](https://www.ncbi.nlm.nih.gov/genbank/genomes_gff/)

### Feature Table (.tbl)

The `.tbl` format is a flat text format used by `table2asn`. It lists coordinates and qualifiers for each feature.

Feature table examples: [NCBI annotation examples](https://www.ncbi.nlm.nih.gov/WebSub/html/annot_examples.html)

---

## table2asn

TOSTADAS uses `table2asn` internally to convert FASTA + annotation files into NCBI ASN.1 (`.sqn`) format for submission. You don't need to run it manually — TOSTADAS handles it in the GenBank submission step.

If you want to test your annotation files locally before running the pipeline:

```bash
table2asn -i sample001.fasta -f sample001.tbl -t template.sbt -o sample001.sqn
```

Check the resulting `.sqn` and `.val` files for validation errors before running the full submission pipeline.

---

## Running with your own annotation files

Set `--annotation false` to skip TOSTADAS's annotation steps and point directly to your pre-annotated files. The pipeline expects them in a flat directory:

```bash
nextflow run main.nf \
  -profile singularity \
  --workflow genbank \
  --annotation false \
  --meta_path path/to/metadata.xlsx \
  --submission_config conf/my_config.yaml
```

Make sure the FASTA files referenced in your metadata match the annotation files in the same directory, sharing the same basename prefix.

---

## Additional NCBI resources

- [GenBank submission overview](https://www.ncbi.nlm.nih.gov/genbank/)
- [table2asn documentation](https://www.ncbi.nlm.nih.gov/genbank/table2asn/)
- [Annotation examples by organism type](https://www.ncbi.nlm.nih.gov/WebSub/html/annot_examples.html)
- [Source modifier table formatting](https://www.ncbi.nlm.nih.gov/books/NBK566986/)
