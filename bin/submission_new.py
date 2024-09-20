#!/usr/bin/env python3

import os
import sys
from pathlib import Path
import argparse
import yaml
from lxml import etree
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom  # Import minidom for pretty-printing
import os
import math  # Required for isnan check
import pandas as pd
from abc import ABC, abstractmethod
#import paramiko
import ftplib
from zipfile import ZipFile

def submission_main():
	""" Main for initiating submission steps
	"""
	# Get all parameters from argparse
	parameters_class = GetParams()
	parameters = parameters_class.parameters

	# Example usage:
	config_parser = SubmissionConfigParser(parameters)
	config_dict = config_parser.load_config()
	
	# Read in metadata file
	metadata_df = pd.read_csv(parameters['metadata_file'], sep='\t')
	
	# Initialize the Sample object with parameters from argparse
	sample = Sample(
		sample_id=parameters['submission_name'],
		metadata_file=parameters['metadata_file'],
		fastq1=parameters.get('fastq1'),
		fastq2=parameters.get('fastq2'),
		fasta_file=parameters.get('fasta_file'),
		gff_file=parameters.get('annotation_file')
	)

	if parameters['test']:
		submission_dir = 'test'
	else:
		submission_dir = 'prod'

	# Conditional submissions based on argparse flags
	if parameters['biosample']:
		# Perform BioSample submission
		biosample_submission = BiosampleSubmission(sample, config_dict, metadata_df, f"{parameters['output_dir']}/biosample", parameters['submission_mode'], submission_dir)
		biosample_submission.submit()

	if parameters['sra']:
		# Perform SRA submission
		sra_submission = SRASubmission(sample, config_dict, metadata_df, f"{parameters['output_dir']}/sra", parameters['submission_mode'], submission_dir)
		#sra_submission.submit()

	if parameters['genbank']:
		# Perform Genbank submission
		genbank_submission = GenbankSubmission(sample, config_dict, metadata_df, f"{parameters['output_dir']}/genbank", parameters['submission_mode'], submission_dir)
		#genbank_submission.submit()
		# Add more GB functions for table2asn submission and creating/emailing zip files

	# Add more submission logic for GISAID, etc.

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
		parser.add_argument("--metadata_file", help="Name of the validated metadata tsv file", required=True)
		parser.add_argument("--species", help="Type of organism data", required=True)
		# optional parameters
		parser.add_argument("-o", "--output_dir", type=str, default='submission_outputs',
							help="Output Directory for final Files, default is current directory")
		parser.add_argument("--test", help="Whether to perform a test submission.", required=False,	action="store_const", default=False, const=True)
		parser.add_argument("--fasta_file",	help="Fasta file to be submitted", required=False)
		parser.add_argument("--annotation_file", help="An annotation file to add to a Genbank submission", required=False)
		parser.add_argument("--fastq1", help="Fastq R1 file to be submitted", required=False)	
		parser.add_argument("--fastq2", help="Fastq R2 file to be submitted", required=False)
		parser.add_argument("--submission_mode", help="Whether to upload via ftp or sftp", required=False, default='ftp')	
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
		# Parse the config file (could be JSON, YAML, etc.)
		# Example: returns a dictionary with SFTP credentials, paths, etc.
		with open(self.parameters['config_file'], "r") as f:
			config_dict = yaml.load(f, Loader=yaml.BaseLoader) # Load yaml as str only
		if type(config_dict) is dict:
			for k, v in config_dict.items():
				# If GISAID submission, check that GISAID keys have values
				if self.parameters["gisaid"]:
					if k.startswith('GISAID') and not v:
						print("Error: There are missing GISAID values in the config file.", file=sys.stderr)
						#sys.exit(1)					
				else:
					# If NCBI submission, check that non-GISAID keys have values (note: this only check top-level keys)
					if k.startswith('NCBI') and not v:
						print("Error: There are missing NCBI values in the config file.", file=sys.stderr)
						#sys.exit(1)	
		else:	
			print("Error: Config file is incorrect. File must has a valid yaml format.", file=sys.stderr)
			sys.exit(1)
		return config_dict

class Sample:
	def __init__(self, sample_id, metadata_file, fastq1, fastq2, fasta_file=None, gff_file=None):
		self.sample_id = sample_id
		self.metadata_file = metadata_file
		self.fastq1 = fastq1
		self.fastq2 = fastq2
		self.fasta_file = fasta_file
		self.gff_file = gff_file
	# todo: add (or ignore) validation for cloud files 
	def validate_files(self):
		files_to_check = [self.metadata_file, self.fastq1, self.fastq2]
		if self.fasta_file:
			files_to_check.append(self.fasta_file)
		if self.gff_file:
			files_to_check.append(self.gff_file)
		missing_files = [f for f in files_to_check if not os.path.exists(f)]
		if missing_files:
			raise FileNotFoundError(f"Missing required files: {missing_files}")
		else:
			print(f"All required files for sample {self.sample_id} are present.")

class MetadataParser:
	def __init__(self, metadata_df):
		self.metadata_df = metadata_df
	# todo: will need to adjust these to handle custom metadata for whatever biosample pkg
	def extract_top_metadata(self):
		columns = ['sequence_name', 'title', 'description', 'authors', 'ncbi-bioproject', 'ncbi-spuid_namespace', 'ncbi-spuid']  # Main columns
		available_columns = [col for col in columns if col in self.metadata_df.columns]
		return self.metadata_df[available_columns].to_dict(orient='records')[0] if available_columns else {}
	def extract_biosample_metadata(self):
		columns = ['bs_package','isolate','isolation_source','host_disease','host','collected_by','lat_lon',
				   'sex','age','geo_location','organism','purpose_of_sampling', 'race','ethnicity','sample_type']  # BioSample specific columns
		available_columns = [col for col in columns if col in self.metadata_df.columns]
		return self.metadata_df[available_columns].to_dict(orient='records')[0] if available_columns else {}
	def extract_sra_metadata(self):
		columns = ['instrument_model','library_construction_protocol','library_layout','library_name','library_selection',
				   'library_source','library_strategy','nanopore_library_layout','nanopore_library_protocol','nanopore_library_selection',
				   'nanopore_library_source','nanopore_library_strategy','nanopore_sequencing_instrument']  # SRA specific columns
		available_columns = [col for col in columns if col in self.metadata_df.columns]
		return self.metadata_df[available_columns].to_dict(orient='records')[0] if available_columns else {}

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
			print(f"Connected to FTP: {self.host}")
		except Exception as e:
			raise ConnectionError(f"Failed to connect to FTP: {e}")
	def upload_file(self, file_path, destination_path):
		try:
			# Open the file and upload it
			with open(file_path, 'r') as file:
				print(file)
				self.ftp.storlines(f'STOR {destination_path}', file)
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
	def __init__(self, sample, submission_config, metadata_df, output_dir):
		self.sample = sample
		self.submission_config = submission_config
		self.output_dir = output_dir
		parser = MetadataParser(metadata_df)
		self.top_metadata = parser.extract_top_metadata()
	def safe_text(self, value):
		if value is None or (isinstance(value, float) and math.isnan(value)):
			return "Not Provided"
		return str(value)
	def create_xml(self, output_dir):
		# Root element
		submission = ET.Element('Submission')
		# Description block (common across all submissions)
		description = ET.SubElement(submission, 'Description')
		title = ET.SubElement(description, 'Title')
		title.text = self.safe_text(self.top_metadata['title'])
		comment = ET.SubElement(description, 'Comment')
		comment.text = self.safe_text(self.top_metadata['description'])
		# Organization block (common across all submissions)
		organization_el = ET.SubElement(description, 'Organization', {
			'type': self.submission_config['Type'],
			'role': self.submission_config['Role'],
			'org_id': self.submission_config['Org_ID']
		})
		name = ET.SubElement(organization_el, 'Name')
		name.text = self.safe_text(self.submission_config['Submitting_Org'])
		# Contact block (common across all submissions)
		contact_el = ET.SubElement(organization_el, 'Contact', {'email': self.submission_config['Email']})
		contact_name = ET.SubElement(contact_el, 'Name')
		first = ET.SubElement(contact_name, 'First')
		first.text = self.safe_text(self.submission_config['Submitter']['Name']['First'])
		last = ET.SubElement(contact_name, 'Last')
		last.text = self.safe_text(self.submission_config['Submitter']['Name']['Last'])
		# Call subclass-specific methods to add the unique parts
		self.add_action_block(submission)
		self.add_attributes_block(submission)
		# Save the XML to file
		xml_output_path = os.path.join(output_dir, "submission.xml")
		os.makedirs(os.path.dirname(xml_output_path), exist_ok=True)
		rough_string = ET.tostring(submission, encoding='utf-8')
		reparsed = minidom.parseString(rough_string)
		pretty_xml = reparsed.toprettyxml(indent="  ")
		with open(xml_output_path, 'w', encoding='utf-8') as f:
			f.write(pretty_xml)
		print(f"XML generated at {xml_output_path}")
		return xml_output_path
	@abstractmethod
	def add_action_block(self, submission):
		"""Add the action block, which differs between submissions."""
		pass
	@abstractmethod
	def add_attributes_block(self, submission):
		"""Add the attributes block, which differs between submissions."""
		pass

class Submission:
	def __init__(self, sample, submission_config, output_dir, submission_mode, submission_dir):
		self.sample = sample
		self.submission_config = submission_config
		self.output_dir = output_dir
		self.submission_mode = submission_mode
		self.submission_dir = submission_dir
		self.client = self.get_client()
	def get_client(self):
		if self.submission_mode == 'sftp':
			return SFTPClient(self.submission_config)
		elif self.submission_mode == 'ftp':
			return FTPClient(self.submission_config)
		else:
			raise ValueError("Invalid submission mode: must be 'sftp' or 'ftp'")
	def submit_files(self, files):
		for file_path in files:
			self.client.upload_file(file_path, f"{submission_dir}/{self.sample.sample_id}/{os.path.basename(file_path)}")
		print(f"Submitted files for sample {self.sample.sample_id}")
	def close(self):
		self.client.close()

class BiosampleSubmission(XMLSubmission, Submission):
	def __init__(self, sample, submission_config, metadata_df, output_dir, submission_mode, submission_dir):
		# Properly initialize the base classes 
		XMLSubmission.__init__(self, sample, submission_config, metadata_df, output_dir) 
		Submission.__init__(self, sample, submission_config, output_dir, submission_mode, submission_dir) 
		# Use the MetadataParser to extract metadata
		parser = MetadataParser(metadata_df)
		self.top_metadata = parser.extract_top_metadata()
		self.biosample_metadata = parser.extract_biosample_metadata()
		# Generate the BioSample XML upon initialization
		self.xml_output_path = self.create_xml(output_dir) 
	def add_action_block(self, submission):
		action = ET.SubElement(submission, 'Action')
		add_data = ET.SubElement(action, 'AddData', {'target_db': 'BioSample'})
		data = ET.SubElement(add_data, 'Data', {'content_type': 'xml'})
		xml_content = ET.SubElement(data, 'XmlContent')
		# BioSample-specific XML elements
		biosample = ET.SubElement(xml_content, 'BioSample', {'schema_version': '2.0'})
		sample_id = ET.SubElement(biosample, 'SampleId')
		spuid = ET.SubElement(sample_id, 'SPUID', {'spuid_namespace': ''})
		spuid.text = self.safe_text(self.top_metadata['ncbi-spuid_namespace'])
	def add_attributes_block(self, submission):
		biosample = submission.find(".//BioSample")
		attributes = ET.SubElement(biosample, 'Attributes')
		for attr_name, attr_value in self.biosample_metadata.items():
			attribute = ET.SubElement(attributes, 'Attribute', {'attribute_name': attr_name})
			attribute.text = self.safe_text(attr_value)
	def submit(self):
		# Create submit.ready file
		submit_ready_file = Path(os.path.join(self.output_dir, 'submit.ready'))
		submit_ready_file.touch()
		# Submit files
		files_to_submit = [submit_ready_file, self.xml_output_path]
		self.submit_files(files_to_submit)
		print(f"Submitted sample {self.sample.sample_id} to BioSample")

class SRASubmission(XMLSubmission, Submission):
	def __init__(self, sample, submission_config, metadata_df, output_dir, submission_mode, submission_dir):
		# Properly initialize the base classes 
		XMLSubmission.__init__(self, sample, submission_config, metadata_df, output_dir) 
		Submission.__init__(self, sample, submission_config, output_dir, submission_mode, submission_dir) 
		# Use the MetadataParser to extract metadata
		parser = MetadataParser(metadata_df)
		self.top_metadata = parser.extract_top_metadata()
		self.sra_metadata = parser.extract_sra_metadata()
		# Generate the BioSample XML upon initialization
		self.xml_output_path = self.create_xml(output_dir) 
	def add_action_block(self, submission):
		action = ET.SubElement(submission, "Action")
		add_files = ET.SubElement(action, "AddFiles", target_db="SRA")
		file1 = ET.SubElement(add_files, "File", file_path=self.sample.fastq1)
		data_type1 = ET.SubElement(file1, "DataType")
		data_type1.text = "generic-data"
		file2 = ET.SubElement(add_files, "File", file_path=self.sample.fastq2)
		data_type2 = ET.SubElement(file2, "DataType")
		data_type2.text = "generic-data"
	def add_attributes_block(self, submission):
		add_files = submission.find(".//AddFiles")
		attributes = ET.SubElement(add_files, 'Attributes')
		for attr_name, attr_value in self.sra_metadata.items():
			attribute = ET.SubElement(attributes, 'Attribute', {'attribute_name': attr_name})
			attribute.text = self.safe_text(attr_value)
	def submit(self):
		# Create submit.ready file
		submit_ready_file = Path(os.path.join(self.output_dir, 'submit.ready'))
		submit_ready_file.touch()
		# Submit files
		files_to_submit = [submit_ready_file, self.xml_output_path, self.sample.fastq1, self.sample.fastq2]
		self.submit_files(files_to_submit)
		print(f"Submitted sample {self.sample.sample_id} to SRA")

class GenbankSubmission(XMLSubmission, Submission):
	def __init__(self, sample, submission_config, metadata_df, output_dir, submission_mode, submission_dir):
		# Properly initialize the base classes 
		XMLSubmission.__init__(self, sample, submission_config, metadata_df, output_dir) 
		Submission.__init__(self, sample, submission_config, output_dir, submission_mode, submission_dir)
		# Use the MetadataParser to extract metadata
		parser = MetadataParser(metadata_df)
		self.top_metadata = parser.extract_top_metadata()
		self.genbank_metadata = parser.extract_genbank_metadata()
		# Generate the BioSample XML upon initialization
		self.xml_output_path = self.create_xml(output_dir) 
	def add_action_block(self, submission):
		action = ET.SubElement(submission, "Action")
		add_files = ET.SubElement(action, "AddFiles", target_db="Genbank")
		file1 = ET.SubElement(add_files, "File", file_path=self.sample.fasta_file)
		data_type1 = ET.SubElement(file1, "DataType")
		data_type1.text = "generic-data"
		file2 = ET.SubElement(add_files, "File", file_path=self.sample.gff_file)
		data_type2 = ET.SubElement(file2, "DataType")
		data_type2.text = "generic-data"
	def add_attributes_block(self, submission):
		add_files = submission.find(".//AddFiles")
		attributes = ET.SubElement(add_files, 'Attributes')
		for attr_name, attr_value in self.genbank_metadata.items():
			attribute = ET.SubElement(attributes, 'Attribute', {'attribute_name': attr_name})
			attribute.text = self.safe_text(attr_value)
	def submit(self):
		# Create submit.ready file
		submit_ready_file = Path(os.path.join(self.output_dir, 'submit.ready'))
		submit_ready_file.touch()
		# Submit files
		files_to_submit = [submit_ready_file, self.xml_output_path, self.sample.fasta_file, self.sample.gff_file]
		self.submit_files(files_to_submit)
		print(f"Submitted sample {self.sample.sample_id} to Genbank")
	def prepare_genbank_files(self):
		# Code for preparing table2asn files
		print(f"Genbank files prepared for {self.sample.sample_id}")
	def table2asn(self):
		# Code for table2asn process
		print("Running table2asn...")
	def create_zip_files(self):
		# Code for creating a zip archive for Genbank submission
		print("Creating zip files...")



if __name__ == "__main__":
	submission_main()