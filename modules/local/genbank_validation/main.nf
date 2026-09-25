/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN GENBANK VALIDATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process GENBANK_VALIDATION {

    conda(params.env_yml)
    container 'docker.io/staphb/tostadas:latest'

    input:
    tuple val(meta), path(fasta)

    output:
    tuple val(meta), path("genbank/${fasta.baseName}_cleaned.fsa")
    
    script:
        // Run the Python script for validating and cleaning FASTA files and copying the GFF file
        """
        validate_genbank.py ${fasta}
        """
}