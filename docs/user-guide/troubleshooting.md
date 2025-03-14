# Troubleshooting

If you encounter issues while using the TOSTADAS pipeline, refer to the following troubleshooting steps to resolve common problems:

### Common Issues and Solutions

#### 1. Errors with 'table2asn not on PATH' or a Python library missing when using the `singularity` or `docker` profiles

**Issue:** Nextflow is using an outdated cached image.

**Solution:** Locate the image (e.g., `$HOME/.singularity/staphb-tostadas-latest.img`) and delete it. This will force Nextflow to pull the latest version.

#### 2. Pipeline hangs indefinitely during the submission step, or you get a "duplicate BioSeq ID error"  

**Issue:** This may be caused by duplicate sample IDs in the FASTA file (e.g., a multicontig FASTA). This is only a problem for submissions to Genbank using `table2asn`.

**Solution:** Review the sequence headers in the sample FASTA files and ensure that each header is unique.

## Get in Touch
If you need to report a bug, suggest new features, or just say “thanks”, [open an issue](https://github.com/CDCgov/tostadas/issues/new/choose) and we’ll try to get back to you as soon as possible!
