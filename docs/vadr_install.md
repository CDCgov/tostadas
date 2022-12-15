# VADR Install Guide for Biolinux
### 1. Clone the repo
```
git clone https://github.com/ncbi/vadr.git
cd vadr
VADRINSTALLDIR='.'
```
### 2. Run the install script, if getting an error with curl, install curl using mamba
`mamba install -c conda-forge curl`
```
vadr-install.sh linux
```

### 3. Set up the MPXV model directory. 
```
curl https://ftp.ncbi.nlm.nih.gov/pub/nawrocki/vadr-models/mpxv/1.4.2-1/vadr-models-mpxv-1.4.2-1.tar.gz --output mpxv-models.tar.gz
tar -xf mpxv-models.tar.gz
mv vadr-models-mpxv-* mpxv-models
```
You also need to copy the modified model file that includes the ITRs from our MPXV repo.
`cp ../mpxv_annotation_submission_dev/mpxv-models/mpxv.rpt.minfo mpxv-models`

### 4. Test and troubleshoot the install

Test your install by running `v-annotate.pl`. It will probably fail with a message something like 'Cant locate XYZ package in @INC'. You now begin the process of troubleshooting by installing the required perl libraries.
If it works as expected, skip to #5 to export your variables.

To install Bio/Easel/MSA.pl
```
cd Bio-Easel/
perl Makefile.PL
make
make install
cd ..
```
To install LWP/Simple.pm
```
cpan install LWP
```
If error about sqp_opts.pm copy the files in sequip to your Perl path, which is shown as the @INC 
`cp sequip/* <YOUR_PATH>`

### 5. Export PATHS
Or add to your .bashrc profile
```
export VADRINSTALLDIR="."
export VADRSCRIPTSDIR="$VADRINSTALLDIR/vadr"
export VADRMODELDIR="$VADRINSTALLDIR/vadr-models-calici"
export VADRINFERNALDIR="$VADRINSTALLDIR/infernal/binaries"
export VADREASELDIR="$VADRINSTALLDIR/infernal/binaries"
export VADRHMMERDIR="$VADRINSTALLDIR/hmmer/binaries"
export VADRBIOEASELDIR="$VADRINSTALLDIR/Bio-Easel"
export VADRSEQUIPDIR="$VADRINSTALLDIR/sequip"
export VADRBLASTDIR="$VADRINSTALLDIR/ncbi-blast/bin"
export VADRFASTADIR="$VADRINSTALLDIR/fasta/bin"
export PERL5LIB="$VADRSCRIPTSDIR":"$VADRSEQUIPDIR":"$VADRBIOEASELDIR/blib/lib":"$VAR 
BIOEASELDIR/blib/arch":"$PERL5LIB"
export PATH="$VADRSCRIPTSDIR":"$PATH"
export VADRMINIMAP2DIR="$VADRINSTALLDIR/minimap2"
export MDIR='../mpxv_annotation_submission_dev/mpxv-models'
export INPUT_DIR='../mpxv_annotation_submission_dev/input_files/'
```

### 6. Run the annotation script
Ideally you have as many threads as samples, since VADR will give one thread to each sample
```
v-annotate.pl --split --cpu 8 --glsearch --minimap2 -s -r --nomisc \
--r_lowsimok --r_lowsimxd 100 --r_lowsimxl 2000 --alt_pass \
discontn,dupregin --s_overhang 150 -i $MDIR/mpxv.rpt.minfo -n \
$MDIR/mpxv.fa -x $MDIR $INPUT_DIR/trialDatav5.fasta \
vadr_testing_outdir -f
```
