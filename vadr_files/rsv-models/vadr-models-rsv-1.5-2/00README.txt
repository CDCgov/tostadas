January 2023
vadr-models-rsv-1.5-2

https://github.com/ncbi/vadr

VADR documentation:
https://github.com/ncbi/vadr/blob/master/README.md

See RELEASE-NOTES.txt for details on changes between model versions. 

------------

Recommended command for RSV annotation using vadr v1.3 or later
(as of January 31, 2023) but still under testing and subject to 
change.

v-annotate.pl \
--split --cpu 4 \
-r --mkey rsv \
--xnocomp \
--mdir <PATH-TO-THIS-MODEL-DIR> \
<fastafile> <outputdir>

The '--split --cpu 4' options will run v-annotate.pl multi-threaded on
4 threads. To change to '<n>' threads use '--split --cpu <n>', but
make sure you have <n> * 32G total RAM available. 

To run single threaded remove the '--split --cpu 4' options.

NOTE: using VADR for RSV sequences is still being tested, and
the above recommended options are subject to change.

------------

Explanation of selected files in this dir:

A.8.stk: alignment of 8 RSV A genomes, tested as a possible training
         alignment for an RSV A CM, but it performed slightly worse
         than the existing RSV A CM (built from KY654518.2.stk which
         as 2 sequences KY654518, and a modified version of KY654518
         with a common deletion), in that a few more 'bad' sequences
         that should have failed passed.

A.8.cm.gz: gzipped CM built from A.8.stk

B.14.stk: alignment of 14 RSV B genomes, tested as a possible training
          alignment for an RSV B CM, but it performed slightly worse
          than the existing RSV B CM (built from MZ516105.2.stk which
          has 2 sequences MZ516105, and a modified version of MZ516105
          with a common deletion), in that a few more 'bad' sequences
          that should have failed passed.

B.14.cm.gz: gzipped CM built from B.14.stk.

KY654518.2.stk: training alignment used to build the RSV A CM in
                rsv.cm. Includes 2 sequences KY654518.1 and KY654518.1
                with a deletion of length 72 starting at position
                5496, which is a commonly deleted region in RSV A.

MZ516105.2.stk: training alignment used to build the RSV B CM in
                rsv.cm. Includes 2 sequences MZ516105.1 and MZ516105.1
                with a deletion of length 60 starting at position
                5441, which is a commonly deleted region in RSV B.

--

Contact eric.nawrocki@nih.gov for help.
