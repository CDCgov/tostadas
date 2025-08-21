process WRITE_VALIDATED_FULL_TSV {

    input:
    path validated_tsvs

    output:
    path "validated_metadata_all_samples.tsv", emit: validated_concatenated_tsv

    script:
    """

    python3 - <<'EOF'
    import pandas as pd

    files = ${validated_tsvs.collect{ '"' + it + '"' }.join(', ')}
    output = "validated_metadata_all_samples.tsv"

    dfs = []
    for i, f in enumerate([${validated_tsvs.collect{ '"' + it + '"' }.join(', ')}]):
        if i == 0:
            df = pd.read_csv(f, sep="\\t", dtype=str)
        else:
            df = pd.read_csv(f, sep="\\t", dtype=str, header=0)
        dfs.append(df)

    final_df = pd.concat(dfs, ignore_index=True)
    final_df.to_csv(output, sep="\\t", index=False)
    EOF
    """
}
