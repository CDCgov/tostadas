#!/usr/bin/env python3
"""Combine NCBI reports using the identifiers in validated metadata."""
import argparse
from pathlib import Path

import pandas as pd

DATABASES = ('biosample', 'sra', 'genbank')
COLUMNS = ['batch_id', 'submission_id', 'spuid', 'spuid_namespace', 'submission_status'] + [
    f'{db}_{field}' for db in DATABASES
    for field in ('submission_id', 'status', 'accession', 'message')
] + ['tracking_location']


def value(raw):
    return '' if pd.isna(raw) else str(raw).strip()


def identifier_maps(metadata):
    """SRA identifiers need not resemble their BioSample identifiers."""
    if 'ncbi-spuid' not in metadata:
        raise ValueError('Validated metadata is missing ncbi-spuid')
    biosample = {}
    sra = {}
    for _, row in metadata.iterrows():
        key = value(row['ncbi-spuid'])
        if not key or key in biosample:
            raise ValueError(f'Blank or duplicate BioSample identifier in metadata: {key!r}')
        biosample[key] = key
        sra_key = value(row.get('ncbi-spuid-sra', ''))
        if sra_key:
            if sra_key in sra:
                raise ValueError(f'Duplicate SRA identifier in metadata: {sra_key!r}')
            sra[sra_key] = key
    # GenBank XML generation explicitly uses this suffix; SRA identifiers
    # remain arbitrary and are mapped only from their metadata column.
    genbank = {f'{key}-GB': key for key in biosample}
    return {'biosample': biosample, 'sra': sra, 'genbank': genbank}


def report_database(row):
    # The parser supplies database-specific fields from Action.target_db. Paths
    # include arbitrary user filenames and cannot identify the database safely.
    matches = [db for db in DATABASES if any(
        value(row.get(f'{db}_{field}', '')) for field in ('status', 'accession', 'message')
    )]
    if len(matches) != 1:
        raise ValueError('Report row has no unambiguous database-specific status/accession')
    return matches[0]


def aggregate_reports(input_files, metadata):
    maps = identifier_maps(metadata)
    combined_rows = []
    for filename in input_files:
        frame = pd.read_csv(filename, dtype=str, keep_default_na=False)
        groups = {}
        for _, row in frame.iterrows():
            db = report_database(row)
            spuid = value(row.get('spuid', ''))
            if spuid not in maps[db]:
                raise ValueError(
                    f'{filename}: {db} report identifier {spuid!r} has no unique metadata match; '
                    'inspect the report before combining accessions'
                )
            key = maps[db][spuid]
            group = groups.setdefault(key, {name: [] for name in DATABASES})
            record = {name: value(raw) for name, raw in row.items()}
            if record not in group[db]:
                group[db].append(record)

        for key, group in groups.items():
            # More than one SRA run per sample is valid. Competing BioSample
            # results must be reconciled explicitly instead of selecting a row.
            for db in ('biosample', 'genbank'):
                if len(group[db]) > 1:
                    raise ValueError(f'{filename}: conflicting {db} reports for {key!r}')
            biosample = group['biosample'][0] if group['biosample'] else {}
            genbank = group['genbank'][0] if group['genbank'] else {}
            for sra in group['sra'] or [{}]:
                preferred = biosample or sra or genbank
                combined = dict.fromkeys(COLUMNS, '')
                combined.update(batch_id=Path(filename).stem, spuid=key)
                for field in ('submission_id', 'spuid_namespace', 'submission_status', 'tracking_location'):
                    combined[field] = preferred.get(field, '')
                for db, record in (('biosample', biosample), ('sra', sra), ('genbank', genbank)):
                    combined[f'{db}_submission_id'] = record.get('submission_id', '')
                    for field in ('status', 'accession', 'message'):
                        combined[f'{db}_{field}'] = record.get(f'{db}_{field}', '')
                combined_rows.append(combined)
    return pd.DataFrame(combined_rows, columns=COLUMNS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--metadata_tsv', required=True)
    parser.add_argument('report_csvs', nargs='*')
    args = parser.parse_args()
    metadata = pd.read_csv(args.metadata_tsv, sep='\t', dtype=str, keep_default_na=False)
    aggregate_reports(args.report_csvs, metadata).to_csv('submission_report.csv', index=False)


if __name__ == '__main__':
    main()
