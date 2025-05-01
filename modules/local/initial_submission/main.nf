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
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    def send_submission_email = params.send_submission_email == true ? '--send_email' : ''
    def biosample = params.biosample == true ? '--biosample' : ''
    def sra = "sra" in enabledDatabases ? '--sra' : ''
    def genbank = "genbank" in enabledDatabases ? '--genbank' : ''

    // Assemble per-sample arguments, quoting paths in case of spaces
    def sample_args_list = samples.collect { sample ->
        def s = [
            "sample_id=${sample.meta.sample_id}",
            "fq1=${sample.fq1}",
            "fq2=${sample.fq2}",
            "nanopore=${sample.nanopore}",
            "fasta=${sample.fasta}",
            "gff=${sample.gff}"
        ].findAll { it.split('=')[1] != "null" }  // remove nulls
        .join(',')
        return "\"${s}\""
    }

    def sample_args = sample_args_list.collect { "--sample ${it}" }.join(' ')

    """ 
    submission_new.py \
        --submit \
        --submission_name ${meta.batch_id} \
        --config_file $submission_config  \
        --metadata_file ${meta.batch_tsv} \
        --species $params.species \
        --output_dir  ./${params.metadata_basename} \
        ${sample_args} \
        --custom_metadata_file $params.custom_fields_file \
        --submission_mode $params.submission_mode \
        $test_flag \
        $send_submission_email \
        $genbank $sra $biosample
    """

    output:
    tuple val(meta), path("${params.metadata_basename}/${meta.batch_id}"), emit: submission_files
}