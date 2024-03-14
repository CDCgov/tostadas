/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN LIFTOFF CLI ANNOTATION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/


process LIFTOFF_CLI {
	
    conda (params.enable_conda ? params.env_yml : null)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/liftoff:1.6.3--pyhdfd78af_0' :
        'quay.io/biocontainers/liftoff:1.6.3--pyhdfd78af_0'}"

    publishDir "$params.output_dir/repeatmasker_liftoff_outputs", mode: "copy", overwrite: params.overwrite_output,
        saveAs: { filename ->
                      filename.indexOf('.fasta') > 0 ? "fasta/${filename}":
                      filename.indexOf('.txt') > 0 ? "errors/${filename}":
                      filename
        }

	input:
	tuple val(meta), path(fasta)
    path ref_fasta_path 
    path ref_gff_path 

	script:
    """
    liftoff -g $ref_gff_path -o ${fasta.baseName}_liftoff-orig.gff \
    -u $params.lift_unmapped_features_file_name \
    -a $params.lift_coverage_threshold -s $params.lift_child_feature_align_threshold \
    -d $params.lift_distance_scaling_factor -flank $params.lift_flank -p $params.lift_parallel_processes \
    -f $params.lift_feature_types -sc $params.lift_copy_threshold \
    -overlap $params.lift_overlap -mismatch $params.lift_mismatch -gap_open $params.lift_gap_open \
    -gap_extend $params.lift_gap_extend $fasta $ref_fasta_path
    """
    
    output:
    path fasta, emit: fasta
    path "*.gff", emit: gff
    path "*.txt", emit: errors

}
