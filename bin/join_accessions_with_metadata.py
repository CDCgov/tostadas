#!/usr/bin/env python3

import argparse
import logging
import pandas as pd

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
    df = pd.read_csv(path, sep=sep, dtype=str, skip_blank_lines=True, keep_default_na=False)
    df = df[~df.eq(df.columns).all(axis=1)]  # Drop repeated header rows
    return df

def log_missing_accessions(df, logger):
    accession_cols = ['biosample_accession', 'sra_accession']
    for col in accession_cols:
        pattern = r'\w+(;\w+)*' if col == 'sra_accession' else r'\w+'
        missing_mask = df[col].isna() | ~df[col].astype(str).str.fullmatch(pattern)
        missing_spuids = df.loc[missing_mask, 'ncbi-spuid'].tolist()
        if missing_spuids:
            logger.info(
                f"No valid {col} found for {len(missing_spuids)} record(s) "
                f"(spuids): {', '.join(missing_spuids)}"
            )

def merge_accessions(metadata_df, report_df):
    """Return one row per metadata sample, preserving identifiers and accessions.

    Multiple SRA runs are stored as distinct, sorted, semicolon-separated
    accessions. Detailed run/status rows remain in submission_report.csv.
    Existing SRA accessions must be a subset of any nonempty reported set;
    missing reports preserve prior values instead of erasing them.
    """
    metadata = metadata_df.copy()
    reports = report_df.copy()
    metadata['_accession_join_key'] = metadata['ncbi-spuid'].fillna('').str.strip()
    reports['_accession_join_key'] = reports['spuid'].fillna('').str.strip()
    keys = metadata['_accession_join_key']
    if keys.eq('').any() or keys.duplicated().any():
        raise ValueError('Metadata requires unique, nonblank ncbi-spuid values')
    if reports['_accession_join_key'].eq('').any():
        raise ValueError('Submission report contains an unidentified sample')
    unknown = set(reports['_accession_join_key']) - set(keys)
    if unknown:
        raise ValueError(f'Submission report identifiers absent from metadata: {sorted(unknown)}')
    accession_cols = ['biosample_accession', 'sra_accession']
    for col in accession_cols:
        if col not in metadata:
            metadata[col] = ''
    placeholders = {'', 'not provided', 'na', 'n/a', 'nan'}

    def accession_set(raw):
        if pd.isna(raw):
            return set()
        return {part.strip() for part in str(raw).split(';')
                if part.strip().lower() not in placeholders}

    # Collapse detailed report rows before merging: downstream GenBank
    # validation requires one unique metadata row per BioSample identifier.
    collapsed = []
    for key, rows in reports.groupby('_accession_join_key', sort=False):
        record = {'_accession_join_key': key}
        for col in accession_cols:
            values = set().union(*(accession_set(raw) for raw in rows[col]))
            if col == 'biosample_accession' and len(values) > 1:
                raise ValueError(f'Conflicting BioSample accessions for {key!r}: {sorted(values)}')
            record[col] = ';'.join(sorted(values))
        collapsed.append(record)
    reports = pd.DataFrame(collapsed, columns=['_accession_join_key'] + accession_cols)
    merged = metadata.merge(reports, how='left', on='_accession_join_key',
                            suffixes=('', '_reported'), validate='one_to_one', sort=False)
    for col in accession_cols:
        reported = merged.pop(col + '_reported')
        resolved = []
        for index, raw in merged[col].items():
            old = accession_set(raw)
            new = accession_set(reported.loc[index])
            if (col == 'biosample_accession' and len(old) > 1) or (old and new and not old.issubset(new)):
                sample = merged.loc[index, 'ncbi-spuid']
                raise ValueError(f'Existing {col} conflicts with report for: {sample!r}')
            resolved.append(';'.join(sorted(new or old)))
        merged[col] = resolved
    return merged.drop(columns=['_accession_join_key'])


def main():
    args = get_args().parse_args()
    params = vars(args)

    # Setup logging
    logging.basicConfig(filename='join_accessions_with_metadata.log', level=logging.DEBUG)
    logger = logging.getLogger()

    # Load metadata TSV and submission report CSV, and clean both
    metadata_df = read_and_clean(params["metadata_tsv"], sep='\t')
    report_df = read_and_clean(params["submission_report"], sep=',')

    merged_df = merge_accessions(metadata_df, report_df)

    # Log missing accessions
    log_missing_accessions(merged_df, logger)

    # Move accession columns next to ncbi-spuid
    insert_after = 'ncbi-spuid'
    for col in ['biosample_accession', 'sra_accession'][::-1]:
        col_data = merged_df.pop(col)
        merged_df.insert(merged_df.columns.get_loc(insert_after) + 1, col, col_data)

    # Write to Excel with extra header line above the column headers
    with pd.ExcelWriter(params["output"], mode='w', engine='openpyxl') as writer:
        # First row for extra info
        extra_info = pd.DataFrame([["NCBI submission report"]])
        extra_info.to_excel(writer, index=False, header=False, startrow=0)
        
        # Then write your real DataFrame starting from row 1
        merged_df.to_excel(writer, index=False, startrow=1)

    logger.info(f'Final Excel file written to: {params["output"]}')

if __name__ == '__main__':
    main()
