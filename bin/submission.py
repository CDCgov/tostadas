#!/usr/bin/env python3
import os
import argparse
import logging
from submission_helper import SubmissionConfigParser, FTPClient, SFTPClient, setup_logging

def get_args():
	""" Expected args from user and default values associated with them
		"""
		# initialize parser
	parser = argparse.ArgumentParser(
		description="Upload all prepared submissions under a folder to NCBI FTP/SFTP"
	)
	parser.add_argument("--submission_folder", required=True,
				   help="Top-level folder containing biosample/, sra/, genbank/ subfolders")
	parser.add_argument("--submission_name",
				   help="Name of the batch")
	parser.add_argument("--config_file", required=True,
				   help="Your same NCBI creds/config YAML")
	parser.add_argument("--identifier", required=True,
				   help="Original metadata file prefix as unique identifier for NCBI FTP site folder name")
	parser.add_argument("--submission_mode", choices=['ftp','sftp'], default='ftp')
	parser.add_argument("--test", action="store_true",
				   help="Upload under Test instead of Production")
	parser.add_argument("--send_email", required=False, 
				   help="Whether to send the ASN.1 file after running table2asn", action="store_const", default=False, const=True)
	parser.add_argument("--dry_run", action="store_true", 
				   help="Print what would be uploaded but don't connect or transfer files")
	return parser

def main_submit():
	args = get_args().parse_args()
	params = vars(args)
	
	setup_logging(log_file=f'{params["submission_folder"]}/submission.log', level=logging.DEBUG)

	# load parameters and credentials
	config = SubmissionConfigParser(params).load_config()
	client = SFTPClient(config) if params['submission_mode']=='sftp' else FTPClient(config)
	root = params['submission_folder']
	mode = 'Test' if params['test'] else 'Production'

	# Loop through all the repositories in the batch folder and submit them
	for dirpath, _, files in os.walk(root):
		# Only consider directories that have both submission.xml and submit.ready
		if dirpath == root:
			continue # Submission files are never directly under top folder
		if 'submission.xml' in files and 'submit.ready' in files:
			# Compute relative path from root, e.g. "biosample" or "sra/illumina"
			rel = os.path.relpath(dirpath, root)             
			# Split into [database] or [database, platform]
			parts = rel.split(os.sep)
			database = parts[0]                               
			platform = parts[1] if len(parts) > 1 else None  
			# Build a “flattened” remote base folder: <identifier>_<submission_name>_<database>[_<platform>]
			base_folder = f"{params['identifier']}_{params['submission_name']}_{database}"
			if platform:
				base_folder += f"_{platform}"
			# Final remote directory: submit/<Test|Production>/<that_flattened_folder>
			remote_dir = f"submit/{mode}/{base_folder}"
			if params['dry_run']:
				logging.info(f"[DRY-RUN] Would connect to {params['submission_mode'].upper()} and upload to: {remote_dir}")
				print(f"[DRY-RUN] Would connect to {params['submission_mode'].upper()} and upload to: {remote_dir}")
				for fname in files:
					local = os.path.join(dirpath, fname)
					logging.info(f"[DRY-RUN] Would upload {local} → {remote_dir}/{fname}")
					print(f"[DRY-RUN] Would upload {local} → {remote_dir}/{fname}")
			else:
				client.connect()
				client.make_dir(remote_dir)
				client.change_dir(remote_dir)
				for fname in files:
					local = os.path.join(dirpath, fname)
					client.upload_file(local, fname)
				client.close()
		# todo: add an elif for genbank email/manual submissions 
		else:
			print(f"[SKIP] {dirpath} does not contain both submission.xml and submit.ready")


if __name__=="__main__":
	main_submit()
