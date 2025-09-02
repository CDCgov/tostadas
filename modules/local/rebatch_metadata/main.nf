/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                                    REBATCH TSVs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process REBATCH_METADATA {
    input:
        path full_tsv
        path batch_summary_json

    output:
        tuple path("*.tsv"), path("*.json"), emit: rebatch_tuple
    
    script:
    """
    python3 <<'EOF'
    import pandas as pd, json, os, sys
    full = pd.read_csv("${full_tsv}", sep="\\t")
    summary = json.load(open("${batch_summary_json}"))

    for batch_file, sample_list in summary.items():
        batch_id = os.path.splitext(batch_file)[0]
        #outdir = f"${params.outdir}/"
        #os.makedirs(outdir, exist_ok=True)
        #rebatch_tsv = f"{outdir}/{batch_file}"
        full[full["sample_name"].isin(sample_list)].to_csv(batch_file, sep="\t", index=False)
        meta = {"batch_id": batch_id, "batch_tsv": batch_file}
        samples = [ {"sample_id": sid} for sid in sample_list ]
        enabled = ["biosample"]
        
        with open(f"{batch_id}.json", "w") as f:
            json.dump({"meta": meta, "samples": samples, "enabled": enabled}, f)
    EOF
    """
}