July 2022
vadr-models-mpxv-1.4-1

https://github.com/ncbi/vadr

Instructions for monkeypox virus (MPXV) annotation using VADR:
https://github.com/ncbi/vadr/wiki/monkeypox-annotation

VADR documentation:
https://github.com/ncbi/vadr/blob/master/README.md

See RELEASE-NOTES.txt for details on changes between model versions. 

------------

Recommended command for MPXV annotation using vadr v1.4.2 or later
(as of July 15, 2022, see
https://github.com/ncbi/vadr/wiki/Monkeypox-virus-annotation for
possibly more current recommendations):

v-annotate.pl \
--split --cpu 4 \
--glsearch \
-s -r --nomisc \
--mkey mpxv \
--r_lowsimok \
--r_lowsimxd 100 \
--r_lowsimxl 2000 \
--alt_pass discontn,dupregin \
--mdir <PATH-TO-THIS-MODEL-DIR> \
<fastafile> <outputdir>

The '--split --cpu 4' options will run v-annotate.pl multi-threaded on
4 threads. To change to '<n>' threads use '--split --cpu <n>', but
make sure you have <n> * 4G total RAM available. 

To run single threaded remove the '--split --cpu 4' options.

The '--r_lowsimok' option will allow sequences to 'pass' that would
have otherwise 'failed' due to LOW_SIMILARITY errors in N-rich regions
where the number of Ns does not exactly match the length of the
corresponding region in NC_063383. 

NOTE: using VADR for MPXV sequences is still relatively untested, and
the above recommended options are subject to change. Many 'good'
MPXV sequences without sequencing or assembly artifacts may 'fail'
v-annotate.pl using these options.

------------

Contact eric.nawrocki@nih.gov for help.
