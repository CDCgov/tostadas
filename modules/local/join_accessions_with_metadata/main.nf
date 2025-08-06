/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN METADATA VALIDATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process JOIN_ACCESSIONS_WITH_METADATA {

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'docker.io/staphb/tostadas:latest' : 'docker.io/staphb/tostadas:latest' }"

    input:
        path validated_metadata_tsv
        path aggregated_csv

    output:
        path "${params.metadata_basename}_updated.xlsx", emit: updated_excel

    script:
        """
        python join_accessions_with_metadata.py \
        --metadata_tsv ${validated_metadata_tsv} \
        --submission_report ${aggregated_csv} \
        --output ${params.metadata_basename}_updated.xlsx
        """
}