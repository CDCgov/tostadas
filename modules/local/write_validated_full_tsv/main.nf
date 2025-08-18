process WRITE_VALIDATED_FULL_TSV {

    input:
    path validated_tsvs

    output:
    path "validated_metadata_all_samples.tsv", emit: validated_concatenated_tsv

    script:
    """
    # Keep the first file's header, skip headers from subsequent files
    awk 'FNR==1 && NR!=1 { next } { print }' ${validated_tsvs.join(' ')} \
        > validated_metadata_all_samples.tsv
    """
}
