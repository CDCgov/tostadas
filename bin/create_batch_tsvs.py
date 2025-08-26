#!/usr/bin/env python3

import pandas as pd
import argparse
import logging
import math
from submission_helper import setup_logging

def get_args():
    """
    Expected args from user for converting an updated metadata Excel file
    into multiple batched TSV files for GenBank submission.
    """
    parser = argparse.ArgumentParser(
        description="Convert updated Excel metadata to batched TSVs for GenBank submission."
    )
    parser.add_argument('--input', required=True, help="Path to the Excel file with accessions")
    parser.add_argument('--batch_size', type=int, default=20, help="Max number of samples per batch")
    parser.add_argument('--output_prefix', required=True, help="Prefix for output TSV files (e.g. '/path/to/batch')")
    return parser


def write_batched_tsvs(df, batch_size, output_prefix):
    """
    Write DataFrame into batched TSV files, with at most `batch_size` rows each.
    Returns a list of output file paths.
    """
    batched_paths = []
    total_rows = len(df)
    num_batches = math.ceil(total_rows / batch_size)
    for i in range(num_batches):
        batch_df = df.iloc[i * batch_size : (i + 1) * batch_size]
        batch_path = f"{output_prefix}_batch_{i+1}.tsv"
        batch_df.to_csv(batch_path, sep='\t', index=False)
        batched_paths.append(batch_path)
        logging.debug(f"Wrote {len(batch_df)} rows to {batch_path}")
    return batched_paths

def main():
    args = get_args().parse_args()
    params = vars(args)

    setup_logging(log_file='create_batch_tsvs.log', level=logging.DEBUG)

    logging.info(f"Reading Excel file: {params['input']}")
    df = pd.read_excel(params['input'], dtype=str)

    # Drop completely empty rows (which can sneak in from Excel)
    df.dropna(how='all', inplace=True)

    # Optionally, drop rows with missing sample_name
    if 'sample_name' in df.columns:
        df = df[df['sample_name'].notna() & df['sample_name'].str.strip().ne("")]
    else:
        logging.error("Missing required column: sample_name")
        return
    
    logging.debug("Filtered DataFrame:\n" + df.to_string())

    if df.empty:
        logging.error("Input Excel file is empty. Exiting.")
        return

    logging.info(f"Read {len(df)} rows. Splitting into batches of {params['batch_size']}")
    output_paths = write_batched_tsvs(df, params['batch_size'], params['output_prefix'])

    logging.info(f"Wrote {len(output_paths)} batched TSV files:")
    for path in output_paths:
        logging.info(f"  {path}")

if __name__ == '__main__':
    main()
