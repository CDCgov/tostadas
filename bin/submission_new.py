#!/usr/bin/env python3

import os
import sys
import shutil
import tempfile
from datetime import datetime
import argparse
import yaml
import json
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom  # Import minidom for pretty-printing
import math  # Required for isnan check
import csv
import time
import shlex
import subprocess
import pandas as pd
from abc import ABC, abstractmethod
import paramiko
import ftplib
from nameparser import HumanName
from zipfile import ZipFile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

def get_compound_extension(filename):
    """Return the full extension (up to 2 suffixes) of a file, like '.fastq.gz'."""
    parts = os.path.basename(filename).split('.')
    if len(parts) >= 3:
        return '.' + '.'.join(parts[-2:])  # e.g., '.fastq.gz'
    elif len(parts) == 2:
        return '.' + parts[-1]             # e.g., '.gz' or '.fq'
    else:
        return ''  # No extension
		
def get_accessions(sample, report_df):
	""" Returns a dict with available accessions for the input sample
	"""
	accessions = {
		'biosample': None,
		'sra': None,
		'genbank': None
	}
	sample_row = report_df[report_df['submission_name'] == sample]
	if not sample_row.empty:
		accessions['biosample'] = sample_row['biosample_accession'].values[0] if 'biosample_accession' in sample_row else None
		accessions['sra'] = sample_row['sra_accession'].values[0] if 'sra_accession' in sample_row else None
		accessions['genbank'] = sample_row['genbank_accession'].values[0] if 'genbank_accession' in sample_row else None
	return accessions

def submission_main():
	""" Main for initiating submission steps
	"""
	# Get all parameters from argparse
	parameters_class = GetParams()
	parameters = parameters_class.parameters
	
	# Get list of all databases to submit to (or update)
	databases = [db for db in parameters if parameters[db] and db in ['biosample', 'sra', 'genbank', 'gisaid']]
	print(f"Submission requested for {','.join([str(i) for i in databases])}")

	# Get the submission config file dictionary
	config_parser = SubmissionConfigParser(parameters)
	config_dict = config_parser.load_config()
	
	# Get the batch ID 
	batch_id = parameters['metadata_file'].split('.')[0].split('/')[-1]

	# Set output directory
	output_dir = f"{parameters['output_dir']}/{batch_id}"
	
	# Read in metadata file
	try:
		metadata_df = pd.read_csv(parameters['metadata_file'], sep='\t')
	except Exception as e:
		raise ValueError(f"Failed to load metadata file: {parameters['metadata_file']}. Error: {e}")
	
	# Initialize the Sample objects 
	samples = []
	for sample_str in parameters['sample']:
		sample_dict = dict(item.split('=') for item in sample_str.split(','))
		sample = Sample(
			sample_id=sample_dict['sample_id'],
			batch_id=batch_id,
			fastq1=sample_dict.get('fq1'),
			fastq2=sample_dict.get('fq2'),
			nanopore=sample_dict.get('nanopore'),
			species=parameters['species'],
			databases=databases,
			fasta_file=sample_dict.get('fasta'),
			annotation_file=sample_dict.get('gff')
		)
		samples.append(sample)

	# Set the submission directory (test or production)
	if parameters['test']:
		submission_dir = 'Test'
	else:
		submission_dir = 'Production'
	
	# Initial a dictionary to hold accessions if updating
	accessions_dict = {'biosample':None, 'sra':None, 'genbank':None}

	# Get workflow
	# todo: error messaging here should probably be part of NF not this script
	if parameters["submit"] and parameters["update"]:
		raise ValueError("Only one of 'submit' or 'update' can be True, not both.")

	if parameters["submit"]:
		workflow = "submit"
	elif parameters["update"]:
		workflow = "update"
	elif parameters["fetch"]:
		workflow = "fetch"
	else:
		raise ValueError("Please specify a workflow (submit, update, or fetch) to proceed.")
	print(f"Workflow requested: {workflow}")

	# Beginning of fetch workflow
	if workflow == 'fetch':
		# Fetch the reports from NCBI's ftp/sftp site
		start_time = time.time()
		timeout = 60  # time out after 60 seconds  
		report_fetched = {db: False for db in ['biosample', 'sra', 'genbank']}  # Track fetched status for each db
		while time.time() - start_time < timeout:
			# Try fetching reports for all applicable databases
			for db in databases:
				if not report_fetched[db]:  # Only attempt fetching if the report has not been fetched
					print(f"Fetching report for {db}")
					# Instantiate a Submission object for this database type
					submission = Submission(sample, parameters, config_dict, f"{parameters['output_dir']}/{db}", parameters['submission_mode'], submission_dir, db)
					for sample in samples:
						fetched_path = submission.fetch_report()
						if fetched_path:
							print(f"Report for {db} successfully fetched or already exists.")
							report_fetched[db] = True
						else:
							print(f"Failed to fetch report for {db}, retrying...")
							time.sleep(3)  # Because spamming servers isn't nice

			# Exit the loop if all reports have been fetched
			if all(report_fetched.values()):
				print("All reports successfully fetched.")
				break
		else:
			# If the while loop completes without fetching all reports
			print("Timeout occurred while trying to fetch all reports.")
		
		# Loop over submission dbs to parse the report.xmls
		all_reports = pd.DataFrame()
		for  db in databases:
			report_xml_file = f"{parameters['output_dir']}/{db}/report.xml"
			df = submission.parse_report_to_df(report_xml_file)
			all_reports = pd.concat([all_reports, df], ignore_index=True)
		report_csv_file = os.path.join(parameters['output_dir'], f"{batch_id}.csv")
		try:
			all_reports.to_csv(report_csv_file, mode='w', header=True, index=False)
			print(f"Report table updated at: {report_csv_file}")
		except Exception as e:
			raise ValueError(f"Failed to save CSV file: {report_csv_file}. Error: {e}")
		# End of the fetch workflow

	# Beginning of submit and update workflows	
	else:
		# Load the report file to get the accession IDs if user is updating a submission
		if workflow == 'update':
			report_file = parameters["submission_report"]
			try:
				report_df =  pd.read_csv(report_file)
			except Exception as e:
				raise ValueError(f"Failed to load CSV file: {report_file}. Error: {e}")
			accessions_dict = get_accessions(sample.sample_id, report_df)
			# Exit gracefully if accession IDs not found (cannot push update to NCBI without an accession ID)
			print(f"Updated requested for databases {', '.join(databases)}")
			if any(accessions_dict.get(db) is None for db in databases):
				print(f"Error: Missing accession for one of more of {', '.join(databases)}. Exiting update workflow.")
				sys.exit(1) 
			else:
				print(f"Accessions found for {', '.join(accessions_dict.keys())}")
				print(f"Accessions: {', '.join(f'{k}: {v}' for k, v in accessions_dict.items())}")
				# Todo: this code requires the user to specify the exact database(s) they want to update

		# Run rest of the submission steps: Prep the files, submit, and fetch the report once
		if parameters['biosample']:
			biosample_submission = BiosampleSubmission(sample, parameters, config_dict, metadata_df, f"{parameters['output_dir']}/biosample", 
													parameters['submission_mode'], submission_dir, 'biosample', accessions_dict['biosample'])
			biosample_submission.init_xml_root() # Start the xml file
			for sample in samples:
				sample_metadata = metadata_df[metadata_df['sample_name'] == sample.sample_id]
				biosample_submission.add_sample(sample, sample_metadata) # Add samples data to xml file
			biosample_submission.finalize_xml() # Write the xml file
		
		if parameters['sra']:
			sra_submission = SRASubmission(sample, parameters, config_dict, metadata_df, f"{parameters['output_dir']}/sra",
										parameters['submission_mode'], submission_dir, 'sra', samples, accessions_dict['sra'])
			sra_submission.init_xml_root() # Start the xml file
			for sample in samples:
				sample_metadata = metadata_df[metadata_df['sample_name'] == sample.sample_id]
				sra_submission.add_sample(sample, sample_metadata) # Add samples data to xml file
			sra_submission.finalize_xml() # Write the xml file
		
		if parameters['genbank']:
			# Generates an XML if ftp_upload is True
			genbank_submission = GenbankSubmission(sample, parameters, config_dict, metadata_df, f"{parameters['output_dir']}/genbank/{parameters['submission_name']}",
												parameters['submission_mode'], submission_dir, 'genbank', accessions_dict['genbank'])

		# Submit all prepared submissions and fetch report once
		if parameters['biosample']:
			biosample_submission.submit()
		if parameters['sra']:
			sra_submission.submit()
		if parameters['genbank']:
			# If user is submitting via FTP
			if sample.ftp_upload:
				genbank_submission.prepare_files_ftp_submission() # Prep files and run table2asn
				genbank_submission.submit()
			else:
				# Otherwise, prepare manual submission
				genbank_submission.prepare_files_manual_submission() # Prep files and run table2asn
				# Send email if the user requests it
				if parameters['send_email']:
					genbank_submission.sendemail()
	# End of submit and update workflows
class GetParams:
	""" Class constructor for getting all necessary parameters (input args from argparse and hard-coded ones)
	"""
	def __init__(self):
		self.parameters = self.get_inputs()

	# read in parameters
	def get_inputs(self):
		""" Gets the user inputs from the argparse
		"""
		args = self.get_args().parse_args()
		parameters = vars(args)
		return parameters

	@staticmethod
	def get_args():
		""" Expected args from user and default values associated with them
		"""
		# initialize parser
		parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
									 description='Automate the process of batch uploading consensus sequences and metadata to databases of your choices')
		# required parameters (do not have default)
		parser.add_argument("--submission_name", help='Name of the submission',	required=True)	
		parser.add_argument("--config_file", help="Name of the submission onfig file",	required=True)
		parser.add_argument("--metadata_file", help="Name of the validated metadata batch tsv file", required=True)
		parser.add_argument("--submission_report", help="Path to submission report csv file", required=False, default="submission_report.csv")
		parser.add_argument("--species", help="Type of organism data", required=True)
		parser.add_argument('--submit', action='store_true', help='Run the full submission process')
		parser.add_argument('--fetch', action='store_true', help='Run the process to fetch and parse report')
		parser.add_argument('--update', action='store_true', help='Run the update process to submit new data')
		parser.add_argument('--sample', action='append', help='Comma-separated sample attributes')
		# optional parameters
		parser.add_argument("-o", "--output_dir", type=str, default='submission_outputs',
							help="Output Directory for final Files, default is current directory")
		parser.add_argument("--test", help="Whether to perform a test submission.", required=False,	action="store_const", default=False, const=True)
		parser.add_argument("--custom_metadata_file", help="JSON file defining custom metadata columns", required=False)
		parser.add_argument("--submission_mode", help="Whether to upload via ftp or sftp", required=False, default='ftp')
		parser.add_argument("--send_email", help="Whether to send the ASN.1 file after running table2asn", required=False,action="store_const",  default=False, const=True)
		parser.add_argument("--genbank", help="Optional flag to run Genbank submission", action="store_const", default=False, const=True)
		parser.add_argument("--biosample", help="Optional flag to run BioSample submission", action="store_const", default=False, const=True)
		parser.add_argument("--sra", help="Optional flag to run SRA submission", action="store_const", default=False, const=True)
		parser.add_argument("--gisaid", help="Optional flag to run GISAID submission", action="store_const", default=False, const=True)
		return parser
	
class SubmissionConfigParser:
	""" Class constructor to read in config file as dict
	"""
	def __init__(self, parameters):
		# Load submission configuration
		self.parameters = parameters
	def load_config(self):
		# Example: returns a dictionary with SFTP credentials, paths, etc.
		with open(self.parameters['config_file'], "r") as f:
			config_dict = yaml.load(f, Loader=yaml.BaseLoader) # Load yaml as str only
		if type(config_dict) is dict:
			for k, v in config_dict.items():
				# If GISAID submission, check that GISAID keys have values
				if self.parameters["gisaid"]:
					if k.startswith('GISAID') and not v:
						print("Error: There are missing GISAID values in the config file.", file=sys.stderr)
						sys.exit(1)					
				else:
					# If NCBI submission, check that non-GISAID keys have values (note: this only check top-level keys)
					if k.startswith('NCBI') and not v:
						print("Error: There are missing NCBI values in the config file.", file=sys.stderr)
						sys.exit(1)	
		else:	
			print("Error: Config file is incorrect. File must has a valid yaml format.", file=sys.stderr)
			sys.exit(1)
		return config_dict

class Sample:
	def __init__(self, sample_id, batch_id, species, databases, fastq1=None, fastq2=None, nanopore=None, fasta_file=None, annotation_file=None):
		self.sample_id = sample_id
		self.batch_id = batch_id
		self.fastq1 = fastq1
		self.fastq2 = fastq2
		self.nanopore = nanopore
		self.species = species
		self.databases = databases
		self.fasta_file = fasta_file
		self.annotation_file = annotation_file
		# ftp_upload is true if GenBank FTP submission is supported for that species, otherwise false
		self.ftp_upload = species in {"flu", "sars", "bacteria"} # flu, sars, bacteria currently support ftp upload to GenBank
		def __repr__(self):
			return f"Sample sample_id:{self.sample_id} batch_id:{self.batch_id} fastq1:{self.fastq1} fastq2:{self.fastq2} \
			nanopore:{self.nanopore} species:{self.species}"

class MetadataParser:
	def __init__(self, metadata_df, parameters):
		self.metadata_df = metadata_df
		self.parameters = parameters
		self.custom_columns = self.load_custom_columns()
	def load_custom_columns(self):
		"""
		Load custom metadata columns from the JSON file (for custom BS packages)
		"""
		json_file_path = self.parameters.get('custom_metadata_file')
		if not json_file_path:
			return []
		try:
			with open(json_file_path, 'r') as f:
				custom_metadata = json.load(f)
			custom_columns = [
				value.get('new_field_name', key).strip() or key.strip() # fall back to JSON key if new_field_name empty
				for key, value in custom_metadata.items()
			]
			return custom_columns
		except Exception as e:
			print(f"Error loading custom metadata file: {e}")
			return []

	def extract_top_metadata(self):
		columns = ['sequence_name', 'title', 'description', 'authors', 'ncbi-bioproject', 'ncbi-spuid_namespace', 'ncbi-spuid']  # Main columns
		available_columns = [col for col in columns if col in self.metadata_df.columns]
		return self.metadata_df[available_columns].to_dict(orient='records')[0] if available_columns else {}
	def extract_biosample_metadata(self):
		columns = ['strain','isolate','host_disease','host','collected_by','lat_lon','geo_loc_name','organism',
				   'sample_type','collection_date','isolation_source','host_age','host_sex', 'race','ethnicity']  # BioSample specific columns
		all_columns = columns + self.custom_columns # add custom columns to BioSample specific cols
		available_columns = [col for col in all_columns if col in self.metadata_df.columns]
		return self.metadata_df[available_columns].to_dict(orient='records')[0] if available_columns else {}
	def extract_sra_metadata(self):
		columns = ['illumina_sequencing_instrument','illumina_library_protocol','illumina_library_layout','illumina_library_selection',
				   'illumina_library_source','illumina_library_strategy','nanopore_library_layout','nanopore_library_protocol','nanopore_library_selection',
				   'nanopore_library_source','nanopore_library_strategy','nanopore_sequencing_instrument']  # SRA specific columns
		available_columns = [col for col in columns if col in self.metadata_df.columns]
		return self.metadata_df[available_columns].to_dict(orient='records')[0] if available_columns else {}
	def extract_genbank_metadata(self):
		columns = ['submitting_lab','submitting_lab_division','submitting_lab_address','publication_status','publication_title',
					'assembly_protocol','assembly_method','mean_coverage']  # Genbank specific columns
		available_columns = [col for col in columns if col in self.metadata_df.columns]
		return self.metadata_df[available_columns].to_dict(orient='records')[0] if available_columns else {}

# todo: this opens an ftp connection for every submission; would be better I think to open it once every x submissions?
class Submission:
	def __init__(self, sample, parameters, submission_config, output_dir, submission_mode, submission_dir, type):
		self.sample = sample
		self.parameters = parameters
		self.submission_config = submission_config
		self.output_dir = output_dir
		self.submission_mode = submission_mode
		self.submission_dir = submission_dir
		self.type = type
		self.client = self.get_client()
	def get_client(self):
		if self.submission_mode == 'sftp':
			return SFTPClient(self.submission_config)
		elif self.submission_mode == 'ftp':
			return FTPClient(self.submission_config)
		else:
			raise ValueError("Invalid submission mode: must be 'sftp' or 'ftp'")
	def fetch_report(self):
		""" Fetches report.xml from the host site folder submit/<Test|Production>/sample_database/"""
		self.client.connect()
		# Navigate to submit/<Test|Production>/<submission_db> folder
		self.client.change_dir(f"submit/{self.submission_dir}/{self.sample.sample_id}_{self.type}")
		# Check if report.xml exists and download it
		report_local_path = os.path.join(self.output_dir, 'report.xml')
		if os.path.exists(report_local_path):
			print(f"Report already exists locally: {report_local_path}")
			return report_local_path
		elif self.client.file_exists('report.xml'):
			print(f"Report found on server. Downloading to: {report_local_path}.")
			self.client.download_file('report.xml', report_local_path)
			return report_local_path # Report fetched, return its path
		else:
			print(f"No report found for submission {self.sample.sample_id}")
			return False # Report not found, need to try again
	def parse_report_to_df(self, report_path):
		"""
		Parses a report.xml file containing multiple samples.
		Returns a DataFrame with one row per action_id (i.e., per sample).
		"""
		reports = []
		try:
			tree = ET.parse(report_path)
			root = tree.getroot()
			submission_status = root.get("status", None)
			submission_id = root.get("submission_id", None)

			tracking_location_tag = root.find("Tracking/SubmissionLocation")
			tracking_location = tracking_location_tag.text if tracking_location_tag is not None else None

			for action in root.findall("Action"):
				action_id = action.get("action_id", None)
				sample_id = action_id  # or strip prefix if needed
				target_db = action.get("target_db", "").lower()
				report = {
					'submission_name': sample_id,
					'submission_status': submission_status,
					'submission_id': submission_id,
					'biosample_status': None,
					'biosample_accession': None,
					'biosample_message': None,
					'sra_status': None,
					'sra_accession': None,
					'sra_message': None,
					'genbank_status': None,
					'genbank_accession': None,
					'genbank_message': None,
					'genbank_release_date': None,
					'tracking_location': tracking_location,
				}
				# Common fields
				status = action.get("status", None)
				response = action.find("Response")
				response_message = None
				if response is not None:
					message_tag = response.find("Message")
					if message_tag is not None:
						response_message = message_tag.text.strip()
					else:
						response_message = response.get("status", "").strip() or (response.text or "").strip()
				# Fill in based on database
				if target_db == "biosample":
					report['biosample_status'] = status
					report['biosample_message'] = response_message
				elif target_db == "sra":
					report['sra_status'] = status
					report['sra_message'] = response_message
				elif target_db == "genbank":
					report['genbank_status'] = status
					report['genbank_message'] = response_message
					report['genbank_release_date'] = action.get("release_date", None)
				reports.append(report)
		except FileNotFoundError:
			print(f"Report not found: {report_path}")
		except ET.ParseError:
			print(f"Error parsing XML report: {report_path}")
		df = pd.DataFrame(reports)
		df = df.where(pd.notna(df), None)
		return df
	def submit_files(self, files, type):
		""" Uploads a set of files to a host site at submit/<Test|Production>/sample_database/<files> """
		sample_subtype_dir = f'{self.sample.batch_id}_{type}' # samplename_<biosample,sra,genbank> (a unique submission dir)
		self.client.connect()
		# Navigate to submit/<Test|Production>/<submission_db> folder
		self.client.change_dir(f"submit/{self.submission_dir}/{sample_subtype_dir}")
		for file_path in files:
			self.client.upload_file(file_path, f"{os.path.basename(file_path)}")
		print(f"Submitted files for sample batch: {self.sample.batch_id}")
	def close(self):
		self.client.close()


class SFTPClient:
	def __init__(self, config):
		self.host = config['NCBI_sftp_host']
		self.username = config['NCBI_username']
		self.password = config['NCBI_password']
		self.port = config.get('port', 22)
		self.sftp = None
		self.ssh = None
	def connect(self):
		try:
			self.ssh = paramiko.SSHClient()
			self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			self.ssh.connect(self.host, username=self.username, password=self.password, port=self.port)
			self.sftp = self.ssh.open_sftp()
			print(f"Connected to SFTP: {self.host}")
		except Exception as e:
			raise ConnectionError(f"Failed to connect to SFTP: {e}")
	def change_dir(self, dir_path):
		try:
			self.sftp.chdir(dir_path)  # Try to change to the directory
		except IOError:
			self.sftp.mkdir(dir_path)  # Create the directory if it doesn't exist
			self.sftp.chdir(dir_path)  # Change to the newly created directory
		print(f"Changed directories to {dir_path} ")
	def file_exists(self, file_path):
		try:
			self.sftp.stat(file_path)
			return True
		except IOError:
			return False
	def download_file(self, remote_file, local_path):
		try:
			self.sftp.get(remote_file, local_path)
			print(f"Downloaded {remote_file} to {local_path}")
		except Exception as e:
			raise IOError(f"Failed to download {remote_file}: {e}")
	def upload_file(self, file_path, destination_path):
		try:
			self.sftp.put(file_path, destination_path)
			print(f"Uploaded {file_path} to {destination_path}")
		except Exception as e:
			raise IOError(f"Failed to upload {file_path}: {e}")
	def close(self):
		if self.sftp:
			self.sftp.close()
		if self.ssh:
			self.ssh.close()
		print("SFTP connection closed.")

class FTPClient:
	def __init__(self, config):
		self.host = config['NCBI_ftp_host']
		self.username = config['NCBI_username']
		self.password = config['NCBI_password']
		self.port = config.get('port', 21)  # Default FTP port is 21
		self.ftp = None
	def connect(self):
		try:
			# Connect to FTP host and login
			self.ftp = ftplib.FTP()
			self.ftp.connect(self.host, self.port)
			self.ftp.login(user=self.username, passwd=self.password)
			print(f"Connected to FTP: {self.host}:{self.port}")
		except EOFError as e:
			print("EOFError occurred during FTP connection.")
			raise ConnectionError(f"Failed to connect to FTP: {e}")
		except Exception as e:
			print(f"Unexpected error during FTP connection: {e}")
			raise ConnectionError(f"Failed to connect to FTP: {e}")
	def change_dir(self, dir_path):
		try:
			self.ftp.cwd(dir_path)  # Try to change to the directory
		except ftplib.error_perm:
			self.ftp.mkd(dir_path)  # Create the directory if it doesn't exist
			self.ftp.cwd(dir_path)  # Change to the newly created directory
		print(f"Changed directories to {dir_path}")
	def file_exists(self, file_path):
		if file_path in self.ftp.nlst():
			return True
		else:
			return False
	def download_file(self, remote_file, local_path):
		with open(local_path, 'wb') as f:
			self.ftp.retrbinary(f'RETR {remote_file}', f.write)
		print(f"Downloaded file from {remote_file} to {local_path}")
	def upload_file(self, file_path, destination_path):
		try:
			if file_path.endswith(('.fasta', '.fastq', '.fna', '.fsa', '.gff', '.gff3', '.gz', 'xml', '.sqn', '.sbt', '.cmt')):  
				with open(file_path, 'rb') as file:
					print(f"Uploading binary file: {file_path}")
					self.ftp.storbinary(f'STOR {destination_path}', file)
			else:
				with open(file_path, 'r') as file:
					print(f"Uploading text file: {file_path}")
					self.ftp.storlines(f'STOR {destination_path}', file)
				# Open the file and upload it
			print(f"Uploaded {file_path} to {destination_path}")
		except Exception as e:
			raise IOError(f"Failed to upload {file_path}: {e}")
	def close(self):
		if self.ftp:
			try:
				self.ftp.quit()  # Gracefully close the connection
			except Exception:
				self.ftp.close()  # Force close if quit() fails
		print("FTP connection closed.")

class XMLSubmission(ABC):
	def __init__(self, sample, submission_config, metadata_df, output_dir, parameters):
		self.sample = sample
		self.submission_config = submission_config
		self.output_dir = output_dir
		self.parameters = parameters
		self.metadata_df = metadata_df
	def safe_text(self, value):
		if value is None or (isinstance(value, float) and math.isnan(value)):
			return "Not Provided"
		return str(value)
	def init_xml_root(self):
		self.submission_root = ET.Element('Submission')
		# Description
		description = ET.SubElement(self.submission_root, 'Description')
		if "Specified_Release_Date" in self.submission_config:
			release_date_value = self.submission_config["Specified_Release_Date"]
			if release_date_value and release_date_value != "Not Provided":
				release_date = ET.SubElement(description, "Hold")
				release_date.set("release_date", release_date_value)
		comment = ET.SubElement(description, 'Comment')
		comment.text = "Batch submission"  # Or use description from the batch
		# Organization
		organization_attributes = {
			'role': self.submission_config['Role'],
			'type': self.submission_config['Type']
		}
		org_id = self.submission_config.get('Org_ID', '').strip()
		if org_id:
			organization_attributes['org_id'] = org_id
		organization_el = ET.SubElement(description, 'Organization', organization_attributes)
		name = ET.SubElement(organization_el, 'Name')
		name.text = self.safe_text(self.submission_config['Submitting_Org'])
		contact_el = ET.SubElement(organization_el, 'Contact', {'email': self.submission_config['Email']})
		contact_name = ET.SubElement(contact_el, 'Name')
		ET.SubElement(contact_name, 'First').text = self.safe_text(self.submission_config['Submitter']['Name']['First'])
		ET.SubElement(contact_name, 'Last').text = self.safe_text(self.submission_config['Submitter']['Name']['Last'])
	def finalize_xml(self):
		xml_output_path = os.path.join(self.output_dir, "submission.xml")
		rough_string = ET.tostring(self.submission_root, encoding='utf-8')
		reparsed = minidom.parseString(rough_string)
		pretty_xml = reparsed.toprettyxml(indent="  ")
		with open(xml_output_path, 'w', encoding='utf-8') as f:
			f.write(pretty_xml)
		print(f"Batch XML generated at {xml_output_path}")
		self.xml_output_path = xml_output_path
	def add_sample(self, sample, metadata_df):
		# Support passing each sample object and its associated metadata (for the per-sample blocks)
		self.sample = sample
		self.metadata_df = metadata_df
		parser = MetadataParser(self.metadata_df, self.parameters)
		self.top_metadata = parser.extract_top_metadata()
		self.biosample_metadata = parser.extract_biosample_metadata()
		self.sra_metadata = parser.extract_sra_metadata()
		# Call subclass-specific methods to add the unique parts
		self.add_action_block(self.submission_root)
		self.add_attributes_block(self.submission_root)
	@abstractmethod
	def add_action_block(self, submission):
		"""Add the action block, which differs between submissions."""
		pass
	@abstractmethod
	def add_attributes_block(self, submission):
		"""Add the attributes block, which differs between submissions."""
		pass

class BiosampleSubmission(XMLSubmission, Submission):
	def __init__(self, sample, parameters, submission_config, metadata_df, output_dir, submission_mode, submission_dir, type, accession_id = None):
		# Properly initialize the base classes 
		XMLSubmission.__init__(self, sample, submission_config, metadata_df, output_dir, parameters) 
		Submission.__init__(self, sample, parameters, submission_config, output_dir, submission_mode, submission_dir, type) 
		self.accession_id = accession_id
		os.makedirs(self.output_dir, exist_ok=True)
	def add_action_block(self, submission):
		action = ET.SubElement(submission, 'Action')
		add_data = ET.SubElement(action, 'AddData', {'target_db': 'BioSample'})
		data = ET.SubElement(add_data, 'Data', {'content_type': 'XML'})
		xml_content = ET.SubElement(data, 'XmlContent')
		spuid_namespace_value = self.safe_text(self.top_metadata['ncbi-spuid_namespace'])
		identifier = ET.SubElement(add_data, 'Identifier')
		identifier_spuid = ET.SubElement(identifier, 'SPUID', {'spuid_namespace': f"{spuid_namespace_value}_BS"})
		identifier_spuid.text = self.safe_text(self.top_metadata['ncbi-spuid'])
		# BioSample-specific XML elements
		biosample = ET.SubElement(xml_content, 'BioSample', {'schema_version': '2.0'})
		sample_id = ET.SubElement(biosample, 'SampleId')
		spuid = ET.SubElement(sample_id, 'SPUID', {'spuid_namespace': f"{spuid_namespace_value}_BS"})
		spuid.text = self.safe_text(self.top_metadata['ncbi-spuid'])
		descriptor = ET.SubElement(biosample, 'Descriptor')
		if 'title' in self.top_metadata and self.top_metadata['title']:
			title = ET.SubElement(descriptor, 'Title')
			title.text = self.safe_text(self.top_metadata['title'])
		# BioSample XSD will not accept a description here, although the example submission.xml has one ("white space not allowed, attribute is element-only")
		#if 'description' in self.top_metadata and self.top_metadata['description']:
		#	description = ET.SubElement(descriptor, 'Description')
		#	description.text = self.safe_text(self.top_metadata['description'])
		organism = ET.SubElement(biosample, 'Organism')
		organismName = ET.SubElement(organism, 'OrganismName')
		organismName.text = self.safe_text(self.biosample_metadata['organism'])
		bioproject = ET.SubElement(biosample, 'BioProject')
		primary_id = ET.SubElement(bioproject, 'PrimaryId')
		primary_id.text = self.safe_text(self.top_metadata['ncbi-bioproject'])
		bs_package = ET.SubElement(biosample, 'Package')
		bs_package.text = self.safe_text(self.submission_config['BioSample_package'])
		# Add conditional block for accession_id
		if self.accession_id:
			attribute_ref_id = ET.SubElement(biosample, 'AttributeRefId')
			ref_id = ET.SubElement(attribute_ref_id, 'RefId')
			primary_id = ET.SubElement(ref_id, 'PrimaryId', {'db': 'BioProject'})
			primary_id.text = self.safe_text(self.top_metadata['ncbi-bioproject'])
			attribute_ref_id = ET.SubElement(biosample, 'AttributeRefId')
			ref_id = ET.SubElement(attribute_ref_id, 'RefId')
			primary_id = ET.SubElement(ref_id, 'PrimaryId', {'db': 'BioSample'})
			primary_id.text = self.accession_id
	def add_attributes_block(self, submission):
		biosample = submission.find(".//BioSample")
		attributes = ET.SubElement(biosample, 'Attributes')
		for attr_name, attr_value in self.biosample_metadata.items():
			# organism already added to XML in add_action_block, also ignore the test fields in the custom metadata JSON
			ignored_fields = ['organism', 'test_field_1', 'test_field_2', 'test_field_3']
			if attr_name not in ignored_fields:
				attribute = ET.SubElement(attributes, 'Attribute', {'attribute_name': attr_name})
				attribute.text = self.safe_text(attr_value)
	def submit(self):
		# Create submit.ready file (without using Posix object because all files_to_submit need to be same type)
		submit_ready_file = os.path.join(self.output_dir, 'submit.ready')
		with open(submit_ready_file, 'w') as fp:
			pass 
		# Submit files
		files_to_submit = [submit_ready_file, self.xml_output_path]
		self.submit_files(files_to_submit, 'biosample')
		print(f"Submitted sample batch {self.sample.batch_id} to BioSample")

class SRASubmission(XMLSubmission, Submission):
	def __init__(self, sample, parameters, submission_config, metadata_df, output_dir, submission_mode, submission_dir, type, samples = None, accession_id = None):
		# Properly initialize the base classes 
		XMLSubmission.__init__(self, sample, submission_config, metadata_df, output_dir, parameters) 
		Submission.__init__(self, sample, parameters, submission_config, output_dir, submission_mode, submission_dir, type)
		self.accession_id = accession_id
		os.makedirs(self.output_dir, exist_ok=True)
		self.samples = samples or []
	def add_action_block(self, submission):
		action = ET.SubElement(submission, "Action")
		add_files = ET.SubElement(action, "AddFiles", target_db="SRA")
		fastq1 = f"{self.sample.sample_id}_R1.fq.gz"
		fastq2 = f"{self.sample.sample_id}_R2.fq.gz"
		file1 = ET.SubElement(add_files, "File", file_path=fastq1)
		data_type1 = ET.SubElement(file1, "DataType")
		data_type1.text = "generic-data"
		file2 = ET.SubElement(add_files, "File", file_path=fastq2)
		data_type2 = ET.SubElement(file2, "DataType")
		data_type2.text = "generic-data"
	def add_attributes_block(self, submission):
		add_files = submission.find(".//AddFiles")
		for attr_name, attr_value in self.sra_metadata.items():
			if attr_value != "Not Provided":
				attribute = ET.SubElement(add_files, 'Attribute', {'name': attr_name})
				attribute.text = self.safe_text(attr_value)
		spuid_namespace_value = self.safe_text(self.top_metadata['ncbi-spuid_namespace'])
		attribute_ref_id_bioproject = ET.SubElement(add_files, "AttributeRefId", name="BioProject")
		refid_bioproject = ET.SubElement(attribute_ref_id_bioproject, "RefId")
		primaryid_bioproject = ET.SubElement(refid_bioproject, "PrimaryId")
		primaryid_bioproject.text = self.safe_text(self.top_metadata['ncbi-bioproject'])
		attribute_ref_id_biosample = ET.SubElement(add_files, "AttributeRefId", name="BioSample")
		refid_biosample = ET.SubElement(attribute_ref_id_biosample, "RefId")
		spuid_biosample = ET.SubElement(refid_biosample, "SPUID", {'spuid_namespace': f"{spuid_namespace_value}_BS"})
		spuid_biosample.text = self.safe_text(self.top_metadata['ncbi-spuid'])
		identifier = ET.SubElement(add_files, 'Identifier')
		identifier_spuid = ET.SubElement(identifier, 'SPUID', {'spuid_namespace': f"{spuid_namespace_value}_SRA"})
		identifier_spuid.text = self.safe_text(self.top_metadata['ncbi-spuid'])
		# todo: add attribute ref ID for BioSample
	def submit(self):
		# Create submit.ready file (without using Posix object because all files_to_submit need to be same type)
		submit_ready_file = os.path.join(self.output_dir, 'submit.ready')
		with open(submit_ready_file, 'w') as fp:
			pass 
		# Submit files (rename them using a temporary dir that gets removed after the loop)
		with tempfile.TemporaryDirectory() as tmpdir:
			files_to_submit = [submit_ready_file, self.xml_output_path] # files to submit
			# Rename (copy) FASTQ files for each sample in batch
			for sample in self.samples:
				ext1 = get_compound_extension(sample.fastq1)
				ext2 = get_compound_extension(sample.fastq2)
				fastq1 = os.path.join(tmpdir, f"{sample.sample_id}_R1{ext1}")
				fastq2 = os.path.join(tmpdir, f"{sample.sample_id}_R2{ext2}")
				shutil.copy(sample.fastq1, fastq1)
				shutil.copy(sample.fastq2, fastq2)
				files_to_submit.extend([fastq1, fastq2])
			# Submit files from temporary directory
			self.submit_files(files_to_submit, 'sra')
			print(f"Submitted sample batch {self.sample.batch_id} to SRA")

class GenbankSubmission(XMLSubmission, Submission):
	def __init__(self, sample, parameters, submission_config, metadata_df, output_dir, submission_mode, submission_dir, type, accession_id = None):
		# Properly initialize the base classes 
		XMLSubmission.__init__(self, sample, submission_config, metadata_df, output_dir, parameters) 
		Submission.__init__(self, sample, parameters, submission_config, output_dir, submission_mode, submission_dir, type)
		# Use the MetadataParser to extract metadata needed for GB submission
		parser = MetadataParser(metadata_df, parameters)
		self.top_metadata = parser.extract_top_metadata()
		self.genbank_metadata = parser.extract_genbank_metadata()
		self.biosample_metadata = parser.extract_biosample_metadata()
		self.accession_id = accession_id
		os.makedirs(self.output_dir, exist_ok=True)
		# Generate the GenBank XML upon initialization only if sample.ftp_upload is True
		if self.sample.ftp_upload:
			self.xml_output_path = self.create_xml(output_dir)
	def add_action_block(self, submission):
		action = ET.SubElement(submission, "Action")
		add_files = ET.SubElement(action, "AddFiles", target_db="WGS")
		# File details
		file1 = ET.SubElement(add_files, "File", file_path=f"{self.sample.sample_id}.sqn")
		data_type1 = ET.SubElement(file1, "DataType")
		data_type1.text = "wgs-contigs-sqn"
		# Meta content with genome description
		meta = ET.SubElement(add_files, "Meta", content_type="XML")
		xml_content = ET.SubElement(meta, "XmlContent")
		genome = ET.SubElement(xml_content, "Genome")
		description = ET.SubElement(genome, "Description")
		# todo: adding these using the comment.cmt file but would rather put them here
		#assembly_metadata_choice = ET.SubElement(description, "GenomeAssemblyMetadataChoice")
		# Add StructuredComment tag within GenomeAssemblyMetadataChoice
		#ET.SubElement(assembly_metadata_choice, "StructuredComment")
		#ET.SubElement(description, "GenomeRepresentation").text = "Full"
		# Add AttributeRefId and BioProject Reference
		attribute_ref = ET.SubElement(add_files, "AttributeRefId")
		ref_id = ET.SubElement(attribute_ref, "RefId")
		primary_id = ET.SubElement(ref_id, "PrimaryId", db="BioProject")
		primary_id.text = self.safe_text(self.top_metadata["ncbi-bioproject"])
		# BioSample SPUID Reference
		spuid_namespace_value = self.safe_text(self.top_metadata['ncbi-spuid_namespace'])
		biosample_ref = ET.SubElement(add_files, "AttributeRefId", name="BioSample")
		refid_biosample = ET.SubElement(biosample_ref, "RefId")
		spuid_biosample = ET.SubElement(refid_biosample, "SPUID", {'spuid_namespace': f"{spuid_namespace_value}_BS"})
		spuid_biosample.text = self.safe_text(self.top_metadata["ncbi-spuid"])

		# Add SPUID Identifier for BioSample
		identifier = ET.SubElement(add_files, "Identifier")
		spuid = ET.SubElement(identifier, "SPUID", spuid_namespace={'spuid_namespace': f"{spuid_namespace_value}_GB"})
		spuid.text = self.safe_text(self.top_metadata["ncbi-spuid"])

	def add_attributes_block(self, submission):
		# Adding a second action for the BioSample details
		action = ET.SubElement(submission, "Action")
		add_data = ET.SubElement(action, "AddData", target_db="BioSample")
		
		# XML content for BioSample details
		data = ET.SubElement(add_data, "Data", content_type="XML")
		xml_content = ET.SubElement(data, "XmlContent")
		biosample = ET.SubElement(xml_content, "BioSample", schema_version="2.0")
		
		spuid_namespace_value = self.safe_text(self.top_metadata['ncbi-spuid_namespace'])
		sample_id = ET.SubElement(biosample, "SampleId")
		spuid = ET.SubElement(sample_id, "SPUID", {'spuid_namespace': f"{spuid_namespace_value}_BS"})
		spuid.text = self.safe_text(self.top_metadata["ncbi-spuid"])

		# Descriptor section
		descriptor = ET.SubElement(biosample, "Descriptor")
		ET.SubElement(descriptor, "Title").text = self.safe_text(self.top_metadata["title"])
		
		# Organism information
		organism = ET.SubElement(biosample, "Organism")
		ET.SubElement(organism, "OrganismName").text = self.safe_text(self.biosample_metadata['organism'])

		# BioProject reference within BioSample
		bio_project = ET.SubElement(biosample, "BioProject")
		primary_id = ET.SubElement(bio_project, "PrimaryId", db="BioProject")
		primary_id.text = self.safe_text(self.top_metadata["ncbi-bioproject"])

		# Package and Attributes
		ET.SubElement(biosample, "Package").text = "Microbe.1.0"
		attributes = ET.SubElement(biosample, "Attributes")
		ET.SubElement(attributes, "Attribute", attribute_name="strain").text = self.safe_text(self.biosample_metadata['strain'])
		ET.SubElement(attributes, "Attribute", attribute_name="collection_date").text = self.safe_text(self.biosample_metadata['collection_date'])
		ET.SubElement(attributes, "Attribute", attribute_name="geo_loc_name").text = self.safe_text(self.biosample_metadata['geo_loc_name'])
		ET.SubElement(attributes, "Attribute", attribute_name="host").text = self.safe_text(self.biosample_metadata['host'])
		ET.SubElement(attributes, "Attribute", attribute_name="isolation_source").text = self.safe_text(self.biosample_metadata['isolation_source'])
		ET.SubElement(attributes, "Attribute", attribute_name="sample_type").text = self.safe_text(self.biosample_metadata['sample_type'])
		
		# Add SPUID Identifier for BioSample
		identifier = ET.SubElement(add_data, "Identifier")
		spuid = ET.SubElement(identifier, "SPUID", spuid_namespace={'spuid_namespace': f"{spuid_namespace_value}_BS"})
		spuid.text = self.safe_text(self.top_metadata["ncbi-spuid"])


	# Functions for manually preparing files for table2asn + manual submission (where ftp upload not supported)
	def create_source_file(self):
		source_data = {
			"Sequence_ID": self.top_metadata.get("sequence_name"),
			"strain": self.top_metadata.get("sequence_name"),
			"BioProject": self.top_metadata.get("ncbi-bioproject"),
			"organism": self.biosample_metadata.get("organism"),
			"Collection_date": self.biosample_metadata.get("collection_date"),
			"country": self.biosample_metadata.get("geo_loc_name"),
			"isolate": self.biosample_metadata.get("isolate"),
			"host": self.biosample_metadata.get("host"),
			"isolation_source": self.biosample_metadata.get("isolation_source")
		}
		source_df = pd.DataFrame([source_data])
		source_df.to_csv(os.path.join(self.output_dir, "source.src"), sep="\t", index=False)
	def create_comment_file(self):
		comment_data = {
			"SeqID": self.top_metadata.get("sequence_name"),
			"StructuredCommentPrefix": "Assembly-Data",
			"organism": self.biosample_metadata.get("organism"),
			"collection_date": self.biosample_metadata.get("collection_date"),
			"Assembly-Method": self.genbank_metadata.get("assembly_method"),
			"Coverage": self.genbank_metadata.get("mean_coverage"),
			"host_age": self.biosample_metadata.get("host_age"),
			"host_gender": self.biosample_metadata.get("host_sex"),
			"StructuredCommentSuffix": "Assembly-Data"
		}
		comment_df = pd.DataFrame([comment_data])
		comment_df.to_csv(os.path.join(self.output_dir, "comment.cmt"), sep="\t", index=False)
	def create_authorset_file(self):
		""" Create the authorset.sbt file that is required for table2asn to run """
		submitter_first = self.submission_config["Submitter"]["Name"]["First"]
		submitter_last = self.submission_config["Submitter"]["Name"]["Last"]
		submitter_email = self.submission_config["Submitter"]["@email"]
		alt_submitter_email = self.submission_config["Submitter"]["@alt_email"]
		affil = self.submission_config["Submitting_Org"]
		div = self.submission_config["Submitting_Org_Dept"]
		publication_status = self.safe_text(self.genbank_metadata['publication_status'])
		publication_title = self.safe_text(self.genbank_metadata['publication_title'])
		street = self.submission_config["Street"]
		city = self.submission_config["City"]
		sub = self.submission_config["State"]
		country = self.submission_config["Country"]
		email = self.submission_config["Email"]
		phone = self.submission_config["Phone"]
		zip_code = self.submission_config["Postal_code"]
		authorset_file = os.path.join(self.output_dir, "authorset.sbt")
		with open(authorset_file, "w+") as f:
			f.write("Submit-block ::= {\n")
			f.write("  contact {\n")
			f.write("    contact {\n")
			f.write("      name name {\n")
			f.write("        last \"" + submitter_last + "\",\n")
			f.write("        first \"" + submitter_first + "\",\n")
			f.write("        middle \"\",\n")
			f.write("        initials \"\",\n")
			f.write("        suffix \"\",\n")
			f.write("        title \"\"\n")
			f.write("      },\n")
			f.write("      affil std {\n")
			f.write("        affil \""+ affil + "\",\n")
			f.write("        div \"" + div + "\",\n")
			f.write("        city \"" + city + "\",\n")
			f.write("        sub \"" + sub + "\",\n")
			f.write("        country \"" + country + "\",\n")
			f.write("        street \"" + street + "\",\n")
			f.write("        email \"" + email + "\",\n")
			f.write("        phone \"" + phone + "\",\n")
			f.write("        postal-code \"" + zip_code + "\"\n")
			f.write("      }\n")
			f.write("    }\n")
			f.write("  },\n")
			f.write("  cit {\n")
			f.write("    authors {\n")
			f.write("      names std {\n")
			authors_list = self.safe_text(self.genbank_metadata.get("authors")).split("; ")
			if authors_list[0] not in ["Not Provided", ""]:
				total_names = len(authors_list)
				for index, author in enumerate(authors_list, start=1):
					# Parse the author name into first, middle, last, suffix, title
					name = HumanName(author.strip())
					f.write("        {\n")
					f.write("          name name {\n")
					f.write("            last \"" + self.safe_text(name.last) + "\",\n")
					f.write("            first \"" + self.safe_text(name.first) + "\"")
					middle_name = self.safe_text(name.middle)
					if middle_name != "Not Provided":
						f.write(",\n            middle \"" + middle_name + "\"")
					suffix = self.safe_text(name.suffix)
					if suffix != "Not Provided":
						f.write(",\n            suffix \"" + suffix + "\"")
					title = self.safe_text(name.title)
					if title != "Not Provided":
						f.write(",\n            title \"" + title + "\"")
					f.write("\n          }\n")
					if index == total_names:
						f.write("        }\n")
					else:
						f.write("        },\n")
			f.write("      },\n")
			f.write("      affil std {\n")
			f.write("        affil \"" + affil + "\",\n")
			f.write("        div \"" + div + "\",\n")
			f.write("        city \"" + city + "\",\n")
			f.write("        sub \"" + sub + "\",\n")
			f.write("        country \"" + country + "\",\n")
			f.write("        street \"" + street + "\",\n")
			f.write("        postal-code \"" + zip_code + "\"\n")
			f.write("      }\n")
			f.write("    }\n")
			f.write("  },\n")
			f.write("  subtype new\n")
			f.write("}\n")
			f.write("Seqdesc ::= pub {\n")
			f.write("  pub {\n")
			f.write("    gen {\n")
			f.write("      cit \"" + publication_status + "\",\n")
			f.write("      authors {\n")
			f.write("        names std {\n")
			authors_list = self.safe_text(self.genbank_metadata.get("authors")).split("; ")
			if authors_list[0] not in ["Not Provided", ""]:
				total_names = len(authors_list)
				for index, author in enumerate(authors_list, start=1):
					# Parse the author name into first, middle, last, suffix, title
					name = HumanName(author.strip())
					f.write("        {\n")
					f.write("          name name {\n")
					f.write("            last \"" + self.safe_text(name.last) + "\",\n")
					f.write("            first \"" + self.safe_text(name.first) + "\"")
					middle_name = self.safe_text(name.middle)
					if middle_name != "Not Provided":
						f.write(",\n            middle \"" + middle_name + "\"")
					suffix = self.safe_text(name.suffix)
					if suffix != "Not Provided":
						f.write(",\n            suffix \"" + suffix + "\"")
					title = self.safe_text(name.title)
					if title != "Not Provided":
						f.write(",\n            title \"" + title + "\"")
					f.write("\n          }\n")
					if index == total_names:
						f.write("        }\n")
					else:
						f.write("        },\n")
			f.write("        }\n")
			f.write("      },\n")
			f.write("      title \"" + publication_title + "\"\n")
			f.write("    }\n")
			f.write("  }\n")
			f.write("}\n")
			if alt_submitter_email is not None and alt_submitter_email.strip() != "":
				f.write("Seqdesc ::= user {\n")
				f.write("  type str \"Submission\",\n")
				f.write("  data {\n")
				f.write("    {\n")
				f.write("      label str \"AdditionalComment\",\n")
				f.write("      data str \"ALT EMAIL: " + alt_submitter_email + "\"\n")
				f.write("    }\n")
				f.write("  }\n")
				f.write("}\n")
			f.write("Seqdesc ::= user {\n")
			f.write("  type str \"Submission\",\n")
			f.write("  data {\n")
			f.write("    {\n")
			f.write("      label str \"AdditionalComment\",\n")
			f.write("      data str \"Submission Title: " + self.sample.sample_id + "\"\n")
			f.write("    }\n")
			f.write("  }\n")
			f.write("}\n")
	def prepare_files_manual_submission(self):
		""" Prepare files for manual upload to GenBank because FTP support not available 
			These files will be emailed to user and/or GenBank, and also zipped to output dir """
		# Create the source df
		# todo: that seq_id needs to be the genbank sequence id
		self.create_source_file()
		# Create Structured Comment file
		self.create_comment_file()
		# Create authorset file
		self.create_authorset_file()
		print(f"Genbank files prepared for {self.sample.sample_id}")
		# Rename and move the fasta for table2asn call
		renamed_fasta = os.path.join(f"{self.output_dir}/sequence.fsa")
		if not os.path.exists(renamed_fasta):
			shutil.move(self.sample.fasta_file, renamed_fasta)
		# Run table2asn 
		self.run_table2asn()
		# Zip the files
		with ZipFile(os.path.join(self.output_dir, self.sample.sample_id + ".zip"), 'w') as zip:
			filelist = [f"{self.sample.sample_id}.sqn","authorset.sbt","sequence.fsa","source.src","comment.cmt"]
			for file in filelist:
				filepath = os.path.join(self.output_dir, file)
				if os.path.exists(filepath):
					zip.write(filepath, file)
				# add f"{self.sample.sample_id}.sqn" to zip files? 
	
	def prepare_files_ftp_submission(self):
		""" Prepare some files needed for table2asn for GenBank FTP submission
			These files will be uploaded along with submission.xml and <sample_name>.sqn files """
		if not os.path.exists(self.output_dir):
			os.makedirs(self.output_dir)
		# Create Structured Comment file
		self.create_comment_file()
		# Create authorset file
		self.create_authorset_file()
		print(f"Genbank files prepared for {self.sample.sample_id}")
		# Rename and move the fasta for table2asn call
		renamed_fasta = os.path.join(f"{self.output_dir}/sequence.fsa")
		if not os.path.exists(renamed_fasta):
			shutil.move(self.sample.fasta_file, renamed_fasta)
		# Run table2asn
		self.run_table2asn() 

	# Functions for running table2asn
	def get_gff_locus_tag(self):
		""" Read the locus lag from the GFF3 file for use in table2asn command"""
		locus_tag = None
		if not self.sample.annotation_file.endswith('.tbl'):
			with open(self.sample.annotation_file, 'r') as file:
				for line in file:
					if line.startswith('##FASTA'):
						break  # Stop reading if FASTA section starts
					elif line.startswith('#'):
						continue  # Skip comment lines
					else:
						columns = line.strip().split('\t')
						if columns[2] == 'CDS':
							attributes = columns[8].split(';')
							for attribute in attributes:
								key, value = attribute.split('=')
								if key == 'locus_tag':
									locus_tag = value.split('_')[0]
									break  # Found locus tag, stop searching
							if locus_tag:
								break  # Found locus tag, stop searching
		return locus_tag
	#  Detect multiple contig fasta for Table2asn submission
	def is_multicontig_fasta(self, fasta_file):
		headers = set()
		with open(fasta_file, 'r') as file:
			for line in file:
				if line.startswith('>'):
					headers.add(line.strip())
					if len(headers) > 1:
						return True
		return False
	def run_table2asn(self):
		"""
		Executes table2asn with appropriate flags and handles errors.
		"""
		print("Running table2asn...")
		# Check if table2asn executable exists in PATH
		table2asn_path = shutil.which('table2asn')
		if not table2asn_path:
			raise FileNotFoundError("table2asn executable not found in PATH.")
		# Check if a GFF file is supplied and extract the locus tag
		# todo: the locus tag needs to be fetched (?) after BioSample is assigned (it appears under Manage Data for the BioProject)
		locus_tag = self.get_gff_locus_tag()
		shutil.move(self.sample.annotation_file, self.output_dir)
		# Construct the table2asn command
		cmd = [
			"table2asn",
			"-i", f"{self.output_dir}/sequence.fsa",
			"-o", f"{self.output_dir}/{self.sample.sample_id}.sqn",
			"-t", f"{self.output_dir}/authorset.sbt",
			"-f", f"{self.output_dir}/{os.path.basename(self.sample.annotation_file)}"
		]
		if locus_tag:
			cmd.extend(["-locus-tag-prefix", locus_tag])
		if self.is_multicontig_fasta(f"{self.output_dir}/sequence.fsa"):
			cmd.append("-M")
			cmd.append("n")
			cmd.append("-Z")
		if os.path.isfile(f"{self.output_dir}/comment.cmt"):
			cmd.append("-w")
			cmd.append("comment.cmt")
		# if not using submission.xml file, need the source.src file
		if not self.sample.ftp_upload:
			cmd.append("-src-file")
			cmd.append(f"{self.output_dir}/source.src")
		# Run the command and capture errors
		print(f'table2asn command: {shlex.join(cmd)}')
		try:
			result = subprocess.run(cmd, check=True, capture_output=True, text=True)
			print(f"table2asn output: {result.stdout}")
		except subprocess.CalledProcessError as e:
			print(f"Error running table2asn: {e.stderr}")
			raise
	def sendemail(self):
		# Code for creating a zip archive for Genbank submission
		print(f"Sending submission email for {self.sample.sample_id}")
		TABLE2ASN_EMAIL = self.submission_config["table2asn_email"]
		try:
			msg = MIMEMultipart('multipart')
			msg['Subject'] = self.sample.sample_id + " table2asn submission"
			from_email = self.submission_config["Submitter"]["@email"]
			to_email = []
			cc_email = []
			if self.parameters.test == True:
				to_email.append(self.submission_config["Submitter"]["@email"])
			else:
				to_email.append(TABLE2ASN_EMAIL)
				#cc_email.append(config_dict["Description"]["Organization"]["Submitter"]["@email"])
			if self.submission_config["Submitter"]["@alt_email"]:
				cc_email.append(self.submission_config["Submitter"]["@alt_email"])
			msg['From'] = from_email
			msg['To'] = ", ".join(to_email)
			if len(cc_email) != 0:
				msg['Cc'] = ", ".join(cc_email)
			with open(os.path.join(self.output_dor, f"{self.sample.sample_id}.sqn"), 'rb') as file_input:
				part = MIMEApplication(file_input.read(), Name=f"{self.sample.sample_id}.sqn")
			part['Content-Disposition'] = "attachment; filename=f'{self.sample.sample_id}.sqn'"
			msg.attach(part)
			s = smtplib.SMTP('localhost')
			s.sendmail(from_email, to_email, msg.as_string())
			print(f"Email sent for {self.sample.sample_id}")
		except Exception as e:
			print("Error: Unable to send mail automatically. If unable to email, submission can be made manually using the sqn file.", file=sys.stderr)
			print("sqn_file:" + os.path.join(self.output_dir, f"{self.sample.sample_id}.sqn"), file=sys.stderr)
			print(e, file=sys.stderr)
	# Functions to ftp upload files
	def submit(self):
		# Create submit.ready file (without using Posix object because all files_to_submit need to be same type)
		submit_ready_file = os.path.join(self.output_dir, 'submit.ready')
		with open(submit_ready_file, 'w') as fp:
			pass 
		# Submit files
		files_to_submit = [submit_ready_file, self.xml_output_path, f"{self.output_dir}/{self.sample.sample_id}.sqn", 
						   f"{self.output_dir}/authorset.sbt", f"{self.output_dir}/comment.cmt"]
		self.submit_files(files_to_submit, 'genbank')
		print(f"Submitted sample {self.sample.sample_id} to Genbank")

if __name__ == "__main__":
	print(f"submission_new.py called with:")
	print(" ".join(sys.argv))
	submission_main()
