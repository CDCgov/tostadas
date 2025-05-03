/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    FETCH SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process FETCH_SUBMISSION {

    publishDir "${params.output_dir}/${params.submission_output_dir}/${params.metadata_basename}",
            mode: 'copy',
            overwrite: params.overwrite_output

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
    val wait_time
    tuple val(meta), val(samples), val(enabledDatabases), path(submission_folder)
    path(submission_config)

    script:
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    def send_submission_email = params.send_submission_email == true ? '--send_email' : ''
    def biosample = params.biosample == true ? '--biosample' : ''
    def sra = params.sra == true ? '--sra' : ''
    def genbank = params.genbank == true ? '--genbank' : ''

    def outdir = submission_folder.getName()

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
        --fetch \
        --submission_name ${meta.batch_id} \
        --config_file $submission_config  \
        --metadata_file ${meta.batch_tsv} \
        --species $params.species \
        --output_dir  ${meta.batch_id}  \
        ${sample_args} \
        --custom_metadata_file $params.custom_fields_file \
        --submission_mode $params.submission_mode \
        $test_flag \
        $send_submission_email \
        $genbank $sra $biosample
    """

output:
//tuple val(meta), path("${meta.batch_id}"), emit: submission_files
// todo: I don't love this solution (it references the folder created in SUBMISSION)
path("${meta.batch_id}/${meta.batch_id}.csv"), emit: submission_report

}