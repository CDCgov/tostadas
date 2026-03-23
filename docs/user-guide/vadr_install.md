# VADR Install Guide for Biolinux

!!! note
    Manual VADR installation is only necessary if you are running the pipeline outside of a container. When using the Docker or Singularity profiles, the pipeline handles VADR model setup automatically through the `VADR_MODEL_SETUP` process, which downloads the covariance model file from the URL specified by `vadr_cm_url` if it is not already present. No manual steps are required in that case.

### 1. Clone the Repo

First, make sure that you are inside of the root directory of the tostadas repository, and then run the following:

```bash
git clone https://github.com/ncbi/vadr.git
cd vadr
VADRINSTALLDIR=$PWD
```

### 2. Run the Install Script, If Getting an Error with Curl, Install Curl Using Mamba

```bash
mamba install -c conda-forge curl
```

Windows:

```bash
bash vadr-install.sh linux
```

Mac:

```bash
bash vadr-install.sh macosx
```

**Troubleshooting:**

If you receive the following error message:

```text
vadr-install.sh: line 174: autoconf: command not found
```

Then, install autoconf using either of the following commands:

```bash
sudo apt-get install autoconf
```

OR

```bash
brew install autoconf
```

### 3. Set Up the MPXV Model Directory

```bash
curl https://ftp.ncbi.nlm.nih.gov/pub/nawrocki/vadr-models/mpxv/1.4.2-1/vadr-models-mpxv-1.4.2-1.tar.gz --output mpxv-models.tar.gz
tar -xf mpxv-models.tar.gz && mv vadr-models-mpxv-* mpxv-models
```

You also need to copy the modified model file that includes the ITRs from our MPXV repo.

```bash
cp ../vadr_files/mpxv.rpt.minfo mpxv-models/
```

### 4. Export PATHS

Or add to your .bashrc profile

**Use env_variables.sh file to export path variables:**

```bash
cd .. && . vadr_files/env_variables.sh
```

### 5. Test and Troubleshoot the Install

Test your install by running `perl vadr/v-annotate.pl`.

It will probably fail with either (1) `use: command not found` or (2) `Cant locate XYZ package in @INC`.

If it works as expected, skip to step 6 to export your variables. Else, you can now begin the process of troubleshooting by installing the required PERL libraries.

**To Install Bio/Easel/MSA.pl**

```bash
perl vadr/Bio-Easel/Makefile.PL
cd vadr/Bio-Easel
make
make install
```

!!! note
    If `make install` throws a permission error, try running it as admin with `sudo make install` instead.

**To Install LWP/Simple.pm**

```bash
cpan install LWP
```

If error about sqp_opts.pm copy the files in sequip to your Perl path, which is shown as the @INC:

```bash
cp sequip/* <YOUR_PATH>
```

### Set Up the Measles (MEV) Model Directory

The measles VADR model is sourced from [vadr-models-mev](https://github.com/greninger-lab/vadr-models-mev). When using the `measles` profile, the pipeline automatically downloads the model via the `vadr_cm_url` parameter defined in `conf/measles.config`. The model files are placed in `vadr_files/mev-models/`.

To download the model manually:

```bash
cd vadr_files
git clone https://github.com/greninger-lab/vadr-models-mev.git mev-models
```

### 6. Run the annotation script

Ideally you have as many threads as samples, since VADR will give one thread to each sample:

```bash
perl vadr/v-annotate.pl --split --cpu 8 --glsearch --minimap2 -s -r --nomisc \
--r_lowsimok --r_lowsimxd 100 --r_lowsimxl 2000 --alt_pass \
discontn,dupregin --s_overhang 150 -i vadr/mpxv-models/mpxv.rpt.minfo -n \
vadr/mpxv-models/mpxv.fa -x $MDIR input_files/trialDatav5.fasta \
vadr_testing_outdir -f
```
