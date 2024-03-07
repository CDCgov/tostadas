/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    RUNNING SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process SUBMISSION_SRA {

    publishDir "$params.output_dir/$params.submission_output_dir/", mode: 'copy', overwrite: params.overwrite_output

    //label'main'

    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'cdcgov/seqsender-dev' : 'cdcgov/seqsender-dev'  }"

    input:
    tuple val(meta), path(validated_meta_path), path(fasta_path), path(fastq_1), path(fastq_2)
    path submission_config
    val annotation_name

    // define the command line arguments based on the value of params.submission_test_or_prod
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    
    script:
    """
    mkdir -p $meta.id $meta.id/raw_reads
    mv $fastq_1 $meta.id/raw_reads/
    mv $fastq_2 $meta.id/raw_reads/

    submission.py submit \
        --sra \
        --biosample \
        --organism $params.organism \
        --submission_dir .  \
        --submission_name ${validated_meta_path.getBaseName()} \
        --config $submission_config  \
        --metadata_file $validated_meta_path $test_flag
    """

    output:
    path "${validated_meta_path.getBaseName()}", emit: submission_files
    path "*.csv", emit: submission_log
}

