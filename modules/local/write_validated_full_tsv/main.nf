process WRITE_VALIDATED_FULL_TSV {

    input:
    path validated_tsvs

    output:
    path "validated_metadata_all_samples.tsv", emit: validated_concatenated_tsv

    script:
    """
    cat ${validated_tsvs.join(' ')} > validated_metadata_all_samples.tsv
    """
}
