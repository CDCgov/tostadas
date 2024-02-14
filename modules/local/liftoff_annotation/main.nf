/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN LIFTOFF ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process LIFTOFF {

    label 'main'
    
    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/liftoff:1.6.3--pyhdfd78af_0' :
        'quay.io/biocontainers/liftoff:1.6.3--pyhdfd78af_0'}"
        
    publishDir "$params.output_dir", mode: 'copy', overwrite: params.overwrite_output

    input:
    val signal
    path meta_path
    path fasta_path
    path ref_fasta_path 
    path ref_gff_path 

    script:
    """
    liftoff_submission.py --fasta_path $fasta_path --meta_path $meta_path --ref_fasta_path $ref_fasta_path \
    --ref_gff_path $ref_gff_path --parallel_processes $params.lift_parallel_processes --final_liftoff_output_dir $params.final_liftoff_output_dir \
    --delete_temp_files $params.lift_delete_temp_files --minimap_path $params.lift_minimap_path --feature_database_name $params.lift_feature_database_name \
    --unmapped_features_file_name $params.lift_unmapped_features_file_name --distance_scaling_factor $params.lift_distance_scaling_factor \
    --copy_threshold $params.lift_copy_threshold --coverage_threshold $params.lift_coverage_threshold --child_feature_align_threshold $params.lift_child_feature_align_threshold \
    --copies $params.lift_copies --flank $params.lift_flank --mismatch $params.lift_mismatch --gap_open $params.lift_gap_open --gap_extend $params.lift_gap_extend
    """

    output:
    path "$params.final_liftoff_output_dir/*/gff/*.gff", emit: gff
    path "$params.final_liftoff_output_dir/*/errors/*.txt", emit: errors
    path "$params.final_liftoff_output_dir/*/tbl/*.tbl", emit: tbl
}
