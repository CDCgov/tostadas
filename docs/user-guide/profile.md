# Profiles

Profiles are `-profile` shortcuts that pre-configure TOSTADAS for specific use cases. Stack them with commas — the last profile wins if settings conflict.

```bash
-profile test,mpox,singularity
```

---

## Container runtime profiles (required — pick one)

| Profile | Description |
|---|---|
| `singularity` | Singularity/Apptainer containers — recommended for HPC environments |
| `docker` | Docker containers — recommended for local/cloud workstations |
| `conda` | conda/mamba environment — fallback when containers aren't available |

Containers are more reproducible and faster to start than conda. Use conda only when Docker/Singularity aren't available.

---

## Organism / program profiles (optional)

| Profile | BioSample package | Annotator | Notes |
|---|---|---|---|
| `mpox` | Pathogen.cl.1.0 | RepeatMasker + Liftoff | Mpox (MPXV) and variola |
| `rsv` | Pathogen.cl.1.0 | VADR | RSV A/B |
| `bacteria` | Pathogen.cl.1.0 | Bakta | Bacterial genomes |
| `virus` | Pathogen.cl.1.0 | RepeatMasker + Liftoff | Generic virus — use when no specific profile fits |
| `nwss` | SARS-CoV-2.wwsurv.1.0 | — | SARS-CoV-2 wastewater surveillance (NWSS program) |
| `pulsenet` | OneHealthEnteric.1.0 | — | Enteric pathogens (PulseNet / One Health) |

These profiles set `organism_type`, `virus_subtype`, `biosample_pkg`, and annotation flags. You can override any individual parameter on the command line.

---

## Test profile

```bash
-profile test,mpox,singularity
```

The `test` profile:
- Uses bundled test data (mpox sequences + metadata in `assets/`)
- Sets `dry_run true` by default — prepares submission files but does not upload
- Does not require a real submission config

To actually submit to the NCBI **test server** (not production), add `--dry_run false`:

```bash
nextflow run main.nf -profile test,mpox,singularity --dry_run false --submission_config conf/my_config.yaml
```

---

## Cloud profiles

### AWS

```bash
-profile aws
```

Configure `accessKey`, `secretKey`, and `endpoint` in `nextflow.config` under the `aws` profile block before use.

### Azure

```bash
-profile azure
```

Configure `accountName` and `accountKey` in `nextflow.config` under the `azure` profile block.

For both cloud profiles, use Nextflow Secrets to store credentials rather than hardcoding them in config:

```bash
nextflow secrets set AWS_ACCESS_KEY your-key
```

---

## Input files required per workflow

### BioSample + SRA submission

| File | Format | Notes |
|---|---|---|
| Metadata | `.xlsx` | Use the appropriate template from `assets/sample_metadata/` |
| FASTQ reads | `.fastq` / `.fastq.gz` | One file (SE) or two files (PE) per sample |
| Submission config | `.yaml` | Credentials and org info |

### GenBank submission (with annotation)

| File | Format | Notes |
|---|---|---|
| Metadata | `.xlsx` | Must include `biosample_accession` column |
| FASTA sequences | `.fasta` | One file per sample |
| Reference FASTA | `.fasta` | Used by Liftoff for annotation transfer |
| Reference GFF | `.gff` | Used by Liftoff for annotation transfer |
| Submission config | `.yaml` | — |

**Note:** File names cannot contain periods (`.`) except for the extension.

---

## Building your own profile

Add a profile in `conf/` and reference it in `nextflow.config`:

```groovy
// conf/mypathogen.config
params {
    organism_type    = 'virus'
    virus_subtype    = 'mypathogen'
    biosample_pkg    = 'Pathogen.cl.1.0'
    repeatmasker_liftoff = true
    vadr             = false
}
```

```groovy
// nextflow.config — add to profiles block
mypathogen { includeConfig 'conf/mypathogen.config' }
```

Then use `-profile mypathogen,singularity`.
