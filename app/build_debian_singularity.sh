# !/bin/bash

# create the output directory if it does not exist 
output_dir=$PWD/singularity/containers
mkdir -p $output_dir

# copy the environment yml file to same directory 
ENV_YML=../environment.yml
cp $ENV_YML $PWD

# build the singularity comtainer using debian
printf "\nBUILDING DEBIAN SINGULARITY CONTAINER\n"
singularity build --fakeroot $output_dir/singularity_debian.sif $PWD/singularity/singularity_debian_boot.def

# remove the environment yml file
rm -f $PWD/environment.yml