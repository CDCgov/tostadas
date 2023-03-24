# VADR Install Guide for Biolinux
### **1. Clone the Repo**
```
git clone https://github.com/ncbi/vadr.git
cd vadr
VADRINSTALLDIR='.'
```
### **2. Run the Install Script, If Getting an Error with Curl, Install Curl Using Mamba**
`mamba install -c conda-forge curl`

Windows:
```
bash vadr-install.sh linux
```
Mac:
```
bash vadr-install.sh macosx
```
**Troubleshooting:**

If you receive the following error message:
```
vadr-install.sh: line 174: autoconf: command not found
```
Then, install autoconf using either of the following commands:

```
sudo apt-get install autoconf
```
OR
```
brew install autoconf
``` 

### 3. **Set Up the MPXV Model Directory**
```
curl https://ftp.ncbi.nlm.nih.gov/pub/nawrocki/vadr-models/mpxv/1.4.2-1/vadr-models-mpxv-1.4.2-1.tar.gz --output mpxv-models.tar.gz
tar -x mpxv-models.tar.gz
mv vadr-models-mpxv-* mpxv-models
```
You also need to copy the modified model file that includes the ITRs from our MPXV repo.
`cp ../mpxv_annotation_submission_dev/mpxv-models/mpxv.rpt.minfo mpxv-models`

### **4. Test and Troubleshoot the Install**

Test your install by running `perl v-annotate.pl`. 

It will probably fail with either (1) ```use: command not found``` or (2) ```Cant locate XYZ package in @INC```. 

If it works as expected, skip to #5 to export your variables.Else, you can now begin the process of troubleshooting by installing the required PERL libraries.

**To Install Bio/Easel/MSA.pl**
```
cd Bio-Easel/
perl Makefile.PL
make
make install
cd ..
```
** If ```make install``` throws a permission error, try running it as admin with ```sudo make install``` instead

**To Install LWP/Simple.pm**
```
cpan install LWP
```
If error about sqp_opts.pm copy the files in sequip to your Perl path, which is shown as the @INC 
`cp sequip/* <YOUR_PATH>`

### **5. Export PATHS**
Or add to your .bashrc profile

**(1) Change directories to env_variables.sh file location in tostadas/docs:**
```
cd <location to env_variables.sh>
```
**(2) Use env_variables.sh file to export path variables:**
```
bash env_variables.sh
```

### 6. Run the annotation script
Ideally you have as many threads as samples, since VADR will give one thread to each sample
```
perl v-annotate.pl --split --cpu 8 --glsearch --minimap2 -s -r --nomisc \
--r_lowsimok --r_lowsimxd 100 --r_lowsimxl 2000 --alt_pass \
discontn,dupregin --s_overhang 150 -i $MDIR/mpxv.rpt.minfo -n \
$MDIR/mpxv.fa -x $MDIR $INPUT_DIR/trialDatav5.fasta \
vadr_testing_outdir -f
```
