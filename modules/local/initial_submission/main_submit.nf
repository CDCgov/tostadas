/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            RUNNING SUBMISSION PREP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process SUBMISSION_SUBMIT {

    publishDir "$params.output_dir/$params.submission_output_dir", mode: 'copy', overwrite: params.overwrite_output

    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
    tuple val(meta), path(validated_meta_path), path(fasta_path), path(fastq_1), path(fastq_2), path(annotations_path)
    path submission_config

    // define the command line arguments based on the value of params.submission_test_or_prod, params.send_submission_email
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    def send_email_flag = params.send_submission_email == 'true' ? '--send_submission_email' : ''
    def biosample = params.biosample == 'true' ? '--biosample' : ''
    def sra = params.sra == 'true' ? '--sra' : ''
    def genbank = params.genbank == 'true' ? '--genbank' : ''

    script:
    """     
    # maybe change to submission.py prep (one script)
    # might change organism to biosample_package
    submission_submit.py \
        --submission_name $meta.id
        --config_file $submission_config  \
        --metadata_file $validated_meta_path \
        --fasta_file $fasta_path \
        --annotation_file $annotations_path \
        --fastq1 $fastq_1 \
        --fastq2 $fastq_2 \
        --organism $params.organism \
        $test_flag $send_email_flag \
        $genbank $sra $biosample 

    """

    output:
    path "${validated_meta_path.getBaseName()}", emit: submission_files
    path "*.csv", emit: submission_log
}