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
    tuple val(meta), path("${fasta.baseName}_cleaned.fasta"), path("${gff.baseName}_validated.gff")// Outputs are defined as a single tuple
    
    script:
        // Run the Python script for validating and cleaning FASTA files and copying the GFF file
        """
        validate_genbank.py ${fasta} ${gff} 
        """
}