# !/bin/bash

# copy the file over to the docker image directory  
ENV_YML=../environment.yml
DESTINATION=$PWD/docker
cp $ENV_YML $DESTINATION

# build the image
docker build -t general ./docker

# delete the environment.yml that was copied over 
rm -f $DESTINATION/environment.yml