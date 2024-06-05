/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process SUBMISSION_FULL {

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

    script:
    """     
    mkdir -p $meta.id $meta.id/raw_reads
    mv $fastq_1 $meta.id/raw_reads/
    mv $fastq_2 $meta.id/raw_reads/

    submission.py submit \
        --genbank --sra --biosample \
        --organism $params.organism \
        --submission_dir .  \
        --submission_name ${validated_meta_path.getBaseName()} \
        --config $submission_config  \
        --metadata_file $validated_meta_path \
        --fasta_file $fasta_path \
        --annotation_file $annotations_path \
        --table2asn $test_flag $send_email_flag

    rm table2asn
    """

    output:
    path "${validated_meta_path.getBaseName()}", emit: submission_files
    path "*.csv", emit: submission_log
}