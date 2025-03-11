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
    tuple val(meta), path(validated_meta_path), path(fasta_path), path(fastq_1), path(fastq_2), path(annotations_path), val(enabledDatabases)
    path(submission_config)

    when:
    {
        println "DEBUG: Checking when condition - enabledDatabases=${enabledDatabases}"
        return enabledDatabases && ("sra" in enabledDatabases || "genbank" in enabledDatabases || "biosample" in enabledDatabases)
    }()

    script:
    def test_flag = params.submission_prod_or_test == 'test' ? '--test' : ''
    def send_submission_email = params.send_submission_email == true ? '--send_email' : ''
    def biosample = params.biosample == true ? '--biosample' : ''
    def sra = "sra" in enabledDatabases ? '--sra' : ''
    def genbank = "genbank" in enabledDatabases ? '--genbank' : ''
    
    """   
    echo "DEBUG: mainf.nf: enabledDatabases=${enabledDatabases}"
    echo "DEBUG: mainf.nf: Params -> sra: $params.sra, genbank: $params.genbank, biosample: $params.biosample"
    echo "DEBUG: mainf.nf: Submission Running for $meta.id"
    echo "DEBUG: mainf.nf: Selected Databases: ${enabledDatabases[0]}"
    submission_new.py \
        --submit \
        --submission_name $meta.id \
        --config_file $submission_config  \
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
}