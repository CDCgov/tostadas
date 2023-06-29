# !/bin/bash


if command -v mamba >/dev/null 2>&1; then
    echo "Mamba exists on the system"
else
    echo "Mamba does not exist on the system"
    echo "Installing mamba now..."
    curl -L -O https://github.com/conda-forge/miniforge/releases/latest/download/Mambaforge-$(uname)-$(uname -m).sh
    bash Mambaforge-$(uname)-$(uname -m).sh -b -p $HOME/mambaforge
    export PATH="$HOME/mambaforge/bin:$PATH"
    source $HOME/mambaforge/etc/profile.d/conda.sh
    rm -f Mambaforge-$(uname)-$(uname -m).sh
fi

echo "Creating mamba environment"
mamba env create -f tests/test_env.yml python=3.9
conda activate tostadas_tests

echo "Running tests"
pytest -p no:warnings tests/test_main.py


