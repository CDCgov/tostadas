# VADR Installation Guide

VADR (Viral Annotation DefineR) is used by TOSTADAS to annotate mpox and RSV sequences. When using the `singularity` or `docker` profile, VADR is included in the container — you don't need to install it manually.

Use this guide only if you're running TOSTADAS with the `conda` profile or need a standalone VADR installation.

---

## Prerequisites

- Linux or macOS
- mamba or conda
- Perl 5.x

---

## Step 1 — Clone VADR

From the TOSTADAS root directory:

```bash
git clone https://github.com/ncbi/vadr.git
cd vadr
VADRINSTALLDIR=$PWD
```

## Step 2 — Run the install script

```bash
# Install curl if needed
mamba install -c conda-forge curl

# Linux
bash vadr-install.sh linux

# macOS
bash vadr-install.sh macosx
```

**If you see `autoconf: command not found`:**

```bash
# Ubuntu/Debian
sudo apt-get install autoconf

# macOS
brew install autoconf
```

## Step 3 — Install Perl dependencies

Test your install first: `perl vadr/v-annotate.pl`

If it fails with missing packages, install them:

```bash
# Bio/Easel
perl vadr/Bio-Easel/Makefile.PL
cd vadr/Bio-Easel
make
sudo make install   # sudo only if you get a permissions error

# LWP
cpan install LWP
```

If you see errors about `sqp_opts.pm`, copy the sequip files to your Perl path (shown in the `@INC` error):

```bash
cp sequip/* /your/perl/path/
```

## Step 4 — Set up virus models

### Mpox models

```bash
curl https://ftp.ncbi.nlm.nih.gov/pub/nawrocki/vadr-models/mpxv/1.4.2-1/vadr-models-mpxv-1.4.2-1.tar.gz \
  --output mpxv-models.tar.gz
tar -xf mpxv-models.tar.gz && mv vadr-models-mpxv-* mpxv-models

# Copy the modified model file with ITRs
cp ../vadr_files/mpxv.rpt.minfo mpxv-models/
```

### RSV models

```bash
curl https://ftp.ncbi.nlm.nih.gov/pub/nawrocki/vadr-models/rsv/1.5-2/vadr-models-rsv-1.5-2.tar.gz \
  --output rsv-models.tar.gz
tar -xf rsv-models.tar.gz && mv vadr-models-rsv-* rsv-models
```

## Step 5 — Export paths

```bash
cd .. && . vadr_files/env_variables.sh
```

Add this to your `.bashrc` or `.zshrc` to make it permanent.

## Step 6 — Configure TOSTADAS

Point TOSTADAS to your model directory:

```bash
# Mpox
nextflow run main.nf -profile singularity,mpox --vadr_models_dir /path/to/mpxv-models ...

# RSV
nextflow run main.nf -profile singularity,rsv --vadr_models_dir /path/to/rsv-models ...
```

Or set `vadr_models_dir` in `nextflow.config`.

---

## Verify the install

```bash
perl vadr/v-annotate.pl --split --cpu 8 --glsearch --minimap2 -s -r --nomisc \
  --r_lowsimok --r_lowsimxd 100 --r_lowsimxl 2000 --alt_pass discontn,dupregin \
  --s_overhang 150 \
  -i vadr/mpxv-models/mpxv.rpt.minfo \
  -n vadr/mpxv-models/mpxv.fa \
  -x $MDIR \
  test_input.fasta \
  vadr_test_output -f
```

Check `vadr_test_output/*.vadr.pass.list` and `*.vadr.fail.list` for results.
