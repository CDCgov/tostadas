/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                INITIALIZE FILES
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process INITIALIZE_FILES {

    label 'main'

    // publishDir "$params.output_dir", mode: 'copy', overwrite: params.overwrite_output

    input:
        val signal

    script:
        """
        general_utility.py --check_fasta_paths True --check_fasta_names True --meta_path $params.meta_path \
        --fasta_path $params.fasta_path --output_fasta_path fasta
        """

    output:
        path "fasta", emit: fasta_dir
        path "fasta/*.{fasta,fastq}", emit: fasta_files
}