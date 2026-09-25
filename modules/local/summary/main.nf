process SUMMARY {
    label 'process_single'

    conda(params.env_yml)
    container 'docker.io/staphb/tostadas:latest'

    input:
    path(vadr_outputs)

    output:
    path("batch_pass_fail.tsv"), emit: pass_fail
    path("batch_alerts.tsv"), emit: alerts

    script:
    """
    # Concatenate all .alt.list files, dedup headers
    find -L . -type f -name '*vadr.alt.list' -exec awk 'FNR==1 && NR!=1{next}{print}' {} + > batch_alerts.tsv || echo "No alerts found" > batch_alerts.tsv

    # Extract pass/fail classification from .mdl files (line 4)
    printf 'sample\\tidx\\tmodel\\tgroup\\tsubgroup\\tnum_seqs\\tnum_pass\\tnum_fail\\n' > batch_pass_fail.tsv
    find -L . -type f -name "*.mdl" | while read file; do
        sample=\$(basename "\$file" | sed 's/_out\\..*//')
        sed -n '4p' "\$file" | tr -s ' ' '\\t' | awk -v s="\$sample" '{print s"\\t"\$0}'
    done >> batch_pass_fail.tsv
    """
}
