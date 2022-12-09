#!/bin/bash

# define variables for nextflow 
WAIT_TIME=3 
OUTPUT_DIR="$PWD/mpxv_annotation_submission_dev/aspen_test_results"
# specify expected paths 
LO=$OUTPUT_DIR/liftoff_outputs
SO=$OUTPUT_DIR/submission_outputs
VO=$OUTPUT_DIR/validation_outputs

# set up some variables for the batch submission job
#$ -N nf_test
#$ -l h_rt=01:00:00
#$ -l mfree=128G

# make directory for runs
mkdir -p $PWD/mpxv_annotation_submission_dev/aspen/runs
if [ -e $PWD/mpxv_annotation_submission_dev/aspen/latest_run ]
then 
    rm -r $PWD/mpxv_annotation_submission_dev/aspen/latest_run
fi
mkdir $PWD/mpxv_annotation_submission_dev/aspen/latest_run

# get unique id for new run file 
NUM_FILES= ls -1 $PWD/mpxv_annotation_submission_dev/aspen/runs | wc -l
NUM_FILES=$((NUM_FILES))
DIV=$((NUM_FILES+1000000000))
RAND_NUM=$(($RANDOM%$DIV))

# print out which node nextflow is being run on 
printf "Running nextflow scripts on $(hostname)" > $PWD/mpxv_annotation_submission_dev/aspen/runs/submit_info_$RAND_NUM.txt

# activate the conda env 
source /apps/x86_64/miniconda3/etc/profile.d/conda.sh 
conda activate nextflow_testing


# run nextflow with the default params + through conda
nextflow run $PWD/mpxv_annotation_submission_dev/main.nf -profile test,conda --submission_wait_time $WAIT_TIME --scicomp true --output_dir $OUTPUT_DIR


if [[ -e $LO && -e $SO && -e $VO ]]
then 
    printf "\n\nSuccessfully ran default test parameters profile with conda: \
    \nnextflow run $PWD/mpxv_annotation_submission_dev/main.nf -profile test,run_singularity --submission_wait_time $WAIT_TIME --scicomp true --output_dir $OUTPUT_DIR" \
    >> $PWD/mpxv_annotation_submission_dev/aspen/runs/submit_info_$RAND_NUM.txt
fi

# run nextflow with default params + through singularity 
nextflow run $PWD/mpxv_annotation_submission_dev/main.nf -profile test,singularity --submission_wait_time $WAIT_TIME --scicomp true --output_dir $OUTPUT_DIR

if [[ -e $LO && -e $SO && -e $VO ]]
then
    printf "\n\nSuccessfully ran default test parameters profile with singularity: \
    \nnextflow run $PWD/mpxv_annotation_submission_dev/main.nf -profile test,run_singularity --submission_wait_time $WAIT_TIME --scicomp true --output_dir $OUTPUT_DIR" \
    >> $PWD/mpxv_annotation_submission_dev/aspen/runs/submit_info_$RAND_NUM.txt
fi

# move the .txt file containing submission info for this job to latest run 
cp $PWD/mpxv_annotation_submission_dev/aspen/runs/submit_info_$RAND_NUM.txt $PWD/mpxv_annotation_submission_dev/aspen/latest_run/submit_info_$RAND_NUM.txt

# remove the nextflow log files 
find $PWD -type f -name '*.nextflow.log' -exec rm -f {} +

# remove the test results
rm -r $OUTPUT_DIR