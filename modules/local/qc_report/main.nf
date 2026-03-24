process QC_REPORT {
    label 'process_single'

    conda(params.env_yml)
    container 'docker.io/staphb/tostadas:latest'

    input:
    path(pass_fail_tsv)
    path(submission_dirs)

    output:
    path("sqn_pass"), emit: sqn_pass
    path("sqn_fail"), emit: sqn_fail
    path("submission_qc_report.tsv"), emit: qc_report

    script:
    """
    mkdir -p sqn_pass sqn_fail

    # Build fail list from VADR pass/fail TSV
    awk -F'\\t' 'NR>1 && \$8>0 {gsub(/_mev\\.vadr\\.mdl/,"",\$1); print \$1}' ${pass_fail_tsv} > fail_list.txt

    # Sort SQN files into pass/fail
    find . -name "*.sqn" -not -path "./sqn_pass/*" -not -path "./sqn_fail/*" | while read sqn; do
        sample=\$(basename \$(dirname "\$sqn"))
        if grep -qF "\$sample" fail_list.txt; then
            cp "\$sqn" sqn_fail/
        else
            cp "\$sqn" sqn_pass/
        fi
    done

    # Generate QC report
    pass_count=\$(ls sqn_pass/*.sqn 2>/dev/null | wc -l)
    fail_count=\$(ls sqn_fail/*.sqn 2>/dev/null | wc -l)

    printf 'sample\\tvadr_status\\tsqn_location\\n' > submission_qc_report.tsv

    for sqn in sqn_pass/*.sqn; do
        [ -f "\$sqn" ] || continue
        sample=\$(basename "\$sqn" .sqn)
        printf '%s\\tPASS\\tsqn_pass/%s\\n' "\$sample" "\$(basename \$sqn)" >> submission_qc_report.tsv
    done

    for sqn in sqn_fail/*.sqn; do
        [ -f "\$sqn" ] || continue
        sample=\$(basename "\$sqn" .sqn)
        printf '%s\\tFAIL\\tsqn_fail/%s\\n' "\$sample" "\$(basename \$sqn)" >> submission_qc_report.tsv
    done

    echo "QC Summary: \${pass_count} PASS, \${fail_count} FAIL"
    """
}
