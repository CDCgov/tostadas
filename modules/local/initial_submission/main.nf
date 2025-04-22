/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process SUBMISSION {

    publishDir "$params.output_dir/$params.submission_output_dir", mode: 'copy', overwrite: params.overwrite_output

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
    tuple val(meta), val(samples), val(enabledDatabases)
    path(submission_config)

    when:
    "sra" in enabledDatabases || "genbank" in enabledDatabases || "biosample" in enabledDatabases

    script:
    def batch_tsv = "${params.output_dir}/${params.val_output_dir}/${params.metadata_basename}/batched_tsvs/${meta.batch_id}.tsv"
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    def send_submission_email = params.send_submission_email == true ? '--send_email' : ''
    def biosample = params.biosample == true ? '--biosample' : ''
    def sra = "sra" in enabledDatabases ? '--sra' : ''
    def genbank = "genbank" in enabledDatabases ? '--genbank' : ''

    """   
    echo "DEBUG: Submission Running for $meta.batch_id"
    echo "DEBUG: $batch_tsv"
    submission_new.py \
        --submit \
        --submission_name ${meta.batch_id} \
        --config_file $submission_config  \
        --metadata_file $batch_tsv \
        --species $params.species \
        --output_dir  . \
        --custom_metadata_file $params.custom_fields_file \
        --submission_mode $params.submission_mode \
        $test_flag \
        $send_submission_email \
        $genbank $sra $biosample
    """

    output:
    tuple val(meta), path("${params.metadata_basename}/${meta.batch_id}"), emit: submission_files
}