/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN GENBANK VALIDATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process GENBANK_VALIDATION {

    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'docker.io/staphb/tostadas:latest' : 'docker.io/staphb/tostadas:latest' }"

    input:
    tuple val(meta), path(fasta), path(gff) // Fasta and GFF are included in the tuple

    output:
    tuple path(tsv_files), path("${fasta.baseName}_cleaned.fasta"), path("${gff.baseName}_validated.gff")// Outputs are defined as a single tuple
    
    script:

        // get absolute path if relative dir passed
        def resolved_outdir = params.outdir.startsWith('/') ? params.outdir : "${baseDir}/${params.outdir}"

        // Resolve submission_config path
        def resolved_submission_config = params.submission_config.startsWith('/') ? params.submission_config : "${baseDir}/${params.submission_config}"

        // Run the Python script for validating and cleaning FASTA files and copying the GFF file
        """
        validate_genbank.py ${fasta} ${gff} 
        """
}