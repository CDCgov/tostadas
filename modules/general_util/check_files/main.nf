/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                CHECK / INITIALIZE FILES 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process CHECK_FILES {

    label 'main'

    input:
        val signal
        val annotation_entry
        val submission_or_no

    script:
        """
        general_utility.py --fasta_path $params.fasta_path --meta_path $params.meta_path --gff_path $params.final_annotated_files_path --ref_gff_path $params.ref_gff_path \
        --ref_fasta_path $params.ref_fasta_path --submission_config $params.submission_config --annotation_entry $annotation_entry --run_submission $submission_or_no --run_annotation $params.run_annotation \
        --run_liftoff $params.run_liftoff --run_repeatmasker_liftoff $params.run_repeatmasker_liftoff --run_vadr $params.run_vadr --run_bakta $params.run_bakta \
        --submission_database $params.submission_database
        """

    output:
        path "new_fasta/", emit: fasta_dir 
        path "new_fasta/*.{fasta,fastq}", emit: fasta_files
        path "new_meta/", emit: meta
        path "new_gff/", emit: gff