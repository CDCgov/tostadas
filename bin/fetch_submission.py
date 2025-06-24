#!/usr/bin/env python3
import os
import argparse
import logging
from submission_helper import SubmissionConfigParser, fetch_all_reports, parse_and_save_reports, setup_logging

def get_args():
    """Expected args from user for fetching reports"""
    parser = argparse.ArgumentParser(
        description="Fetch all reports for a batch submission from NCBI FTP/SFTP."
    )
    parser.add_argument("--submission_folder", required=True,
                        help="Top-level submission directory containing database subfolders.")
    parser.add_argument("--config_file", required=True,
                        help="Path to the NCBI configuration YAML file.")
    parser.add_argument("--identifier", required=True,
                        help="Original metadata file prefix (identifier for the NCBI submission).")
    parser.add_argument("--batch_id", required=True,
                        help="Batch ID for submission (used for naming files).")
    parser.add_argument("--databases", required=True, nargs="+",
                        help="List of databases to fetch reports from (e.g., biosample sra genbank).")
    parser.add_argument("--submission_mode", choices=["ftp", "sftp"], required=False, default="ftp",
                        help="Connect via FTP or SFTP (default: ftp).")
    parser.add_argument("--test", action="store_true",
                        help="True if submitting to Test, false if submitting to Production")
    parser.add_argument("--dry_run", action="store_true",
                        help="Perform a dry run (don't fetch files).")
    return parser

def main_fetch():
    """Main method for fetching submission reports."""
    args = get_args().parse_args()
    params = vars(args)

    # Setup logging
    setup_logging(log_file=f'{params["submission_folder"]}/fetch_submission.log',
                  level=logging.DEBUG)

    # Load submission configuration
    config = SubmissionConfigParser(params).load_config()
    mode = "Test" if params["test"] else "Production"

    if params["dry_run"]:
        logging.info(f"[DRY-RUN] Would fetch submission reports for databases: {params['databases']} in {mode}.")
        print(f"[DRY-RUN] Would fetch submission reports for databases: {params['databases']} in {mode}.")
        return

    # Perform actual fetch
    reports_fetched = fetch_all_reports(
        databases=params["databases"],
        output_dir=params["submission_folder"],
        config_dict=config,
        parameters=params,
        submission_dir=mode,
        submission_mode=params["submission_mode"],
        identifier=params["identifier"],
        batch_id=params["batch_id"],
        timeout=60,
    )

    # Parse and save the results
    parse_and_save_reports(reports_fetched, params["submission_folder"], params["batch_id"])
    logging.info(f"Reports parsed and saved for batch: {params['batch_id']}")

if __name__ == "__main__":
    main_fetch()
