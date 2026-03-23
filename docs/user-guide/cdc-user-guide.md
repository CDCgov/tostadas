# CDC User Guide

This page contains information specific to running TOSTADAS on CDC high-performance computing (HPC) infrastructure. For general pipeline usage, see the [Submission Guide](submission_guide.md) and [Installation](installation.md) pages.

## Environment Setup

### Clone the Repository

```bash
git clone https://github.com/CDCgov/tostadas.git
cd tostadas
```

### Load Required Modules

Load Nextflow and Singularity on the CDC HPC cluster:

```bash
ml nextflow singularity
```

Both modules must be loaded before running the pipeline. Singularity is the recommended container runtime on CDC systems because Docker is not available on shared HPC nodes.

### Verify Nextflow

Confirm that Nextflow is available:

```bash
nextflow -version
```

Expected Output:

```text
nextflow version <CURRENT VERSION>
```

## Running on CDC HPC

### Using the scicomp_rosalind Profile

CDC provides a preconfigured Nextflow profile for the HPC environment. Use the `scicomp_rosalind` profile in combination with `singularity`:

```bash
nextflow run main.nf -profile singularity,scicomp_rosalind --workflow full_submission --submission_config conf/submission_config.yaml
```

This profile sets appropriate executor settings, queue configurations, and resource defaults for the CDC HPC scheduler.

### CDC Nextflow Configuration

Load the shared Nextflow configuration file maintained by the SciComp team:

```bash
nextflow run main.nf -c /scicomp/reference-pure/nextflow/nextflow-configs/latest.scicomp.config -profile singularity,scicomp_rosalind --workflow full_submission --submission_config conf/submission_config.yaml
```

This configuration provides site-specific defaults for the job scheduler, module paths, and scratch directories. It can be combined with any additional parameters or profiles.

### SGE Job Scheduler Considerations

The CDC HPC uses the SGE (Sun Grid Engine) job scheduler. Keep the following in mind:

- **Walltime limits.** Long-running processes (such as VADR annotation on large batches) may exceed default walltime allocations. If jobs are killed by the scheduler, increase the walltime in your Nextflow process configuration or use `-resume` to pick up where the run left off.
- **Memory requests.** SGE enforces hard memory limits. If a process exceeds its requested memory, SGE will terminate it. Check `.command.log` in the process work directory for out-of-memory indicators.
- **Queue selection.** The `scicomp_rosalind` profile selects appropriate queues automatically. If you need to override the queue, use Nextflow's `process.queue` directive in a custom config file.

## Singularity Cache and Scratch Directories

On CDC systems, home directories have limited storage quotas. Configure the Singularity cache to use a scratch or project directory with sufficient space:

```bash
export NXF_SINGULARITY_CACHEDIR=/path/to/scratch/singularity_cache
export SINGULARITY_TMPDIR=/path/to/scratch/singularity_tmp
```

!!! warning
    If the Singularity cache is stored in a home directory with a small quota, image pulls will fail with disk space errors. Always point the cache to a volume with adequate storage.

Set these variables in your shell profile or job submission script so they persist across sessions.

## Shared Data Locations

CDC HPC systems provide shared group directories for reference data and collaborative storage. Consult your group's documentation or system administrators for the paths to:

- Shared reference databases (e.g., VADR models, Bakta databases)
- Group-level project directories for pipeline output
- Scratch space for temporary pipeline files

Storing large reference files in shared directories avoids redundant downloads and conserves quota on individual home directories.

## Network Considerations: FTP vs. SFTP

CDC network firewalls may block outbound FTP connections (port 21) from compute nodes. If FTP-based submissions fail with connection timeouts, switch to SFTP mode:

```bash
nextflow run main.nf -profile singularity,scicomp_rosalind --workflow biosample_and_sra --submission_mode sftp --submission_config conf/submission_config.yaml
```

Ensure that `NCBI_sftp_host` is set in your `submission_config.yaml`. See the [SFTP Submission Mode](submission_guide.md#sftp-submission-mode) section for details.

!!! tip
    If you are unsure whether FTP is blocked, test connectivity from a compute node: `curl -v ftp://ftp-private.ncbi.nlm.nih.gov`. A connection timeout indicates that SFTP mode is required.

## Update the Submission Config

Before running any submission, update `conf/submission_config.yaml` with your NCBI center account credentials and organization details.

See [Run a test submission](installation.md#run-a-test-submission).
