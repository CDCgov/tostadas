#!/usr/bin/env python3

import os
import sys
import shutil
from datetime import datetime
import argparse
import yaml
from lxml import etree
import xml.etree.ElementTree as ET
import xml.dom.minidom as minidom  # Import minidom for pretty-printing
import os
import math  # Required for isnan check
import csv
import time
import subprocess
import pandas as pd
from abc import ABC, abstractmethod
#import paramiko
import ftplib
from nameparser import HumanName
from zipfile import ZipFile

def fetch_and_parse_report(submission_object, client, submission_id, submission_dir, output_dir, type):
    # Connect to the FTP/SFTP client
    client.connect()
    client.change_dir('submit')  # Change to 'submit' directory
    client.change_dir(submission_dir)  # Change to Test or Prod
    client.change_dir(f"{submission_id}_{type}")  # Change to sample-specific directory
    # Check if report.xml exists and download it
    report_file = "report.xml"
    if client.file_exists(report_file):
        print(f"Report found at {report_file}")
        report_local_path = os.path.join(output_dir, 'report.xml')
        client.download_file(report_file, report_local_path)
        # Parse the report.xml
        parsed_report = submission_object.parse_report_xml(report_local_path)
        # Save as CSV to top level sample submission folder
        # output_dir = 'path/to/results/sample_name/database' and we want to save a report for all samples to 'path/to/results/'
        report_filename = os.path.join(os.path.dirname(os.path.dirname(output_dir)), 'submission_report.csv')
        print(f"save_report_to_csv inputs are: {parsed_report}, {report_filename}")
        submission_object.save_report_to_csv(parsed_report, report_filename)
        return parsed_report
    else:
        print(f"No report found for submission {submission_id}")
        return None

def submission_main():
    """ Main for initiating submission steps
    """
    # Get all parameters from argparse
    parameters_class = GetParams()
    parameters = parameters_class.parameters

    # Get the submission config file dictionary
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
        annotation_file=parameters.get('annotation_file'),
        species = parameters['species']
    )
    # Perform file validation
    sample.validate_files()

    # Get list of all databases to submit to (or update)
    databases = [db for db in parameters if parameters[db] and db in ['biosample', 'sra', 'genbank', 'gisaid']]

    # Set the submission directory (test or prod)
    if parameters['test']:
        submission_dir = 'Test'
    else:
        submission_dir = 'Prod'

    # Prepare all submissions first (so files are generated even if submission step fails)
    if parameters['biosample']:
        biosample_submission = BiosampleSubmission(sample, parameters, config_dict, metadata_df, f"{parameters['output_dir']}/{parameters['submission_name']}/biosample", 
                                                   parameters['submission_mode'], submission_dir, 'biosample')
    if parameters['sra']:
        sra_submission = SRASubmission(sample, parameters, config_dict, metadata_df, f"{parameters['output_dir']}/{parameters['submission_name']}/sra",
                                       parameters['submission_mode'], submission_dir, 'sra')
    if parameters['genbank']:
        genbank_submission = GenbankSubmission(sample, parameters, config_dict, metadata_df, f"{parameters['output_dir']}/{parameters['submission_name']}/genbank",
                                               parameters['submission_mode'], submission_dir, 'genbank')

    # If submission mode
    if parameters['submit']:
        # Submit all prepared submissions and fetch report once
        if parameters['biosample']:
            biosample_submission.submit()
        if parameters['sra']:
            sra_submission.submit()
        if parameters['genbank']:
            if sample.ftp_upload:
                genbank_submission.run_table2asn()
                genbank_submission.submit()
            else:
                genbank_submission.prepare_files()
                genbank_submission.run_table2asn()
                if parameters['send_email']:
                    genbank_submission.sendemail()

    # If update mode
    elif parameters['update']:
        start_time = time.time()
        timeout = 60  # todo: change to 300 seconds (5 minutes) or make user-optional
        
        while time.time() - start_time < timeout:
            if sample.ftp_upload:
                submission_objects = { 'biosample': biosample_submission, 'sra': sra_submission, 'genbank': genbank_submission }
            else:
                submission_objects = { 'biosample': biosample_submission, 'sra': sra_submission }
            for db in submission_objects.keys():
                submission_object = submission_objects[db]
                result = submission_object.update_report()  # Call the fetch_report function repeatedly
                if result:  # If report fetch is successful, break the loop
                    print("Report successfully fetched")
                    break
                time.sleep(10)  # Wait before retrying
            else:
                print("Timeout occurred while trying to fetch the report")

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
        parser.add_argument('--submit', action='store_true', help='Run the full submission process')
        parser.add_argument('--update', action='store_true', help='Run the update process to fetch and parse report')
        # optional parameters
        parser.add_argument("-o", "--output_dir", type=str, default='submission_outputs',
                            help="Output Directory for final Files, default is current directory")
        parser.add_argument("--test", help="Whether to perform a test submission.", required=False,	action="store_const", default=False, const=True)
        parser.add_argument("--fasta_file",	help="Fasta file to be submitted", required=False)
        parser.add_argument("--annotation_file", help="An annotation file to add to a Genbank submission", required=False)
        parser.add_argument("--fastq1", help="Fastq R1 file to be submitted", required=False)	
        parser.add_argument("--fastq2", help="Fastq R2 file to be submitted", required=False)
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
    def __init__(self, sample_id, metadata_file, fastq1, fastq2, species, fasta_file=None, annotation_file=None):
        self.sample_id = sample_id
        self.metadata_file = metadata_file
        self.fastq1 = fastq1
        self.fastq2 = fastq2
        self.fasta_file = fasta_file
        self.annotation_file = annotation_file
        self.species = species
        # ftp_upload is true if GenBank FTP submission is supported for that species, otherwise false
        self.ftp_upload = species in {"flu", "sars", "bacteria"} # flu, sars, bacteria currently support ftp upload to GenBank
    # todo: add (or ignore) validation for cloud files 
    def validate_files(self):
        files_to_check = [self.metadata_file, self.fastq1, self.fastq2]
        if self.fasta_file:
            files_to_check.append(self.fasta_file)
        if self.annotation_file:
            files_to_check.append(self.annotation_file)
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
    def parse_report_xml(self, report_path):
        # Parse the XML file and extract required information
        tree = ET.parse(report_path)
        root = tree.getroot()
        report_dict = {
            'submission_name': self.sample.sample_id,
            'submission_type': self.type,
            'submission_status': None,
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
        }
        for action in root.findall('Action'):
            db = action.attrib.get('target_db')
            status = action.attrib.get('status')
            accession = action.attrib.get('accession')
            message = action.find('Message').text if action.find('Message') is not None else ""
            if db == 'biosample':
                report_dict['biosample_status'] = status
                report_dict['biosample_accession'] = accession
                report_dict['biosample_message'] = message
            elif db == 'sra':
                report_dict['sra_status'] = status
                report_dict['sra_accession'] = accession
                report_dict['sra_message'] = message
            elif db == 'genbank':
                report_dict['genbank_status'] = status
                if status == 'processed-ok':
                    # Handle Genbank-specific logic (AccessionReport.tsv)
                    accession_report = action.find('AccessionReport')
                    if accession_report is not None:
                        report_dict['genbank_accession'] = accession_report.find('Accession').text
                        report_dict['genbank_release_date'] = accession_report.find('ReleaseDate').text
                report_dict['genbank_message'] = message
        return report_dict
    def save_report_to_csv(self, report_dict, csv_file):
        with open(csv_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=report_dict.keys())
            if not os.path.isfile(csv_file):
                writer.writeheader() # todo: need to use pandas to do this probably, not all keys are being written to the file 
            writer.writerow(report_dict)
        print(f"Submission report saved to {csv_file}")
    def submit_files(self, files, type):
        sample_subtype_dir = f'{self.sample.sample_id}_{type}' # samplename_<biosample,sra,genbank> (a unique submission dir)
        self.client.connect()
        self.client.change_dir('submit')  # Change to 'submit' directory
        self.client.change_dir(self.submission_dir) # Change to Test or Prod
        self.client.change_dir(sample_subtype_dir) # Change to unique dir for sample_destination
        for file_path in files:
            self.client.upload_file(file_path, f"{os.path.basename(file_path)}")
        print(f"Submitted files for sample {self.sample.sample_id}")
    def close(self):
        self.client.close()
    def fetch_report(self):
        if self.sample.ftp_upload:
            fetch_and_parse_report(self, self.client, self.sample.sample_id, self.submission_dir, self.output_dir, self.type)

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
    def download_file(self, remote_path, local_path):
        try:
            self.sftp.get(remote_path, local_path)
            print(f"Downloaded file from {remote_path} to {local_path}")
        except Exception as e:
            raise IOError(f"Failed to download {remote_path}: {e}")
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
    def download_file(self, remote_path, local_path):
        with open(local_path, 'wb') as f:
            self.ftp.retrbinary(f'RETR {remote_path}', f.write)
        print(f"Downloaded file from {remote_path} to {local_path}")
    def upload_file(self, file_path, destination_path):
        try:
            if file_path.endswith(('.fasta', '.fastq', '.fna', '.fsa', '.gff', '.gff3', '.gz', 'xml', '.sqn')):  
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
        contact_el = ET.SubElement(organization_el, 'Contact', {'email': self.safe_text(self.submission_config['Email'])})
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

# todo: don't think I need separate classes for each db
class BiosampleSubmission(XMLSubmission, Submission):
    def __init__(self, sample, parameters, submission_config, metadata_df, output_dir, submission_mode, submission_dir, type):
        # Properly initialize the base classes 
        XMLSubmission.__init__(self, sample, submission_config, metadata_df, output_dir) 
        Submission.__init__(self, sample, parameters, submission_config, output_dir, submission_mode, submission_dir, type) 
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
        # Create submit.ready file (without using Posix object because all files_to_submit need to be same type)
        submit_ready_file = os.path.join(self.output_dir, 'submit.ready')
        with open(submit_ready_file, 'w') as fp:
            pass 
        # Submit files
        files_to_submit = [submit_ready_file, self.xml_output_path]
        self.submit_files(files_to_submit, 'biosample')
        print(f"Submitted sample {self.sample.sample_id} to BioSample")
    # Trigger report fetching
    def update_report(self):
        self.fetch_report()

class SRASubmission(XMLSubmission, Submission):
    def __init__(self, sample, parameters, submission_config, metadata_df, output_dir, submission_mode, submission_dir, type):
        # Properly initialize the base classes 
        XMLSubmission.__init__(self, sample, submission_config, metadata_df, output_dir) 
        Submission.__init__(self, sample, parameters, submission_config, output_dir, submission_mode, submission_dir, type) 
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
        # Create submit.ready file (without using Posix object because all files_to_submit need to be same type)
        submit_ready_file = os.path.join(self.output_dir, 'submit.ready')
        with open(submit_ready_file, 'w') as fp:
            pass 
        # Submit files
        # todo: this assumes the fastq files are gzipped!!
        fastq1 = os.path.join(self.output_dir, f"{self.sample.sample_id}_R1.fq.gz")
        fastq2 = os.path.join(self.output_dir, f"{self.sample.sample_id}_R2.fq.gz")
        shutil.move( self.sample.fastq1, fastq1)
        shutil.move( self.sample.fastq2, fastq2)
        files_to_submit = [submit_ready_file, self.xml_output_path, fastq1, fastq2]
        self.submit_files(files_to_submit, 'sra')
        print(f"Submitted sample {self.sample.sample_id} to SRA")
    # Trigger report fetching
    def update_report(self):
        self.fetch_report()

class GenbankSubmission(XMLSubmission, Submission):
    def __init__(self, sample, parameters, submission_config, metadata_df, output_dir, submission_mode, submission_dir, type):
        # Properly initialize the base classes 
        XMLSubmission.__init__(self, sample, submission_config, metadata_df, output_dir) 
        Submission.__init__(self, sample, parameters, submission_config, output_dir, submission_mode, submission_dir, type)
        # Use the MetadataParser to extract metadata needed for GB submission
        parser = MetadataParser(metadata_df)
        self.top_metadata = parser.extract_top_metadata()
        self.genbank_metadata = parser.extract_genbank_metadata()
        self.biosample_metadata = parser.extract_biosample_metadata()
        # Generate the GenBank XML upon initialization only if sample.ftp_upload is True
        if self.sample.ftp_upload:
            self.xml_output_path = self.create_xml(output_dir)
    def add_action_block(self, submission):
        action = ET.SubElement(submission, "Action")
        add_files = ET.SubElement(action, "AddFiles", target_db="Genbank")
        file1 = ET.SubElement(add_files, "File", file_path=f"{self.sample.sample_id}.sqn")
        data_type1 = ET.SubElement(file1, "DataType")
        data_type1.text = "wgs-contigs-sqn"
    def add_attributes_block(self, submission):
        add_files = submission.find(".//AddFiles")   
        # Meta and Genome information
        meta_el = ET.SubElement(add_files, "Meta", content_type="XML")
        xml_content = ET.SubElement(meta_el, "XmlContent")
        genome = ET.SubElement(xml_content, "Genome")
        description = ET.SubElement(genome, "Description")
        assembly_metadata_choice = ET.SubElement(description, "GenomeAssemblyMetadataChoice")
        assembly_metadata = ET.SubElement(assembly_metadata_choice, "GenomeAssemblyMetadata")
        sequencing_technologies = ET.SubElement(assembly_metadata, "SequencingTechnologies", {"coverage": str(self.genbank_metadata['mean_coverage'])})
        technology = ET.SubElement(sequencing_technologies, "Technology")
        technology.text = self.safe_text(self.genbank_metadata['assembly_protocol'])
        assembly = ET.SubElement(assembly_metadata, "Assembly")
        method = ET.SubElement(assembly, "Method")
        method.text = self.safe_text(self.genbank_metadata['assembly_method'])
        genome_representation = ET.SubElement(description, "GenomeRepresentation")
        genome_representation.text = "Full"
        # Authors
        authors = self.genbank_metadata.get('authors')
        if authors and authors not in ["Not Provided", "NaN", ""]:
            sequence_authors = ET.SubElement(description, "SequenceAuthors")
            authors_list = authors.split('; ')
            
            for author in authors_list:
                author_el = ET.SubElement(sequence_authors, "Author")
                name_el = ET.SubElement(author_el, "Name")
                
                # Split the author's name into components
                name_parts = author.split()
                first_name = name_parts[0]
                last_name = name_parts[-1]
                middle_name = ' '.join(name_parts[1:-1]) if len(name_parts) > 2 else None
                
                # Add First element
                first_el = ET.SubElement(name_el, "First")
                first_el.text = first_name
                
                # Add Last element
                last_el = ET.SubElement(name_el, "Last")
                last_el.text = last_name
                
                # Add Middle element if there is one
                if middle_name:
                    middle_el = ET.SubElement(name_el, "Middle")
                    middle_el.text = middle_name
        # Publication
        #todo: db_type?
        publication = ET.SubElement(description, "Publication", status=self.safe_text(self.genbank_metadata['publication_status']), 
                                                                id=self.safe_text(self.genbank_metadata['publication_title']))
        db_type = ET.SubElement(publication, "DbType")
        db_type.text = "ePubmed"
        # Additional attributes
        ET.SubElement(description, "ExpectedFinalVersion").text = "Yes"
        ET.SubElement(description, "AnnotateWithPGAP").text = "No"
        # BioProject and BioSample references
        attribute_ref1 = ET.SubElement(add_files, "AttributeRefId")
        ref_id1 = ET.SubElement(attribute_ref1, "RefId")
        primary_id1 = ET.SubElement(ref_id1, "PrimaryId", db="BioProject")
        primary_id1.text = self.safe_text(self.top_metadata['ncbi-bioproject'])
        attribute_ref2 = ET.SubElement(add_files, "AttributeRefId")
        ref_id2 = ET.SubElement(attribute_ref2, "RefId")
        primary_id2 = ET.SubElement(ref_id2, "PrimaryId", db="BioSample")
        # todo: need to figure out BioSample (and don't forget self.safe_text())
        primary_id2.text = ""
        # Identifier
        identifier = ET.SubElement(add_files, "Identifier")
        spuid = ET.SubElement(identifier, "SPUID", spuid_namespace="NCBI")
        spuid.text = self.safe_text(self.top_metadata['ncbi-spuid_namespace'])
    # Functions for manually preparing files for table2asn + manual submission (where ftp upload not supported)
    def create_source_file(self):
        source_data = {
            "Sequence_ID": self.top_metadata.get("sequence_name"),
            "strain": self.top_metadata.get("sequence_name"),
            "BioProject": self.top_metadata.get("ncbi-bioproject"),
            "organism": self.biosample_metadata.get("organism"),
            "Collection_date": self.biosample_metadata.get("collection_date"),
            "country": self.biosample_metadata.get("geo_location"),
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
            "HOST_AGE": self.biosample_metadata.get("age"),
            "HOST_GENDER": self.biosample_metadata.get("sex"),
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
    def prepare_files(self):
        """ Prepare files for manual upload to GenBank because FTP support not available """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        # Create the source df
        # todo: that seq_id needs to be the genbank sequence id
        self.create_source_file()
        # Create Structured Comment file
        self.create_comment_file()
        # Create authorset file
        self.create_authorset_file()
        print(f"Genbank files prepared for {self.sample.sample_id}")
        # Zip the files for email submission
        renamed_fasta = os.path.join(f"{self.output_dir}/sequence.fsa")
        if not os.path.exists(renamed_fasta):
            shutil.move(self.sample.fasta_file, renamed_fasta)
        with ZipFile(os.path.join(self.output_dir, self.sample.sample_id + ".zip"), 'w') as zip:
            zip.write(os.path.join(self.output_dir, "authorset.sbt"), "authorset.sbt")
            zip.write(os.path.join(self.output_dir, "sequence.fsa"), "sequence.fsa")
            zip.write(os.path.join(self.output_dir, "source.src"), "source.src")
            zip.write(os.path.join(self.output_dir, "comment.cmt"), "comment.cmt")

    # Functions for running table2asn
    def get_gff_locus_tag(self):
        """ Read the locus lag from the GFF3 file for use in table2asn command"""
        locus_tag = None
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
        # If prepare_files() not run, move the fasta file to the genbank submission folder and rename it sequence.fsa
        renamed_fasta = os.path.join(f"{self.output_dir}/sequence.fsa")
        if not os.path.exists(renamed_fasta):
            shutil.move(self.sample.fasta_file, renamed_fasta)
        shutil.move(self.sample.annotation_file, self.output_dir)
        # Construct the table2asn command
        if self.sample.ftp_upload:
            cmd = [
                "table2asn",
                "-i", f"{self.output_dir}/sequence.fsa",
                "-o", f"{self.output_dir}/{self.sample.sample_id}.sqn",
                #"-indir", self.output_dir,
                #"-outdir", self.output_dir
            ]
        else:
            cmd = [
                "table2asn",
                "-i", f"{self.output_dir}/sequence.fsa",
                "-src-file", f"{self.output_dir}/source.src",
                "-o", f"{self.output_dir}/{self.sample.sample_id}.sqn",
                "-t", f"{self.output_dir}/authorset.sbt",
                "-f", f"{self.output_dir}/{self.sample.annotation_file}"
            ]
        if locus_tag:
            cmd.extend(["-locus-tag-prefix", locus_tag])
        if self.is_multicontig_fasta(renamed_fasta):
            cmd.append("-M")
            cmd.append("n")
            cmd.append("-Z")
        if os.path.isfile("comment.cmt"):
            cmd.append("-w")
            cmd.append("comment.cmt")
        # Run the command and capture errors
        print(cmd)
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
            if test == True:
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
        files_to_submit = [submit_ready_file, self.xml_output_path, f"{self.output_dir}/{self.sample.sample_id}.sqn", f"{self.output_dir}/sequence.fsa"]
        self.submit_files(files_to_submit, 'genbank')
        print(f"Submitted sample {self.sample.sample_id} to Genbank")
    # Trigger report fetching
    def update_report(self):
        self.fetch_report()


if __name__ == "__main__":
    submission_main()