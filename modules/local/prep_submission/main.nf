/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process PREP_SUBMISSION {

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'docker.io/staphb/tostadas:latest' : 'docker.io/staphb/tostadas:latest' }"

    input:
    tuple val(meta), val(samples), val(enabledDatabases)
    path(submission_config)
    
    output:
    tuple val(meta), path("${meta.batch_id}"), emit: submission_files

    when:
    "sra" in enabledDatabases || "genbank" in enabledDatabases || "biosample" in enabledDatabases

    script:
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    def send_submission_email = params.send_submission_email == true ? '--send_email' : ''
    def dry_run = params.dry_run == true ? '--dry_run' : ''
    def biosample = params.biosample == true ? '--biosample' : ''
    def sra = "sra" in enabledDatabases ? '--sra' : ''
    def genbank = "genbank" in enabledDatabases ? '--genbank' : ''
    def wastewater = params.wastewater == true ? '--wastewater' : ''

    // Assemble per-sample arguments, quoting paths in case of spaces
    def sample_args_list = samples.collect { sample ->
        def s = [
            "sample_id=${sample.meta.sample_id}",
            sample.get("fq1")      ? "fq1=${sample.fq1}"       : null,
            sample.get("fq2")      ? "fq2=${sample.fq2}"       : null,
            sample.get("nnp")      ? "nnp=${sample.nanopore}"  : null,
            sample.get("fasta")    ? "fasta=${sample.fasta}"   : null,
            sample.get("gff")      ? "gff=${sample.gff}"       : null
        ].findAll { it != null }
        .join(',')
        return "\"${s}\""
    }
    def sample_args = sample_args_list.collect { "--sample ${it}" }.join(' ')

    """
    submission_prep.py \
        --submission_name ${meta.batch_id} \
        --config_file $submission_config  \
        --metadata_file ${meta.batch_tsv} \
        --identifier ${params.metadata_basename} \
        --species $params.species \
        --outdir  ${meta.batch_id} \
        ${sample_args} \
        --submission_mode $params.submission_mode \
        $test_flag \
        $send_submission_email \
        $genbank $sra $biosample \
        $wastewater \
        $dry_run
    """
}