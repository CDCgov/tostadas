import os
import sys
import yaml
from lxml import etree
import xml.etree.ElementTree as ET
import pandas as pd

import paramiko
from zipfile import ZipFile

class SubmissionConfigParser:
	""" Class constructor to read in config file as dict
	"""
	def __init__(self, config_file):
		# Load submission configuration
		self.config_file = config_file
	def load_config(self):
		# Parse the config file (could be JSON, YAML, etc.)
		# Example: returns a dictionary with SFTP credentials, paths, etc.
		with open(self.config_file, "r") as f:
			config_dict = yaml.load(f, Loader=yaml.BaseLoader) # Load yaml as str only
		if type(config_dict) is dict:
			for k, v in config_dict.items():
				# If GISAID submission, check that GISAID keys have values
				if gisaid_submission:
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
		#self.top_metadata = self.extract_top_metadata()
	def extract_top_metadata(self):
		columns = ['sequence_name', 'title', 'description', 'authors', 'ncbi-spuid_namespace', 'ncbi-spuid']  # Reused columns
		return self.metadata_df[columns].to_dict(orient='records')[0]  # Get first row as a dictionary
	def extract_biosample_metadata(self):
		columns = ['bs_package','isolate','isolation_source','host_disease','host','collected_by','lat_lon',
				   'host_sex','host_age','geo_location','geo_loc_name','organism','purpose_of_sampling',
				   'race','ethnicity','sample_type','source_type','strain']  # BioSample specific columns
		return self.metadata_df[columns].to_dict(orient='records')[0]
	def extract_sra_metadata(self):
		columns = ['instrument_model','library_construction_protocol','library_layout','library_name','library_selection',
				   'library_source','library_strategy','nanopore_library_layout','nanopore_library_protocol','nanopore_library_selection',
				   'nanopore_library_source','nanopore_library_strategy','nanopore_sequencing_instrument']  # SRA specific columns
		return self.metadata_df[columns].to_dict(orient='records')[0]



class SFTPClient:
	def __init__(self, config):
		self.host = config['sftp_host']
		self.username = config['username']
		self.password = config['password']
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

class BiosampleSubmission:
	def __init__(self, sample, submission_config, metadata_dict):
		self.sample = sample
		self.submission_config = submission_config
		self.metadata_dict = metadata_dict

	def submit(self):
		# Code to prepare and submit to BioSample
		print(f"Submitting sample {self.sample.sample_id} to BioSample")
		# Implement BioSample-specific submission logic here

	def create_biosample_xml(self, output_dir):
		# Root element
		submission = ET.Element('Submission')

		# Description block
		description = ET.SubElement(submission, 'Description')
		title = ET.SubElement(description, 'Title')
		title.text = self.metadata['title']
		comment = ET.SubElement(description, 'Comment')
		comment.text = self.metadata['description']

		# Organization block
		organization_el = ET.SubElement(description, 'Organization', {
			'type': self.submission_config['Type'], 'role': self.submission_config['Role'], 'org_id': self.submission_config['Org_ID']
		})
		name = ET.SubElement(organization_el, 'Name')
		name.text = self.submission_config['Name']

		# Contact block
		contact_el = ET.SubElement(organization_el, 'Contact', {'email': self.submission_config['Email']})
		contact_name = ET.SubElement(contact_el, 'Name')
		first = ET.SubElement(contact_name, 'First')
		first.text = self.submission_config['Submitter']['Name']['First']
		last = ET.SubElement(contact_name, 'Last')
		last.text = self.submission_config['Submitter']['Name']['Last']

		# Action block
		action = ET.SubElement(submission, 'Action')
		add_data = ET.SubElement(action, 'AddData', {'target_db': 'BioSample'})
		data = ET.SubElement(add_data, 'Data', {'content_type': 'xml'})
		xml_content = ET.SubElement(data, 'XmlContent')

		# BioSample block
		biosample = ET.SubElement(xml_content, 'BioSample', {'schema_version': '2.0'})

		# SampleId block
		sample_id = ET.SubElement(biosample, 'SampleId')
		spuid = ET.SubElement(sample_id, 'SPUID', {'spuid_namespace': ''})
		spuid.text = self.metadata_dict['ncbi-spuid_namespace']

		# Descriptor block
		descriptor = ET.SubElement(biosample, 'Descriptor')
		sample_title = ET.SubElement(descriptor, 'Title')
		sample_title.text = self.sample['title']

		# Organism block
		organism = ET.SubElement(biosample, 'Organism')
		organism_name = ET.SubElement(organism, 'OrganismName')
		organism_name.text = self.metadata_dict['organism']

		# Package block
		package = ET.SubElement(biosample, 'Package')
		package.text = self.metadata_dict['bs-package']

		# Attributes block
		attributes = ET.SubElement(biosample, 'Attributes')
		for attr_name, attr_value in self.sample['attributes'].items():
			attribute = ET.SubElement(attributes, 'Attribute', {'attribute_name': attr_name})
			attribute.text = attr_value

		# Identifier block
		identifier = ET.SubElement(add_data, 'Identifier')
		spuid_identifier = ET.SubElement(identifier, 'SPUID', {'spuid_namespace': '_bs'})
		spuid_identifier.text = self.metadata_dict['ncbi-spuid_namespace']

		# Save the XML to file
		tree = ET.ElementTree(submission)
		output_path = os.path.join(output_dir, f"{self.sample['sample_id']}_biosample.xml")
		tree.write(output_path, encoding='utf-8', xml_declaration=True)
		print(f"BioSample XML generated at {output_path}")





class SRASubmission:
	def __init__(self, sample, submission_config, metadata_df, sftp_client):
		self.sample = sample
		self.submission_contact = submission_config
		self.sftp_client = sftp_client
		parser = MetadataParser(metadata_df)
		self.top_metadata = parser.extract_top_metadata()
		self.sra_metadata = parser.extract_sra_metadata()

	def submit(self):
		# Upload FASTQ files to SRA via SFTP
		self.sftp_client.connect()
		self.sftp_client.upload_file(self.sample.fastq1, f"/uploads/{self.sample.sample_id}_fastq1.fastq")
		self.sftp_client.upload_file(self.sample.fastq2, f"/uploads/{self.sample.sample_id}_fastq2.fastq")
		self.sftp_client.close()
		print(f"Submitted {self.sample.sample_id} to SRA")

		def create_sra_xml(self, file_name='sra_submission.xml'):
		"""Creates an SRA submission XML file based on the provided metadata and file paths."""
		root = ET.Element("Submission")
		
		# Description block
		description = ET.SubElement(submission, 'Description')
		title = ET.SubElement(description, 'Title')
		title.text = self.top_metadata['title']
		comment = ET.SubElement(description, 'Comment')
		comment.text = self.top_metadata['description']

		# Organization block
		organization_el = ET.SubElement(description, 'Organization', {
			'type': self.submission_config['Type'], 'role': self.submission_config['Role'], 'org_id': self.submission_config['Org_ID']
		})
		name = ET.SubElement(organization_el, 'Name')
		name.text = self.submission_config['Name']

		# Contact block
		contact_el = ET.SubElement(organization_el, 'Contact', {'email': self.submission_config['Email']})
		contact_name = ET.SubElement(contact_el, 'Name')
		first = ET.SubElement(contact_name, 'First')
		first.text = self.submission_config['Submitter']['Name']['First']
		last = ET.SubElement(contact_name, 'Last')
		last.text = self.submission_config['Submitter']['Name']['Last']


		# Create Action
		action = ET.SubElement(root, "Action")
		add_files = ET.SubElement(action, "AddFiles", target_db="SRA")

		# Add file paths
		file1 = ET.SubElement(add_files, "File", file_path=self.sample.fastq1)
		data_type1 = ET.SubElement(file1, "DataType")
		data_type1.text = "generic-data"
		
		file2 = ET.SubElement(add_files, "File", file_path=self.sample.fastq2)
		data_type2 = ET.SubElement(file2, "DataType")
		data_type2.text = "generic-data"

		# Attributes block
		attributes = ET.SubElement(sra, 'Attributes')
		for attr_name, attr_value in self.sra_metadata.items():
			attribute = ET.SubElement(attributes, 'Attribute', {'attribute_name': attr_name})
			attribute.text = attr_value if attr_value else "Not Provided"  # Handle missing values if needed

		# Add AttributeRefId for BioSample
		attribute_ref_id = ET.SubElement(add_files, "AttributeRefId", name="BioSample")
		ref_id = ET.SubElement(attribute_ref_id, "RefId")
		spuid = ET.SubElement(ref_id, "SPUID", spuid_namespace="_bs")
		spuid.text = self.top_metadata['ncbi-spuid_namespace']

		# Add Identifier for SRA
		identifier = ET.SubElement(add_files, "Identifier")
		spuid_sra = ET.SubElement(identifier, "SPUID", spuid_namespace="_sra")
		spuid_sra.text = self.top_metadata['ncbi-spuid']

		# Write the XML to file
		tree = ET.ElementTree(root)
		output_path = os.path.join(output_dir, f"{self.sample['sample_id']}_sra.xml")
		tree.write(output_path, encoding="utf-8", xml_declaration=True)
		print(f"SRA XML generated at {output_path}")



class GenbankSubmission:
	def __init__(self, sample, config, sftp_client):
		self.sample = sample
		self.config = config
		self.sftp_client = sftp_client
		self.submission_files_dir = f"{sample.sample_id}_genbank_submission_files"

	def prepare_genbank_files(self):
		os.makedirs(self.submission_files_dir, exist_ok=True)
		create_genbank_files(self.config, self.sample.metadata_file, self.sample.fasta_file, self.sample.sample_id, self.submission_files_dir)
		print(f"Genbank files prepared for {self.sample.sample_id}")

	def run_table2asn(self):
		create_genbank_table2asn(self.sample.sample_id, self.submission_files_dir, self.sample.gff_file)
		print(f"Table2asn executed for {self.sample.sample_id}")

	def zip_genbank_files(self):
		create_genbank_zip(self.sample.sample_id, self.submission_files_dir)
		print(f"Genbank submission files zipped for {self.sample.sample_id}")

	def submit_sftp(self):
		self.sftp_client.connect()
		self.sftp_client.upload_file(os.path.join(self.submission_files_dir, f"{self.sample.sample_id}.sqn"), f"/uploads/{self.sample.sample_id}.sqn")
		self.sftp_client.close()
		print(f"Genbank .sqn file submitted via SFTP for {self.sample.sample_id}")

	def submit_email(self):
		self.zip_genbank_files()
		print(f"Genbank files ready for email submission for {self.sample.sample_id}")
		# Logic to email the zipped files would go here

	def submit(self):
		self.prepare_genbank_files()
		self.run_table2asn()

		if self.config['genbank_submission_method'] == 'sftp':
			self.submit_sftp()
		elif self.config['genbank_submission_method'] == 'email':
			self.submit_email()



# Create the SFTP client
sftp_client = SFTPClient(config.config)

# Perform BioSample submission
biosample_submission = BiosampleSubmission(sample)
biosample_submission.submit()

# Perform SRA submission
sra_submission = SRASubmission(sample, sftp_client)
sra_submission.submit()

# Perform Genbank submission
genbank_submission = GenbankSubmission(sample, config.config, sftp_client)
genbank_submission.submit()



# Example usage:
config_parser = SubmissionConfigParser("submission_config.yaml")
config_dict = config_parser.load_config()
sample = Sample(sample_id="IL0005", metadata_file="IL0005.tsv", fastq1="IL0005/raw_reads/LIY15306A2_2022_054_3005007722.R_1.mpx.fastq.gz", 
				fastq2="IL0005/raw_reads/LIY15306A2_2022_054_3005007722.R_2.mpx.fastq.gz", fasta_file="IL0005.fasta", gff_file="IL0005.tbl")
metadata_parser = MetadataParser("IL0005.tsv")
metadata_dict = metadata_parser.get_all_data()
submission = NCBISubmission(sample, config.config)
submission.submit()




class NCBISubmission:
	def __init__(self, sample, config):
		self.sample = sample
		self.config = config
		self.sftp_client = SFTPClient(self.config)
		self.submission_files_dir = f"{sample.sample_id}_submission_files"

	def prepare_submission(self):
		# Prepare files for submission
		self.sample.validate_files()

	def submit_biosample(self):
		# Code to prepare and submit to BioSample
		print(f"Submitting sample {self.sample.sample_id} to BioSample")

	def submit_sra(self):
		# Upload FASTQ files to SRA
		self.sftp_client.connect()
		self.sftp_client.upload_file(self.sample.fastq1, f"/uploads/{self.sample.sample_id}_fastq1.fastq")
		self.sftp_client.upload_file(self.sample.fastq2, f"/uploads/{self.sample.sample_id}_fastq2.fastq")
		self.sftp_client.close()

	def prepare_genbank_files(self):
		# Prepare the Genbank submission files using the provided function
		os.makedirs(self.submission_files_dir, exist_ok=True)
		create_genbank_files(self.config, self.sample.metadata_file, self.sample.fasta_file, self.sample.sample_id, self.submission_files_dir)
		print(f"Genbank files prepared for {self.sample.sample_id}")

	def run_table2asn(self):
		# Run the table2asn command using the provided function
		create_genbank_table2asn(self.sample.sample_id, self.submission_files_dir, self.sample.gff_file)
		print(f"Table2asn executed for {self.sample.sample_id}")

	def zip_genbank_files(self):
		# Create a zip file for Genbank submission using the provided function
		create_genbank_zip(self.sample.sample_id, self.submission_files_dir)
		print(f"Genbank submission files zipped for {self.sample.sample_id}")

	def submit_genbank_sftp(self):
		# Submit Genbank files via SFTP
		self.sftp_client.connect()
		self.sftp_client.upload_file(os.path.join(self.submission_files_dir, f"{self.sample.sample_id}.sqn"), f"/uploads/{self.sample.sample_id}.sqn")
		self.sftp_client.close()

	def submit_genbank_email(self):
		# Zipping the files to email
		self.zip_genbank_files()
		# You can add an email function here to automate sending an email with the zip file as an attachment.
		print(f"Genbank files ready for email submission for {self.sample.sample_id}")

	def submit_genbank(self):
		# First, prepare Genbank files
		self.prepare_genbank_files()
		# Run table2asn to create .sqn file
		self.run_table2asn()

		# Determine how to submit Genbank files based on config
		if self.config['genbank_submission_method'] == 'sftp':
			self.submit_genbank_sftp()
		elif self.config['genbank_submission_method'] == 'email':
			self.submit_genbank_email()

	def submit(self):
		self.prepare_submission()
		self.submit_biosample()
		self.submit_sra()
		if self.sample.fasta_file and self.sample.gff_file:
			self.submit_genbank()




#submission_name = "IL0005"
#config_file = "default_config.yaml"
#metadata_file = "IL0005.tsv"
#fasta_file = "IL0005.fasta"
#annotation_file = "IL0005.tbl"
#fastq1 = "IL0005/raw_reads/LIY15306A2_2022_054_3005007722.R_1.mpx.fastq.gz"
#fastq2 = "IL0005/raw_reads/LIY15306A2_2022_054_3005007722.R_2.mpx.fastq.gz"
#organism = "mpxv"
#genbank, biosample, sra, gisaid