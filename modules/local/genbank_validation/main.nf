/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN METADATA VALIDATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process GENBANK_VALIDATION {

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'docker.io/staphb/tostadas:latest' : 'docker.io/staphb/tostadas:latest' }"

    input:
    path meta_path
   
    output:
    path "*.tsv", emit: tsv
    path "*.fasta", optional: true, emit: fasta
    path "*.gff", optional: true, emit: gff
    path "error.txt", optional: true, emit: errors
    
    script:

        // get absolute path if relative dir passed
        def resolved_outdir = params.outdir.startsWith('/') ? params.outdir : "${baseDir}/${params.outdir}"

        // Resolve submission_config path
        def resolved_submission_config = params.submission_config.startsWith('/') ? params.submission_config : "${baseDir}/${params.submission_config}"

        """
        # placeholder script with some dummy args
        validate_genbank.py \
            --meta_path $meta_path \
            --output_dir . \
            --config_file $resolved_submission_config \
        """
}