/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                RUN CONCAT GFFS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process CONCAT_GFFS {

    conda("conda-forge::python=3.8.3 conda-forge::pandas")
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'https://depot.galaxyproject.org/singularity/pandas:1.1.5' :
        'biocontainers/pandas:1.5.2' }"

	input:
	path ref_gff_path
    tuple val(meta), path(fasta), path(repeatmasker_gff), path(liftoff_gff)

	output:
    tuple val(meta), path('*.gff'), emit: gff
    tuple val(meta), path('*.txt'), emit: errors
    tuple val(meta), path('*.tbl'), emit: tbl

	script:
	"""
	repeatmasker_liftoff.py \
        --repeatm_gff $repeatmasker_gff \
        --liftoff_gff $liftoff_gff \
        --refgff $ref_gff_path \
        --fasta $fasta  \
        --sample_name $meta.sample_id
	"""
}

