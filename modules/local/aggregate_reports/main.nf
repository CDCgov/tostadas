/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                            SUMMARIZE SUBMISSION REPORTS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/

process AGGREGATE_REPORTS {
    
    conda(params.env_yml)
    container "${ workflow.containerEngine == 'singularity' && !task.ext.singularity_pull_docker_container ?
        'docker.io/staphb/tostadas:latest' : 'docker.io/staphb/tostadas:latest' }"

    input:
    path(report_csvs)

    output:
    path("submission_report.csv"), emit: submission_report

    script:
    """
    set -eux
    python3 - << 'EOF'
    import pandas as pd
    from functools import reduce

    # Read all CSVs into a list of dataframes
    files = [${report_csvs.collect { "'${it}'" }.join(', ')}]
    dfs = [pd.read_csv(f) for f in files]

    # Merge them on 'submission_id'
    merged = reduce(lambda left, right: pd.merge(left, right, on='submission_id', how='outer'), dfs)

    # Save result
    merged.to_csv('submission_report.csv', index=False)
    EOF

    """
}
