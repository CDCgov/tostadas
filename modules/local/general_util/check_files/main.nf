/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                CHECK / INITIALIZE FILES 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process CHECK_FILES {

    // label 'main'
    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'staphb/tostadas:latest' :
        'staphb/tostadas:latest' }"

    input:
        val signal
        val annotation_entry
        val submission_entry
        val update_submission_entry
        path metadata_files

    script:
        """
        general_utility.py --fasta_path $params.fasta_path --meta_path $metadata_files --gff_path $params.final_annotated_files_path --ref_gff_path $params.ref_gff_path \
        --ref_fasta_path $params.ref_fasta_path --submission_config $params.submission_config --annotation_entry $annotation_entry --run_submission $params.submission --run_annotation $params.annotation \
        --run_liftoff $params.liftoff --run_repeatmasker_liftoff $params.repeatmasker_liftoff --run_vadr $params.vadr --run_bakta $params.bakta \
        --submission_database $params.submission_database --submission_entry $submission_entry --update_submission_entry $update_submission_entry --processed_samples $params.processed_samples
        """

    output:
        path "new_fasta/", emit: fasta_dir, optional: true
        path "new_fasta/*.{fasta,fastq}", emit: fasta_files, optional: true
        path "new_meta/", emit: meta_dir, optional: true
        path "new_meta/*.{tsv,csv}", emit: meta_files, optional: true
        path "new_gff/", emit: gff_dir, optional: true
        path "new_gff/*.gff", emit: gff_files, optional: true
        path "update_entry/*", emit: samples, optional: true
}