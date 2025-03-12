/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    UPDATE SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process UPDATE_SUBMISSION {

    publishDir "$params.output_dir/$params.submission_output_dir", mode: 'copy', overwrite: params.overwrite_output

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' : 'staphb/tostadas:latest' }"

    input:
    tuple val(meta), path(validated_meta_path), path(fasta_path), path(fastq_1), path(fastq_2), path(annotations_path), val(enabledDatabases)
    path(submission_config)

    when:
    "sra" in enabledDatabases || "genbank" in enabledDatabases || "biosample" in enabledDatabases

    script:
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    def send_submission_email = params.send_submission_email == true ? '--send_email' : ''
    def biosample = params.biosample == true ? '--biosample' : ''
    def sra = (params.sra == true && "sra" in enabledDatabases) ? '--sra' : ''
    def genbank = (params.genbank == true && "genbank" in enabledDatabases) ? '--genbank' : ''
    // get absolute path if relative dir passed
    def resolved_output_dir = params.output_dir.startsWith('/') ? params.output_dir : "${baseDir}/${params.output_dir}"

    """     
    submission_new.py \
        --update \
        --submission_name $meta.id \
        --submission_report ${resolved_output_dir}/${params.submission_output_dir}/submission_report.csv \
        --config_file $submission_config \
        --metadata_file $validated_meta_path \
        --species $params.species \
        --output_dir  . \
        ${fasta_path ? "--fasta_file $fasta_path" : ""} \
        ${annotations_path ? "--annotation_file $annotations_path" : ""} \
        ${fastq_1 ? "--fastq1 $fastq_1" : ""} \
        ${fastq_2 ? "--fastq2 $fastq_2" : ""} \
        --custom_metadata_file $params.custom_fields_file \
        --submission_mode $params.submission_mode \
        $test_flag \
        $send_submission_email \
        $genbank $sra $biosample 

    """
    output:
    tuple val(meta), path("${validated_meta_path.getBaseName()}"), emit: submission_files
    //path ""${validated_meta_path.getBaseName()}/*.csv", emit: submission_report
}