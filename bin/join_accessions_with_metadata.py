#!/usr/bin/env python3

import re
import pandas as pd
import argparse
import logging
from submission_helper import setup_logging

def get_args():
    """Expected args from user for fetching reports"""
    parser = argparse.ArgumentParser(
        description="Add NCBI Accession IDs to the validated metadata file."
    )
    parser.add_argument('--metadata_tsv', required=True, help="Path to TSV metadata file with data for all samples")
    parser.add_argument('--submission_report', required=True, help="Path to submission_report.csv")
    parser.add_argument('--output', required=True, help="Path to final Excel file to write")
    return parser

def extract_sample_matches(report_df, metadata_df):
    """
    For each row in the report, find a sample_name from metadata that appears as a substring
    of submission_name. Case-insensitive. Returns a list of matched rows.
    """
    sample_names = metadata_df['sample_name'].str.lower().tolist()
    matched_rows = []
    for _, row in report_df.iterrows():
        submission_name = str(row['submission_name']).lower()
        matched_sample = next((s for s in sample_names if s in submission_name), None)
        if matched_sample:
            matched_rows.append({
                'sample_name': matched_sample,
                'biosample_accession': row.get('biosample_accession'),
                'sra_accession': row.get('sra_accession'),
                'genbank_accession': row.get('genbank_accession')
            })
    return pd.DataFrame(matched_rows)

def log_missing_accessions(df, logger):
    accession_cols = ['biosample_accession', 'sra_accession', 'genbank_accession']
    for col in accession_cols:
        # Find rows where accession is missing, NaN, or non-alphanumeric
        missing_mask = df[col].isna() | ~df[col].astype(str).str.fullmatch(r'\w+')
        missing_samples = df.loc[missing_mask, 'sample_name'].tolist()
        if missing_samples:
            logging.info(
                f"No valid {col} found for {len(missing_samples)} sample(s): "
                + ", ".join(missing_samples)
            )

def main():
    """
    """
    args = get_args().parse_args()
    params = vars(args)

    # Setup logging
    setup_logging(log_file='join_accessions_with_metadata.log',
                  level=logging.DEBUG)

    # Load metadata TSV and submission report CSV
    metadata_df = pd.read_csv(params["metadata_tsv"], sep='\t', dtype=str)
    report_df = pd.read_csv(params["submission_report"], dtype=str)

    # Preserve original sample name capitalization
    metadata_df['original_sample_name'] = metadata_df['sample_name']

    # Normalize casing
    metadata_df['sample_name'] = metadata_df['sample_name'].str.strip().str.lower()
    report_df['submission_name'] = report_df['submission_name'].str.strip().str.lower()

    # Build accession dataframe by matching sample_name as substring of submission_name
    accessions_df = extract_sample_matches(report_df, metadata_df)

    # Merge
    merged_df = metadata_df.merge(accessions_df, how='left', on='sample_name')

    # Restore original capitalization of sample_name
    merged_df['sample_name'] = merged_df['original_sample_name']
    merged_df.drop(columns=['original_sample_name'], inplace=True)

    # Log missing accessions
    log_missing_accessions(merged_df, logging.getLogger())

    # Move accession columns next to sample_name
    insert_after = 'sample_name'
    for col in ['biosample_accession', 'sra_accession', 'genbank_accession'][::-1]:
        col_data = merged_df.pop(col)
        merged_df.insert(merged_df.columns.get_loc(insert_after) + 1, col, col_data)

    # Write to Excel
    merged_df.to_excel(params["output"], index=False)
    logging.info(f"Final Excel file written to: {params["output"]}")


if __name__ == '__main__':
    main()
