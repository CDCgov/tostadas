process QC_REPORT {
    label 'process_single'

    conda(params.env_yml)
    container 'docker.io/staphb/tostadas:latest'

    input:
    path(pass_fail_tsv)
    path(submission_dirs)

    output:
    path("all_pass_sqn"), emit: sqn_pass
    path("all_fail_sqn"), emit: sqn_fail
    path("submission_qc_report.tsv"), emit: qc_report

    script:
    """
    mkdir -p all_pass_sqn all_fail_sqn

    # Build fail list from VADR pass/fail TSV
    awk -F'\\t' 'NR>1 && \$8>0 {gsub(/_mev\\.vadr\\.mdl/,"",\$1); print \$1}' ${pass_fail_tsv} > fail_list.txt

    # Sort SQN files into pass/fail
    find -L . -name "*.sqn" -not -path "./all_pass_sqn/*" -not -path "./all_fail_sqn/*" | while read sqn; do
        sample=\$(basename \$(dirname "\$sqn"))
        if grep -qF "\$sample" fail_list.txt; then
            cp "\$sqn" all_fail_sqn/
        else
            cp "\$sqn" all_pass_sqn/
        fi
    done

    # Generate QC report
    pass_count=\$(ls all_pass_sqn/*.sqn 2>/dev/null | wc -l)
    fail_count=\$(ls all_fail_sqn/*.sqn 2>/dev/null | wc -l)

    printf 'sample\\tvadr_status\\n' > submission_qc_report.tsv

    for sqn in all_pass_sqn/*.sqn; do
        [ -f "\$sqn" ] || continue
        sample=\$(basename "\$sqn" .sqn)
        printf '%s\\tPASS\\n' "\$sample" >> submission_qc_report.tsv
    done

    for sqn in all_fail_sqn/*.sqn; do
        [ -f "\$sqn" ] || continue
        sample=\$(basename "\$sqn" .sqn)
        printf '%s\\tFAIL\\n' "\$sample" >> submission_qc_report.tsv
    done

    echo "QC Summary: \${pass_count} PASS, \${fail_count} FAIL"
    """
}
