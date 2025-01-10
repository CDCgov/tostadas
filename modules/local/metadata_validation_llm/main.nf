/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN METADATA VALIDATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process METADATA_VALIDATION_LLM {

    // label 'main'

    //errorStrategy { sleep(Math.pow(2, task.attempt) * 200 as long); return 'retry' }
    //maxRetries 5

    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'us-east4-docker.pkg.dev/amd-nftower-poc/oamd-artifacts/openai-container:latest' : 'us-east4-docker.pkg.dev/amd-nftower-poc/oamd-artifacts/openai-container:latest' }"


    input:
    val api_key
    path meta_path

    script:
    """
    validate_metadata_llm.py \
        --api_key $api_key \
        --meta_path $meta_path \
        --out_dir .
    """

    output:
    path "*/*.tsv", emit: tsv_Files
    // path "*/tsv_per_sample", emit: tsv_dir
    // path "*/errors", emit: errors
}
