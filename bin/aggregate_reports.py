#!/usr/bin/env python3
import pandas as pd
from pathlib import Path
import sys

# Usage: python aggregate_reports.py batch_*.csv
# Output: submission_report.csv

def main():
    input_files = sys.argv[1:]
    if not input_files:
        print("Usage: python aggregate_reports.py <batch_*.csv>")
        sys.exit(1)

    all_rows = []

    for f in input_files:
        batch_path = Path(f)
        batch_id = batch_path.stem  # e.g. "batch_3"
        df = pd.read_csv(f, dtype=str).fillna("")

        # Split into biosample and sra rows
        biosample_df = df[df["tracking_location"].str.contains("biosample", case=False)]
        sra_df = df[df["tracking_location"].str.contains("sra", case=False)]

        # Merge by row order (assume they align one-to-one within the same batch file)
        biosample_df = biosample_df.reset_index(drop=True)
        sra_df = sra_df.reset_index(drop=True)

        max_len = max(len(biosample_df), len(sra_df))
        biosample_df = biosample_df.reindex(range(max_len)).fillna("")
        sra_df = sra_df.reindex(range(max_len)).fillna("")

        # Build combined rows
        for i in range(max_len):
            b = biosample_df.iloc[i]
            s = sra_df.iloc[i]

            combined = {
                "batch_id": batch_id,
                "submission_id": b.get("submission_id","") or s.get("submission_id",""),
                "spuid": b.get("spuid",""),
                "spuid_namespace": b.get("spuid_namespace",""),
                "submission_status": b.get("submission_status","") or s.get("submission_status",""),
                "biosample_submission_id": b.get("submission_id",""),
                "biosample_status": b.get("biosample_status",""),
                "biosample_accession": b.get("biosample_accession",""),
                "biosample_message": b.get("biosample_message",""),
                "sra_submission_id": s.get("submission_id",""),
                "sra_status": s.get("sra_status",""),
                "sra_accession": s.get("sra_accession",""),
                "sra_message": s.get("sra_message",""),
                "genbank_submission_id": b.get("genbank_submission_id","") or s.get("genbank_submission_id",""),
                "genbank_status": b.get("genbank_status","") or s.get("genbank_status",""),
                "genbank_accession": b.get("genbank_accession","") or s.get("genbank_accession",""),
                "genbank_message": b.get("genbank_message","") or s.get("genbank_message",""),
                "tracking_location": b.get("tracking_location","") or s.get("tracking_location","")
            }
            all_rows.append(combined)

    final_df = pd.DataFrame(all_rows)
    final_df.to_csv("submission_report.csv", index=False)

if __name__ == "__main__":
    main()
