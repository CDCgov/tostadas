#!/usr/bin/env python3

import pandas as pd
import argparse
import logging
from submission_helper import setup_logging

def get_args():
    """Expected args from user for fetching reports"""
    parser = argparse.ArgumentParser(
        description="Add NCBI Accession IDs to the validated metadata file."
    )
    parser.add_argument('--metadata', required=True, help="Path to TSV metadata file with data for all samples")
    parser.add_argument('--submission_report', required=True, help="Path to submission_report.csv")
    parser.add_argument('--output', required=True, help="Path to final Excel file to write")
    return parser


def main():
    """
    """
    args = get_args().parse_args()
    params = vars(args)

    # Setup logging
    setup_logging(log_file='joine_accessions_with_metadata.log',
                  level=logging.DEBUG)

    # Load metadata TSV and submission report CSV
    metadata_df = pd.read_csv(params["metadata"], sep='\t', dtype=str)
    report_df = pd.read_csv(params["submission_report"], dtype=str)

    # Normalize join keys
    # todo: there is no sample_name restriction in the submission data, we need this otherwise we can't join them back 
    metadata_df['sample_name'] = metadata_df['sample_name'].str.strip().str.lower()
    report_df['submission_name'] = report_df['submission_name'].str.strip().str.lower()

    # Merge accessions from submission report
    merged_df = metadata_df.merge(
        report_df[['submission_name', 'biosample_accession', 'sra_accession', 'genbank_accession']],
        how='left',
        left_on='sample_name',
        right_on='submission_name'
    )

    # Remove helper join column
    merged_df.drop(columns=['submission_name'], inplace=True)

    # Optional: move accession columns next to sample_name
    insert_after = 'sample_name'
    base_cols = merged_df.columns.tolist()
    insertion_index = base_cols.index(insert_after) + 1
    for col in ['biosample_accession', 'sra_accession', 'genbank_accession'][::-1]:
        merged_col = merged_df.pop(col)
        merged_df.insert(insertion_index, col, merged_col)

    # Write to Excel
    merged_df.to_excel(params["output"], index=False)
    print(f"Final Excel file written to: {params["output"]}")


if __name__ == '__main__':
    main()
