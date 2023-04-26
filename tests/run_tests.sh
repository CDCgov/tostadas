# !/bin/bash

ENV_NAME="tostadas_test_docker"
IMG_NAME="tostadas_test"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Check if Docker is installed
if ! command -v docker &> /dev/null
then
    echo "Docker is not installed on this system. Please install Docker and try again."
    exit 1
fi

# Check if the Conda environment exists
if conda env list | grep -q "^${ENV_NAME}\s"
then
    # If the environment exists, delete it
    echo "Deleting existing Conda environment..."
    conda env remove --quiet --name ${ENV_NAME}
fi

# Create a new Conda environment
echo "Creating new Conda environment..."
conda create --quiet -y --name ${ENV_NAME}

# Activate the test conda environment 
source activate ${ENV_NAME}

# Install yq into it 
if ! command -v yq &> /dev/null
then
    echo "yq not found. Installing..."
    conda install -y --quiet -c conda-forge yq
fi

# Read the password from the docker config and save as variable
chmod 777 $PROJECT_DIR/tests/docker_configs
chmod 777 $PROJECT_DIR/tests/docker_configs/personal.yaml
PASSWORD=$(yq -e '.password' $PROJECT_DIR/tests/docker_configs/personal.yaml)

# Check if service command is available
if command -v systemctl &> /dev/null
then
    # If service command is not available, use systemctl instead
    SERVICE_COMMAND="systemctl"
else
    if command -v service &> /dev/null
    then
        SERVICE_COMMAND="service"
    else
        SERVICE_COMMAND="absent"
    fi
fi

# Check if Docker daemon is already running
if [ $SERVICE_COMMAND = "absent" ]; then
    echo "Skipping Docker daemon check and start since Systemctl nor Service is available in system... will assume it is running and proceed"
else
    if ! ${SERVICE_COMMAND} docker status > /dev/null 2>&1
    then
        # If not running, start the Docker daemon with the password
        echo "Starting Docker daemon..."
        echo ${PASSWORD} | sudo -S ${SERVICE_COMMAND} start docker
    else
        echo "Docker daemon is already running."
    fi
fi

# Change directories 
cd ${SCRIPT_DIR}

# Build the docker image 
docker build -t ${IMG_NAME} .

# Run the docker container
docker run ${IMG_NAME}

