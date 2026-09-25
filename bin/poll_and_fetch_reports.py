#!/usr/bin/env python3
import os
import argparse
import logging
import time
from submission_helper import (
    SubmissionConfigParser,
    Submission,
    fetch_all_reports,
    parse_and_save_reports,
    get_remote_submission_dir,
    is_report_complete,
    parse_report_xml_to_df,
    setup_logging,
)


def get_args():
    """Expected args from user for polling and fetching reports."""
    parser = argparse.ArgumentParser(
        description="Poll NCBI FTP for report.xml with exponential backoff, then parse results."
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
    parser.add_argument("--initial_interval", type=int, default=30,
                        help="Initial polling interval in seconds (default: 30).")
    parser.add_argument("--max_interval", type=int, default=120,
                        help="Maximum polling interval in seconds (default: 120).")
    parser.add_argument("--timeout", type=int, default=1800,
                        help="Total timeout in seconds (default: 1800).")
    return parser


def discover_databases(submission_folder):
    """Discover which databases have submission.xml files."""
    databases = []
    for db in ["biosample", "sra"]:
        db_path = os.path.join(submission_folder, db)
        if os.path.isfile(os.path.join(db_path, "submission.xml")):
            databases.append(db)
    genbank_path = os.path.join(submission_folder, "genbank")
    if os.path.exists(genbank_path):
        if os.path.isfile(os.path.join(genbank_path, "submission.xml")):
            databases.append("genbank")
        else:
            for subdir in os.listdir(genbank_path):
                full_subdir_path = os.path.join(genbank_path, subdir)
                if os.path.isdir(full_subdir_path) and os.path.isfile(os.path.join(full_subdir_path, "submission.xml")):
                    databases.append("genbank")
                    break
    return databases


def resolve_db_targets(databases, submission_folder):
    """Return a list of (db, platform, local_output_path) tuples to poll."""
    targets = []
    for db in databases:
        if db == "genbank":
            continue  # skip genbank for now (same as fetch_submission.py)
        if db == "sra":
            base_outdir = os.path.join(submission_folder, db)
            has_both = all(
                os.path.isdir(os.path.join(base_outdir, p)) for p in ["illumina", "nanopore"]
            )
            platforms = ["illumina", "nanopore"] if has_both else [None]
        else:
            platforms = [None]
        for platform in platforms:
            if db == "sra" and platform:
                local_output_path = os.path.join(submission_folder, db, platform)
            else:
                local_output_path = os.path.join(submission_folder, db)
            targets.append((db, platform, local_output_path))
    return targets


def poll_and_fetch(params, config):
    """Poll NCBI FTP with exponential backoff until reports reach terminal status or timeout."""
    mode = "Test" if params["test"] else "Production"
    databases = discover_databases(params["submission_folder"])
    targets = resolve_db_targets(databases, params["submission_folder"])

    if not targets:
        logging.warning("No databases found with submission.xml. Nothing to poll.")
        return

    interval = params["initial_interval"]
    max_interval = params["max_interval"]
    timeout = params["timeout"]
    start_time = time.time()

    # Track which targets still need a terminal report
    pending = {i: None for i in range(len(targets))}  # index -> last fetched path or None
    reports_fetched = {db: [] for db in databases}

    attempt = 0
    while pending and (time.time() - start_time) < timeout:
        attempt += 1
        elapsed = int(time.time() - start_time)
        logging.info(f"Poll attempt {attempt} (elapsed {elapsed}s, interval {interval}s, {len(pending)} target(s) pending)")

        # Sleep before polling (except we still check timeout after sleep)
        time.sleep(interval)
        if (time.time() - start_time) >= timeout:
            logging.warning("Timeout reached during sleep interval.")
            break

        # Poll each pending target
        resolved = []
        for idx in list(pending.keys()):
            db, platform, local_output_path = targets[idx]
            report_local_path = os.path.join(local_output_path, "report.xml")
            remote_subdir = get_remote_submission_dir(
                params["identifier"], params["batch_id"], db, platform
            )
            remote_dir = f"submit/{mode}/{remote_subdir}"

            # Create a fresh FTP/SFTP connection each iteration
            submission = Submission(
                parameters=params,
                submission_config=config,
                outdir=local_output_path,
                submission_mode=params["submission_mode"],
                submission_dir=mode,
                type=db,
                sample=None,
                identifier=params["identifier"],
            )

            try:
                submission.client.connect()
                submission.client.change_dir(remote_dir)
            except Exception as e:
                logging.warning(f"Could not access {remote_dir} for {db} ({platform or 'default'}): {e}")
                try:
                    submission.client.close()
                except Exception:
                    pass
                continue

            try:
                report_path = submission.fetch_report(remote_dir, report_local_path)
            except Exception as e:
                logging.warning(f"Error fetching report for {db} ({platform or 'default'}): {e}")
                report_path = None
            finally:
                try:
                    submission.client.close()
                except Exception:
                    pass

            if not report_path:
                logging.info(f"Report not yet available for {db} ({platform or 'default'})")
                continue

            # Report downloaded — check if terminal
            is_complete, status_summary = is_report_complete(report_path)
            logging.info(f"Report for {db} ({platform or 'default'}): complete={is_complete}, statuses={status_summary}")

            if is_complete:
                reports_fetched[db].append(report_path)
                resolved.append(idx)
            else:
                # Keep track of partial report path in case we time out
                pending[idx] = report_path

        for idx in resolved:
            del pending[idx]

        # Increase interval with 1.5x backoff, capped at max_interval
        interval = min(int(interval * 1.5), max_interval)

    # Handle any remaining pending targets (timeout reached with partial reports)
    if pending:
        logging.warning(f"Timeout reached with {len(pending)} target(s) still pending.")
        for idx, partial_path in pending.items():
            db, platform, local_output_path = targets[idx]
            if partial_path and os.path.exists(partial_path):
                logging.warning(f"Using partial report for {db} ({platform or 'default'}): {partial_path}")
                reports_fetched[db].append(partial_path)
            else:
                logging.warning(f"No report fetched for {db} ({platform or 'default'}) before timeout.")

    # Parse and save all fetched reports
    parse_and_save_reports(reports_fetched, params["submission_folder"], params["batch_id"])
    logging.info(f"Reports parsed and saved for batch: {params['batch_id']}")


def main():
    """Main entry point for poll-and-fetch."""
    args = get_args().parse_args()
    params = vars(args)

    os.makedirs(params["submission_folder"], exist_ok=True)
    log_file_path = os.path.join(params["submission_folder"], "fetch_submission.log")
    setup_logging(log_file=log_file_path, level=logging.DEBUG)

    logging.info("Started poll_and_fetch_reports.")
    logging.info(f"Polling params: initial_interval={params['initial_interval']}s, "
                 f"max_interval={params['max_interval']}s, timeout={params['timeout']}s")

    config = SubmissionConfigParser(params).load_config()

    databases = discover_databases(params["submission_folder"])
    mode = "Test" if params["test"] else "Production"

    if params["dry_run"]:
        logging.info(f"[DRY-RUN] Would poll for submission reports for databases: {databases} in {mode}.")
        print(f"[DRY-RUN] Would poll for submission reports for databases: {databases} in {mode}.")
        return

    poll_and_fetch(params, config)


if __name__ == "__main__":
    main()
