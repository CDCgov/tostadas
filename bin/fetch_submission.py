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
    os.makedirs(params["submission_folder"], exist_ok=True)

    log_file_path = os.path.join(params["submission_folder"], "fetch_submission.log")
    setup_logging(log_file=log_file_path, level=logging.DEBUG)

    logging.info("Started fetching reports.")

    # Load submission configuration
    config = SubmissionConfigParser(params).load_config()
    mode = "Test" if params["test"] else "Production"

    databases = []
    # Check whether user submitted to BioSample/SRA
    for db in ["biosample", "sra"]:
        db_path = os.path.join(params["submission_folder"], db)
        if os.path.isfile((os.path.join(db_path,"submission.xml"))):
            databases.append(db)
    # Check whether user submitted to Genbank (could be top level if SARS or flu, or in sample subdirs)
    genbank_path = os.path.join(params["submission_folder"], "genbank")
    if os.path.exists(genbank_path):
        # Check if submission.xml is directly in genbank/ (i.e., for sars or flu)
        if os.path.isfile(os.path.join(genbank_path, "submission.xml")):
            databases.append("genbank")
        else:
            # Look for submission.xml in subdirectories
            for subdir in os.listdir(genbank_path):
                full_subdir_path = os.path.join(genbank_path, subdir)
                if os.path.isdir(full_subdir_path) and os.path.isfile(os.path.join(full_subdir_path, "submission.xml")):
                    databases.append("genbank")
                    break # Assume for now all samples were submitted via ftp if one found

    # Run a dry-run if asked
    if params["dry_run"]:
        logging.info(f"[DRY-RUN] Would fetch submission reports for databases: {databases} in {mode}.")
        print(f"[DRY-RUN] Would fetch submission reports for databases: {databases} in {mode}.")
        return

    # Perform actual fetch
    reports_fetched = fetch_all_reports(
        #databases=params["databases"],
        databases=databases,
        outdir=params["submission_folder"],
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
