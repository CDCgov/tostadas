#!/usr/bin/env python3

import argparse
import logging
import pandas as pd
from submission_helper import setup_logging  # assuming you already have this helper

def get_args():
    """Expected args from user for fetching reports"""
    parser = argparse.ArgumentParser(
        description="Add NCBI Accession IDs to the validated metadata file."
    )
    parser.add_argument('--metadata_tsv', required=True, help="Path to TSV metadata file with data for all samples")
    parser.add_argument('--submission_report', required=True, help="Path to submission_report.csv")
    parser.add_argument('--output', required=True, help="Path to final Excel file to write")
    return parser

def read_and_clean(path, sep=None):
    """
    Reads a CSV/TSV and removes repeated header rows.
    Automatically detects if rows are exact duplicates of the header row.
    """
    df = pd.read_csv(path, sep=sep, dtype=str, skip_blank_lines=True)
    df = df[~df.eq(df.columns).all(axis=1)]  # Drop repeated header rows
    return df

def log_missing_accessions(df, logger):
    accession_cols = ['biosample_accession', 'sra_accession']
    for col in accession_cols:
        missing_mask = df[col].isna() | ~df[col].astype(str).str.fullmatch(r'\w+')
        missing_spuids = df.loc[missing_mask, 'ncbi-spuid'].tolist()
        if missing_spuids:
            logger.info(
                f"No valid {col} found for {len(missing_spuids)} record(s) "
                f"(spuids): {', '.join(missing_spuids)}"
            )

def main():
    args = get_args().parse_args()
    params = vars(args)

    # Setup logging
    setup_logging(log_file='join_accessions_with_metadata.log',
                  level=logging.DEBUG)
    logger = logging.getLogger()

    # Load metadata TSV and submission report CSV, and clean both
    metadata_df = read_and_clean(params["metadata_tsv"], sep='\t')
    report_df = read_and_clean(params["submission_report"], sep=',')

    # Normalize casing and strip whitespace on join keys
    metadata_df['ncbi-spuid'] = metadata_df['ncbi-spuid'].str.strip().str.lower()
    report_df['spuid'] = report_df['spuid'].str.strip().str.lower()

    # Merge directly on spuid
    merged_df = metadata_df.merge(
        report_df[['spuid', 'biosample_accession', 'sra_accession']],
        how='left', left_on='ncbi-spuid', right_on='spuid'
    )

    # Drop redundant spuid column from report
    merged_df.drop(columns=['spuid'], inplace=True)

    # Log missing accessions
    log_missing_accessions(merged_df, logger)

    # Move accession columns next to ncbi-spuid
    insert_after = 'ncbi-spuid'
    for col in ['biosample_accession', 'sra_accession'][::-1]:
        col_data = merged_df.pop(col)
        merged_df.insert(merged_df.columns.get_loc(insert_after) + 1, col, col_data)

    # Write to Excel
    merged_df.to_excel(params["output"], index=False)
    logger.info(f'Final Excel file written to: {params["output"]}')


if __name__ == '__main__':
    main()
