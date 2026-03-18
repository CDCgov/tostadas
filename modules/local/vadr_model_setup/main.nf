/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                        PREPARE VADR MODEL DIRECTORY
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    Ensures the VADR model directory is ready for annotation. Downloads the
    covariance model file if a URL is provided and the local copy is missing
    or invalid (e.g. a Git LFS pointer), then builds CM indices with cmpress.

    Runs once per pipeline invocation; cached on -resume if inputs are unchanged.
*/
process VADR_MODEL_SETUP {

    conda(params.vadr_env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'docker.io/staphb/vadr:latest' : 'docker.io/staphb/vadr:latest' }"

    // Network download; idempotent and safe to retry
    errorStrategy 'retry'
    maxRetries 3

    input:
    path vadr_models_dir

    output:
    path "models", emit: prepared_models

    script:
    def cm_url = params.vadr_cm_url ?: ''
    """
    cp -rL ${vadr_models_dir} models

    cm=models/${params.virus_subtype}.cm
    needs_cmpress=false

    # Download CM file if URL is provided and local copy is missing or invalid
    if [ -n "${cm_url}" ]; then
        if [ ! -f "\$cm" ] || [ "\$(wc -c < "\$cm" 2>/dev/null || echo 0)" -lt 1000 ]; then
            curl -L -o "\$cm" "${cm_url}"
            needs_cmpress=true
        fi
    fi

    # Verify CM file is present and valid
    if [ ! -f "\$cm" ] || [ "\$(wc -c < "\$cm" 2>/dev/null || echo 0)" -lt 1000 ]; then
        echo "ERROR: \$cm is missing or invalid. Set vadr_cm_url if the CM file must be downloaded." >&2
        exit 1
    fi

    # Build CM indices if they are missing, invalid, or the CM was just downloaded
    if [ "\$needs_cmpress" = true ] || [ ! -f "\${cm}.i1m" ] || [ "\$(wc -c < "\${cm}.i1m" 2>/dev/null || echo 0)" -lt 1000 ]; then
        cmpress -F "\$cm"
    fi
    """
}
