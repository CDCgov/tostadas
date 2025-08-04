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
    val sample_id
    path fasta
    path gff
   
    output:
    path "*.tsv", emit: tsv_files // undecided whether to include this here
    path "*.fasta", optional: true, emit: fasta
    path "*.gff", optional: true, emit: gff
    path "error.txt", optional: true, emit: errors
    
    script:

        // get absolute path if relative dir passed
        def resolved_outdir = params.outdir.startsWith('/') ? params.outdir : "${baseDir}/${params.outdir}"

        // Resolve submission_config path
        def resolved_submission_config = params.submission_config.startsWith('/') ? params.submission_config : "${baseDir}/${params.submission_config}"

        // Run the Python script for validating and cleaning FASTA files and copying the GFF file
        """
        python3 validate_and_clean_fasta.py ${fasta} ${gff} > ${resolved_outdir}/error.txt 2>&1
        """
}