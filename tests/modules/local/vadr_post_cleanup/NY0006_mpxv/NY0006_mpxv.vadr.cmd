mkdir NY0006_mpxv
/opt/vadr/infernal/binaries/esl-reformat fasta NY0006.trimmed.fasta > NY0006_mpxv/NY0006_mpxv.vadr.in.fa
/opt/vadr/infernal/binaries/esl-seqstat --dna -a NY0006_mpxv/NY0006_mpxv.vadr.in.fa > NY0006_mpxv/NY0006_mpxv.vadr.seqstat
sh NY0006_mpxv/NY0006_mpxv.annotate.1.sh > /dev/null 2> NY0006_mpxv/NY0006_mpxv.annotate.1.sh.err

cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.cmd > NY0006_mpxv/NY0006_mpxv.vadr.cmd.chunk
rm  NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.cmd
mkdir NY0006_mpxv/NY0006_mpxv.1
/opt/vadr/infernal/binaries/esl-reformat fasta NY0006_mpxv/NY0006_mpxv.vadr.in.fa > NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.in.fa
/opt/vadr/infernal/binaries/esl-seqstat --dna -a NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.in.fa > NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.seqstat
/opt/vadr/ncbi-blast/bin/blastn -num_threads 1 -query NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.blastn.fa -db mpxv-models/mpxv.fa -out NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cls.blastn.out -word_size 7 -reward 1 -penalty -2 -xdrop_gap_final 110 -gapopen 2 -gapextend 1
/opt/vadr/vadr/parse_blast.pl --program n --input NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cls.blastn.out --splus > NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cls.blastn.summary.txt
grep -v ^# NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cls.tblout | sed 's/  */ /g' | sort -k 1,1 -k 3,3rn > NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cls.tblout.sort
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cdt.NC_063383.tblout | grep -v ^# | sed 's/  */ /g' | sort -k 1,1 -k 15,15rn -k 16,16g > NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cdt.tblout.sort
/opt/vadr/ncbi-blast/bin/blastn -num_threads 1 -query NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.blastn.fa -db mpxv-models/mpxv.fa -out NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cls.blastn.out -word_size 7 -reward 1 -penalty -2 -xdrop_gap_final 110 -gapopen 2 -gapextend 1
/opt/vadr/vadr/parse_blast.pl --program n --input NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cls.blastn.out --splus > NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cls.blastn.summary.txt
grep -v ^# NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cls.tblout | sed 's/  */ /g' | sort -k 1,1 -k 3,3rn > NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cls.tblout.sort
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cdt.NC_063383.tblout | grep -v ^# | sed 's/  */ /g' | sort -k 1,1 -k 15,15rn -k 16,16g > NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cdt.tblout.sort
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.a.fa | /opt/vadr/minimap2/minimap2 -a  -rmq=no --junc-bonus=0 --for-only --sam-hit-only --secondary=no --score-N=0 -t 1 -x asm20 NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.minimap2.fa - -o NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.mm2.NC_063383.out 2> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.mm2.NC_063383.err
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.1.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.2.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.3.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.4.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.5.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.6.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.7.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.8.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.9.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.10.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.11.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.12.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.13.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.14.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.15.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.16.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.17.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.18.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.19.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.20.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.21.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.22.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.23.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.24.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.25.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.26.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.27.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.28.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.29.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.30.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.31.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.32.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.33.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.34.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.35.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.36.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.37.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.38.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.39.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.40.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.41.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.42.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.43.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.44.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.45.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.46.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.47.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.48.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.49.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.50.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.51.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.52.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.53.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.54.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.55.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.56.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.57.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.58.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.59.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.60.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.61.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.62.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.63.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.64.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.65.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.66.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.67.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.68.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.69.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.70.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.71.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.72.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.73.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.74.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.75.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.76.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.77.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.78.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.79.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.80.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.81.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.82.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.83.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.84.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.85.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.86.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.87.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.88.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.89.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.90.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.91.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.92.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.93.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.94.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.95.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.96.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.97.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.98.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.99.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.100.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.101.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.102.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.103.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.104.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.105.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.106.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.107.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.108.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.109.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.110.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.111.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.112.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.113.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.114.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.115.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.116.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.117.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.118.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.119.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.120.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.121.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.122.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.123.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.124.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.125.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.126.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.127.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.128.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.129.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.130.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.131.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.132.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.133.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.134.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.135.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.136.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.137.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.138.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.139.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.140.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.141.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.142.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.143.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.144.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.145.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.146.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.147.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.148.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.149.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.150.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.151.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.152.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.153.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.154.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.155.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.156.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.157.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.158.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.159.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.160.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.161.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.162.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.163.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.164.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.165.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.166.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.167.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.168.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.169.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.170.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.171.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.172.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.173.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.174.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.175.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.176.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.177.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.178.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.179.fa >> NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa
/opt/vadr/ncbi-blast/bin/blastx -num_threads 1 -num_alignments 20 -query NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa -db mpxv-models/NC_063383.vadr.protein.fa -seg no -out NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.blastx.out
/opt/vadr/vadr/parse_blast.pl --program x --input NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.blastx.out > NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.blastx.summary.txt
rm  NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.in.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.in.fa.ssi NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.blastn.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cls.blastn.out NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cls.blastn.summary.txt NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cls.blastn.pretblout NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cls.tblout NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cls.tblout.sort NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cdt.NC_063383.tblout NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cdt.NC_063383.indel NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.cdt.tblout.sort NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.rpn.sub.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cls.blastn.out NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cls.blastn.summary.txt NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cls.blastn.pretblout NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cls.tblout NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cls.tblout.sort NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cdt.NC_063383.tblout NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cdt.NC_063383.indel NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.std.cdt.tblout.sort NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.glsearch.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.minimap2.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.a.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.jalign.ifile NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.1.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.2.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.3.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.4.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.5.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.6.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.7.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.8.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.9.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.10.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.11.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.12.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.13.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.14.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.15.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.16.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.17.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.18.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.19.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.20.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.21.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.22.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.23.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.24.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.25.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.26.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.27.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.28.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.29.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.30.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.31.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.32.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.33.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.34.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.35.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.36.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.37.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.38.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.39.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.40.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.41.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.42.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.43.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.44.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.45.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.46.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.47.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.48.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.49.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.50.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.51.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.52.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.53.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.54.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.55.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.56.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.57.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.58.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.59.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.60.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.61.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.62.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.63.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.64.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.65.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.66.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.67.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.68.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.69.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.70.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.71.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.72.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.73.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.74.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.75.fa
rm  NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.76.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.77.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.78.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.79.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.80.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.81.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.82.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.83.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.84.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.85.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.86.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.87.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.88.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.89.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.90.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.91.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.92.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.93.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.94.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.95.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.96.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.97.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.98.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.99.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.100.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.101.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.102.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.103.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.104.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.105.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.106.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.107.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.108.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.109.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.110.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.111.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.112.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.113.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.114.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.115.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.116.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.117.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.118.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.119.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.120.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.121.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.122.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.123.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.124.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.125.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.126.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.127.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.128.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.129.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.130.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.131.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.132.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.133.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.134.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.135.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.136.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.137.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.138.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.139.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.140.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.141.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.142.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.143.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.144.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.145.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.146.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.147.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.148.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.149.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.150.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.151.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.152.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.153.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.154.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.155.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.156.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.157.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.158.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.159.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.160.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.161.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.162.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.163.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.164.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.165.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.166.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.167.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.168.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.169.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.170.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.171.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.172.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.173.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.174.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.175.fa
rm  NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.176.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.177.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.178.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.CDS.179.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.align.r3.s0.stk NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.pv.blastx.fa NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.blastx.out NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.NC_063383.blastx.summary.txt
# Mon Jun 23 17:30:51 EDT 2025
# Linux nettie 4.18.0-553.54.1.el8_10.x86_64 #1 SMP Sat May 17 16:41:33 EDT 2025 x86_64 x86_64 x86_64 GNU/Linux
[ok]
cat NY0006_mpxv/NY0006_mpxv.vadr.cmd.chunk
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.pass.tbl > NY0006_mpxv/NY0006_mpxv.vadr.pass.tbl
rm  NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.pass.tbl
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.fail.tbl > NY0006_mpxv/NY0006_mpxv.vadr.fail.tbl
rm  NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.fail.tbl
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.pass.list > NY0006_mpxv/NY0006_mpxv.vadr.pass.list
rm  NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.pass.list
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.fail.list > NY0006_mpxv/NY0006_mpxv.vadr.fail.list
rm  NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.fail.list
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.alt.list > NY0006_mpxv/NY0006_mpxv.vadr.alt.list
rm  NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.alt.list
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.pass.fa > NY0006_mpxv/NY0006_mpxv.vadr.pass.fa
rm  NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.pass.fa
cat NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.fail.fa > NY0006_mpxv/NY0006_mpxv.vadr.fail.fa
rm  NY0006_mpxv/NY0006_mpxv.1/NY0006_mpxv.1.vadr.fail.fa
rm  NY0006_mpxv/NY0006_mpxv.vadr.in.fa NY0006_mpxv/NY0006_mpxv.vadr.blastn.fa NY0006_mpxv/NY0006_mpxv.1.out NY0006_mpxv/NY0006_mpxv.annotate.1.sh NY0006_mpxv/NY0006_mpxv.annotate.1.sh.err NY0006_mpxv/NY0006_mpxv.vadr.cmd.chunk
rm NY0006_mpxv/NY0006_mpxv.1/*
rmdir NY0006_mpxv/NY0006_mpxv.1
# Mon Jun 23 17:30:52 EDT 2025
# Linux nettie 4.18.0-553.54.1.el8_10.x86_64 #1 SMP Sat May 17 16:41:33 EDT 2025 x86_64 x86_64 x86_64 GNU/Linux
[ok]
