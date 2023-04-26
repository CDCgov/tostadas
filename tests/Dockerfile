FROM continuumio/miniconda3 as app

ARG CONDA_ENV=ci_tostadas

# Stage 1: Clone the repository and checkout the current branch
FROM app as GETREPO
WORKDIR /app
RUN git clone https://github.com/CDCgov/tostadas.git && \
    cd tostadas && \
    git checkout $(git symbolic-ref --short HEAD)

# Stage 2: Set up conda environment
FROM app as ENVSETUP
WORKDIR /app
COPY --from=GETREPO /app /app
RUN conda install mamba -n base -c conda-forge
RUN conda create -n ${CONDA_ENV} python=3.9
RUN echo "conda activate ${CONDA_ENV}" >> ~/.bashrc
SHELL ["conda", "run", "-n", "ci_tostadas", "/bin/bash", "-c"]
RUN mamba install -c bioconda nextflow
RUN conda install pytest -c conda-forge
RUN conda install pandas
RUN ["/bin/bash", "-c", "chmod -R a+rw /opt/conda/envs/${CONDA_ENV}"]

# Stage 3: Run tests on environment 
FROM app as ENVTEST
WORKDIR /app
COPY --from=ENVSETUP /opt/conda /opt/conda
RUN nextflow --version && \
    pytest --version && \
    pandas --version 

# Stage 4: Specify Entrypoint to be used when running container
FROM app as RUNAPP
WORKDIR /app
COPY --from=ENVSETUP /opt/conda /opt/conda
COPY . /app/tests/
CMD ["conda", "run", "--name", "ci_tostadas", "pytest", "-p", "no:warnings", "/app/tests/test_main.py"]