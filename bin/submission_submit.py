#!/usr/bin/env python3

# Python Libraries
import pysftp
#import ftplib
import os
import sys
import time
import argparse
import yaml
import subprocess
import pandas as pd
from datetime import datetime
from Bio import SeqIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Define organsim choices
ORGANISM_CHOICES = ["OTHER", "FLU", "COV"]


# Define program arguments and commands
def get_args():
	"""
	Argument parser setup and build.
	"""
	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
									 description='Automate the process of batch uploading consensus sequences and metadata to databases of your choices')
	parser.add_argument("--submission_name",
		help='Name of the submission',
		required=True)	
	parser.add_argument("--config_file",
		help="Config file stored in submission directory",
		required=True)
	parser.add_argument("--metadata_file",
		help="Metadata file stored in submission directory",
		required=True)
	parser.add_argument("--test",
		help="Whether to perform a test submission.",
		required=False,
		action="store_const",
		default=False,
		const=True)
	parser.add_argument("--fasta_file",
		help="Fasta file stored in submission directory",
		required=False)	
	parser.add_argument("--annotation_file",
		help="An annotation file to add to a Table2asn submission",
		required=False)
	parser.add_argument("--fastq1",
		help="Fastq R1 file to be submitted",
		required=False)	
	parser.add_argument("--fastq2",
		help="Fastq R2 file to be submitted",
		required=False)	
	parser.add_argument("--organism",
		help="Type of organism data",
		choices=ORGANISM_CHOICES,
		type=str.upper,
		default=ORGANISM_CHOICES[0],
		required=True)
	parser.add_argument("--genbank",
		help="Optional flag to run Genbank submission",
		action="store_const",
		default=False,
		const=True)
	parser.add_argument("--biosample",
		help="Optional flag to run BioSample submission",
		action="store_const",
		default=False,
		const=True)
	parser.add_argument("--sra",
		help="Optional flag to run SRA submission",
		action="store_const",
		default=False,
		const=True)
	parser.add_argument("--gisaid",
		help="Optional flag to run GISAID submission",
		action="store_const",
		default=False,
		const=True)

	args = parser.parse_args()
	return args

# Check the config file
def get_config(config_file, gisaid_submission):
	# Read in config file
	with open(config_file, "r") as f:
		config_dict = yaml.load(f, Loader=yaml.BaseLoader) # Load yaml as str only
	if type(config_dict) is dict:
		for k, v in config_dict.items():
			# If GISAID submission, check that GISAID keys have values
			if gisaid_submission:
				if k.startswith('GISAID') and not v:
					print("Error: There are missing values in the config file.", file=sys.stderr)
					sys.exit(1)					
			else:
				# If NCBI submission, check that non-GISAID keys have values (note: this only check top-level keys)
				if not k.startswith('GISAID') and not v:
					print("Error: There are missing values in the config file.", file=sys.stderr)
					sys.exit(1)	
	else:	
		print("Error: Config file is incorrect. File must has a valid yaml format.", file=sys.stderr)
		sys.exit(1)
	return config_dict

# Read in metadata file
def get_metadata(metadata_file):
	# Read in metadata file
	metadata = pd.read_csv(metadata_file, sep = '\t', header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False, na_filter=False)
	# Check if empty
	if metadata.empty:
		print("Error: Metadata file is empty.", file=sys.stderr)
		sys.exit(1)
	# Remove rows if entirely empty
	metadata = metadata.dropna(how="all")
	# Remove extra spaces from column names
	metadata.columns = metadata.columns.str.strip()
	return metadata

# Check user credentials information
def check_credentials(config_dict, database):
	# If database is sra, biosample, or genbank
	if database != "gisaid":
		# Check username
		if ("NCBI_username" in config_dict.keys()) and ((config_dict["NCBI_username"] is not None) and (config_dict["NCBI_username"] != "")):
			pass
		elif "NCBI_username" not in config_dict.keys:
			print("Error: there is no Submission > " + database + " > NCBI Username information in config file.", file=sys.stderr)
			sys.exit(1)
		else:
			print("Error: Submission > " + database + " > NCBI_username in the config file cannot be empty.", file=sys.stderr)
			sys.exit(1)
		# Check password
		if ("NCBI_password" in config_dict.keys()) and ((config_dict["NCBI_password"] is not None) and (config_dict["NCBI_password"] != "")):
			pass
		elif "NCBI_password" not in config_dict.keys():
			print("Error: there is no Submission > " + database + " > NCBI password information in config file.", file=sys.stderr)
			sys.exit(1) 
		else:
			print("Error: Submission > " + database + " > NCBI_password in the config file cannot be empty.", file=sys.stderr)
			sys.exit(1)
	# If database is GISAID
	elif database == "gisaid":
		if ("GISAID_client-id" in config_dict.keys() and ((config_dict["GISAID_client-id"] is not None) and (config_dict["GISAID_client-id"] != ""))):
			pass
		elif "GISAID_client-id" not in config_dict.keys():
			print("Error: there is no Submission > " + database + " > GISAID Client-Id information in config file.", file=sys.stderr)
			sys.exit(1)
		else:
			print("Error: Submission > " + database + " > GISAID Client-Id in the config file cannot be empty.", file=sys.stderr)
			sys.exit(1)


# Create submission log csv
def create_submission_log(database, submission_position, organism, submission_name, config_file, submission_log_file, submission_status, submission_id, annotation_file, submission_type):
	# If file doesn't exist create it
	submission_log_file = os.path.join(os.getcwd(), f"{submission_name}_submission_log.csv")
	if os.path.isfile(submission_log_file) == True:
		df = pd.read_csv(submission_log_file, header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False)
	else:
		df = pd.DataFrame(columns = ["Submission_Name", "Organism", "Database", "Submission_Position", "Submission_Type", "Submission_Date", "Submission_Status", "Submission_Directory", "Config_File", "Annotation_File", "Update_Date"])
	# Fill in the log field if it exists, otherwise create new
	df_partial = df.loc[(df["Organism"] == organism) & (df["Database"] == database) & (df["Submission_Directory"] == os.getcwd()) & (df["Submission_Name"] == submission_name) & (df["Submission_Type"] == submission_type)]
	# Update existing field	
	if df_partial.shape[0] > 0:
		df.loc[df_partial.index.values, "Submission_Position"] = submission_position			
		df.loc[df_partial.index.values, "Submission_Status"] = submission_id + ";" + submission_status
		df.loc[df_partial.index.values, "Annotation_File"] = annotation_file
		df.loc[df_partial.index.values, 'Update_Date'] = datetime.now().strftime("%Y-%m-%d")
	else:
		# Create new field
		status = submission_id + ";" + submission_status
		new_entry = {'Submission_Name': submission_name,
					 'Organism': organism,
					 'Database': database,
					 'Submission_Position': submission_position,
					 'Submission_Type': submission_type,
					 'Submission_Date': datetime.now().strftime("%Y-%m-%d"),
					 'Submission_Status': status,
					 'Submission_Directory': os.getcwd(),
					 'Config_File': config_file,
					 'Annotation_File': annotation_file,
					 'Update_Date': datetime.now().strftime("%Y-%m-%d")
					}
		df.loc[len(df)] = new_entry
	df.to_csv(submission_log_file, header = True, index = False)

# Submit to NCBI
def submit_ncbi(database, submission_name, config_dict, submission_type):
	# Get the directory that stores all submission files
	submission_files_dir = os.path.join(os.getcwd(), submission_name, database)
	# Create submission name
	ncbi_submission_name = submission_name + "_" + database
	# Check user credentials
	check_credentials(config_dict=config_dict, database="NCBI")
	# Create an empty submit.ready file if it not exists
	submit_ready_file = os.path.join(os.getcwd(), "submit.ready")
	open(submit_ready_file, 'w+').close()
	# Submit sequences to NCBI via FTP Server
	
	try:
		cnopts = pysftp.CnOpts()
		cnopts.hostkeys = None  # Disable host key checking for simplicity, but it's recommended to configure host keys

		# Login into NCBI FTP Server
		SFTP_HOST = config_dict["NCBI_ftp_host"]
		SFTP_USERNAME = config_dict["NCBI_username"]
		SFTP_PASSWORD = config_dict["NCBI_password"]

		with pysftp.Connection(SFTP_HOST, username=SFTP_USERNAME, password=SFTP_PASSWORD, cnopts=cnopts) as sftp:
			print("\n"+"Uploading submission files to NCBI-"+database, file=sys.stdout)
			print("Performing a '" + submission_type + "' submission", file=sys.stdout)
			print("If this is not a '" + submission_type + "' submission, interrupts submission immediately.", file=sys.stdout)
			print("\n"+"Connecting to NCBI FTP Server", file=sys.stdout)
			print("Submission name: " + submission_name, file=sys.stdout)
		
		# CD into submit dir
		sftp.cwd('submit')

		# CD to to test/production folder
		sftp.cwd(submission_type)

		# Create submission directory if it does not exist
		if ncbi_submission_name not in sftp.nlst():
			sftp.mkd(ncbi_submission_name)
		
		# CD to submission folder
		sftp.cwd(ncbi_submission_name)

		print("Submitting '" + submission_name + "'", file=sys.stdout)

		# Upload submission xml
		submission_xml_path = os.path.join(submission_files_dir, "submission.xml")
		sftp.put(submission_xml_path, "submission.xml")

		# Upload raw reads
		if "sra" in database:
			raw_read_location = os.path.join(submission_files_dir, "raw_reads_location.txt")
			if os.path.isfile(raw_read_location) is False:
				print("Error: Submission " + submission_name + " is missing raw reads file at " + raw_read_location, file=sys.stderr)
				sys.exit(1)
			else:
				# Upload SRA files
				with open(raw_read_location, "r") as file:
					for line in file:
						line = line.strip()
						if line is None or line == "":
							continue
						elif os.path.isfile(line):
							print('Uploading FASTQs for ', submission_name)
							sftp.put(line, os.path.basename(line))
						else:
							print("Error: Uploading files to SRA database failed. Possibly files have been moved or this is not a valid file: " + line, file=sys.stderr)
							sys.exit(1)
		#elif "genbank" in database:
		# Note: not supporting Genbank zip file upload ?
		#	zip_path = os.path.join(submission_files_dir, submission_name + ".zip")
		#		sftp.put(zip_path, submission_name + ".zip")
		try:
			submit_ready_path = os.path.join(submission_files_dir, "submit.ready")
			sftp.put(submit_ready_path, "submit.ready")
			complete = True
		except Exception as err: 
			if str(err).startswith('Error:550 submit.ready: Permission denied'):
				print('The submission has been submitted and currently in pending.', file=sys.stdout)
			else:
				print(err, file=sys.stderr)
				sys.exit(1)
		if complete:
			print('Submission complete.')
		else:
			print('submit.ready upload failed.', file=sys.stderr)
			sys.exit(1)
	except Exception as e:
		print("\n" + 'Error:' + str(e), file=sys.stderr)
		sys.exit(1)

# Read output log from gisaid submission script
def read_gisaid_log(log_file, submission_status_file):
	if os.path.isfile(log_file) is False:
		print("Error: GISAID log file does not exist at: "+log_file, file=sys.stderr)
		print("Error: Either a submission has not been made or log file has been moved.", file=sys.stderr)
		print("Try to re-upload the sequences again.", file=sys.stderr)
		sys.exit(1)
	if os.path.isfile(submission_status_file) is False:
		print("Error: GISAID submission status file does not exist at: "+submission_status_file, file=sys.stderr)
		print("Error: Either a submission has not been made or file has been moved.", file=sys.stderr)
		print("Try to re-upload the sequences again.", file=sys.stderr)
		sys.exit(1)
	# Read in submission status csv
	submission_status = pd.read_csv(submission_status_file, header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False)
	submission_status = submission_status.fillna("")
	# Read in log file
	with open(log_file) as f:
		while True:
			line = f.readline()
			if not line:
				break
			else:
				# Get sample or segment accession
				if "epi_isl".upper() in line.upper():
					column_name = "gs-sample_name"
					sample_name = list(set(filter(lambda x: (x.upper() in line.upper())==True, submission_status[column_name])))
					accession_id = "epi_isl_id" 
					accession = re.search("EPI_ISL_[1-9]+", line)
				elif "epi_id".upper() in line.upper():
					column_name = "gs-sequence_name"
					sample_name = list(set(filter(lambda x: (x.upper() in line.upper())==True, submission_status[column_name])))
					accession_id = "epi_id" 
					accession = re.search("EPI[1-9]+", line)
				else:
					continue
				# Get the accession number only
				if accession is not None:
					start = accession.span()[0]
					end = accession.span()[1]
					accession_number = line[start:end]
					sample_message = submission_status.loc[submission_status[column_name].isin(sample_name), "gisaid_message"].astype(str)
					submission_status.loc[submission_status[column_name].isin(sample_name), ("gisaid_accession_" + accession_id)] = accession_number
					submission_status.loc[submission_status[column_name].isin(sample_name), "gisaid_message"] = sample_message + line
				else:
					continue
	# Save submission status df
	submission_status.to_csv(submission_status_file, header = True, index = False)
	not_submitted = submission_status[~submission_status["gisaid_accession_epi_isl_id"].str.contains("EPI", na=False)].copy()
	return not_submitted[["gs-sample_name", "gs-sequence_name"]]

# Submit to GISAID
def submit_gisaid(organism, database, submission_name, config_dict, gisaid_cli, submission_status_file, submission_type):
	# Get the directory that stores all submission files
	submission_files_dir = os.path.join(os.getcwd(), submission_name, database)
	# Gather all required files
	metadata = os.path.join(submission_files_dir, "metadata.csv")
	orig_metadata = os.path.join(submission_files_dir, "orig_metadata.csv")
	fasta = os.path.join(submission_files_dir, "sequence.fsa")
	orig_fasta = os.path.join(submission_files_dir, "orig_sequence.fsa")
	# Extract user credentials (e.g. username, password, client-id)
	check_credentials(config_dict=config_dict, database="gisaid")	
	# Output message
	print("\n"+"Uploading submission files to GISAID-"+organism, file=sys.stdout)
	print("Performing a '" + submission_type + "' submission with Client-Id: " + config_dict["GISAID_client-id"], file=sys.stdout)
	print("If this is not a '" + submission_type + "' submission, interrupts submission immediately.", file=sys.stdout)
	# Set number of attempt to 3 if erroring out occurs
	attempts = 1
	# Submit to GISAID
	while attempts <= 3:
		print("\n"+"Submission attempt: " + str(attempts), file=sys.stdout)
		# Create a log submission for each attempt
		log_file = os.path.join(submission_files_dir, "gisaid_upload_log_" + str(attempts) + ".txt")
		# If log file exists, removes it
		if os.path.isfile(log_file) == True:
			os.remove(log_file)
		# Upload submission 
		command = subprocess.run([gisaid_cli, "upload", "--username", config_dict["GISAID_username"], "--password", config_dict["GISAID_password"], "--clientid", config_dict["GISAID_client-id"], "--metadata", metadata, "--fasta", fasta, "--log", log_file, "--debug"],
			cwd=submission_files_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		# Check if uploading is successful
		if command.returncode != 0:
			print("Error: upload command error", file=sys.stderr)
			print(command.stdout)
			print(command.stderr)
			sys.exit(1)
		# Check if log file exists
		while not os.path.exists(log_file):
			time.sleep(10)
		# Check submission log to see if all samples are uploaded successfully
		not_submitted_df = submission_process.read_gisaid_log(log_file=log_file, submission_status_file=submission_status_file)
		# If submission completed, no more attempts
		if not_submitted_df.empty:
			print("Uploading successfully", file=sys.stdout)
			print("Status report is stored at: " + submission_status_file, file=sys.stdout)
			print("Log file is stored at: " + submission_files_dir + "/gisaid_upload_log_attempt_" + str(attempts) +  ".txt", file=sys.stdout)
			return "processed-ok"
		else:
			# If submission is not completed, try again
			metadata_df = pd.read_csv(metadata, header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False)
			if "FLU" in organism:
				column_name = "Isolate_Name"
			elif "COV" in organism:
				column_name = "virus_name"
			metadata_df = metadata_df.merge(not_submitted_df, how="inner", left_on=column_name, right_on="gs-sample_name")
			fasta_names = metadata_df["gs-sequence_name"].tolist()
			metadata_df = metadata_df.drop(columns=["gs-sample_name", "gs-sequence_name"])
			metadata_df.to_csv(orig_metadata, header = True, index = False)
			fasta_dict = []
			with open(orig_fasta, "r") as fsa:
				records = SeqIO.parse(fsa, "fasta")
				for record in records:
					if record.id in fasta_names:
						fasta_dict.append(record)
			with open(fasta, "w+") as fasta_file:
				SeqIO.write(fasta_dict, fasta_file, "fasta")
			attempts += 1
	if not not_submitted_df.empty:
		print("Error: " + str(len(not_submitted_df.index)) + " sample(s) failed to upload to GISAID", file=sys.stderr)
		print("Please check status report at: " + submission_status_file, file=sys.stdout)
		print("Please check log file at: " + submission_files_dir + "/gisaid_upload_log_attempt_{1,2,3}.txt", file=sys.stderr)
		return "Error-Submission-Incomplete"

# Send table2asn file through email
def sendmail(database, submission_name, config_dict, test):
	# Create a database subfolder within the submission directory to dump all submission files
	submission_files_dir = os.path.join(os.getcwd(), submission_name, database)
	# Create submission files directory
	os.makedirs(submission_files_dir, exist_ok=True)
	TABLE2ASN_EMAIL = config_dict["table2asn_email"]
	submission_status = "processed-ok"
	try:
		msg = MIMEMultipart('multipart')
		msg['Subject'] = submission_name + " table2asn submission"
		from_email = config_dict["Description"]["Organization"]["Submitter"]["@email"]
		to_email = []
		cc_email = []
		if test == True:
			to_email.append(config_dict["Description"]["Organization"]["Submitter"]["@email"])
		else:
			to_email.append(TABLE2ASN_EMAIL)
			cc_email.append(config_dict["Description"]["Organization"]["Submitter"]["@email"])
		if config_dict["Description"]["Organization"]["Submitter"]["@alt_email"]:
			cc_email.append(config_dict["Description"]["Organization"]["Submitter"]["@alt_email"])
		msg['From'] = from_email
		msg['To'] = ", ".join(to_email)
		if len(cc_email) != 0:
			msg['Cc'] = ", ".join(cc_email)
		with open(os.path.join(submission_files_dir, submission_name + ".sqn"), 'rb') as file_input:
			part = MIMEApplication(file_input.read(), Name=submission_name + ".sqn")
		part['Content-Disposition'] = "attachment; filename=" + submission_name + ".sqn"
		msg.attach(part)
		s = smtplib.SMTP('localhost')
		s.sendmail(from_email, to_email, msg.as_string())
	except Exception as e:
		print("Error: Unable to send mail automatically. If unable to email, submission can be made manually using the sqn file.", file=sys.stderr)
		print("sqn_file:" + os.path.join(submission_files_dir, submission_name + ".sqn"), file=sys.stderr)
		print(e, file=sys.stderr)
		submission_status = "processed-ok-email-failure"
	return submission_status


def main():

	args = get_args()
	
	# required args
	submission_name = args.submission_name
	organism = args.organism
	config_file = args.config_file
	# Check if config file exists
	if os.path.isfile(config_file) == False:
		print("There is no config file at " + config_file, file=sys.stderr)
		sys.exit(1)
	metadata_file = args.metadata_file
	# Check if metadata file exists
	if os.path.isfile(metadata_file) == False:
		print("There is no metadata at " + metadata_file, file=sys.stderr)
		sys.exit(1)
	# optional args
	if "fasta_file" in args:
		fasta_file = args.fasta_file
		# Check if fasta file exists
		if os.path.isfile(fasta_file) == False:
			print("There is no fasta file at " + fasta_file, file=sys.stderr)
			sys.exit(1)
	else:
		fasta_file = None
	fastq_files = [("fastq1", args.fastq1), ("fastq2", args.fastq2)]
	for fastq_name, fastq_file in fastq_files:
		if fastq_file:  # Check if each fastq file exists
			if not os.path.isfile(fastq_file):
				print(f"There is no {fastq_name} file at {fastq_file}", file=sys.stderr)
				sys.exit(1)
			locals()[fastq_name] = fastq_file # Dynamically create vars fastq1 and fastq2
		else:
			locals()[fastq_name] = None
	if "annotation_file" in args:
		annotation_file = args.annotation_file
		# Check if gff file exists
		if os.path.isfile(annotation_file) == False:
			print("Error: annotation file does not exist at: " + annotation_file, file=sys.stderr)
			sys.exit(1)
	else:
		annotation_file = None
	if "test" in args:
		test = args.test
		submission_type = "Test"
	else:
		test = False
		submission_type = "Production"
	database = []
	genbank_submission = sra_submission = biosample_submission = gisaid_submission = False
	if "genbank" in args:
		genbank_submission = True
		database.append('genbank')
	if "sra" in args:
		sra_submission = True
		database.append('sra')
	if "biosample" in args:
		biosample_submission = True
		database.append('biosample')
	if "gisaid" in args:
		gisaid_submission = True
		database.append('gisaid')

	submission_status_file = os.path.join(os.getcwd(), submission_name, "submission_report_status.csv")
	
	# IF database is GISAID, check if CLI is downloaded and store in the correct directory
	gisaid_cli = os.path.join(os.getcwd(), "gisaid_cli", organism.lower()+"CLI", organism.lower()+"CLI") if "gisaid" in database else None
	# Check if the gisaid_cli exists
	if (gisaid_cli is not None) and os.path.isfile(gisaid_cli) == False:
		print("There is no GISAID CLI package for " + organism + " located at "+ gisaid_cli, file=sys.stderr)
		print("Please download the GISAID " + organism + " CLI package from the GISAID platform", file=sys.stderr)
		print("Extract the zip file and place a copy of the CLI binary at "+ gisaid_cli, file=sys.stderr)
		sys.exit(1)	
	
	# Check config file
	config_dict = get_config(config_file=config_file, gisaid_submission=gisaid_submission)
	# Check metadata file
	metadata = get_metadata(metadata_file=metadata_file)

	# Submit to databases
	for database_name in database:
		# BioSample and SRA can be submitted together but to add accessions to GenBank they must be fully processed
		if database_name in ["biosample", "sra"]:	
			if ("gisaid" in database) and (int(config_dict["gisaid"]["Submission_Position"]) == 1):
				submission_position = 2
			else:
				submission_position = 1
			submission_status = "submitted"
			submission_id = "pending"
			submit_ncbi(submission_name=submission_name, database=database_name, config_dict=config_dict["NCBI"], submission_type=submission_type)
		elif "GENBANK" in database_name:
			if ("GISAID" in database) and (int(config_dict["GISAID"]["Submission_Position"]) == 1):
				submission_position = 2
			else:
				submission_position = 1
			# Don't submit to GENBANK yet if BIOSAMPLE OR SRA is given or if GISAID is given and the submission_position is set to primary
			if any(x in ["BIOSAMPLE", "SRA"] for x in database) or (submission_position == 2):
				submission_status = "---"
				submission_id = "---"
			elif table2asn == True:
				# GenBank Table2asn submission
				if send_email == True:
					sendmail(database=database_name, submission_name=submission_name, config_dict=config_dict["NCBI"], test=test)
					submission_status = "processed-ok"
				else:
					submission_status = "email not sent"
				submission_id = "Table2asn"
			else:
				# GenBank FTP submission
				submit_ncbi(database=database_name, submission_name=submission_name, config_dict=config_dict["NCBI"], submission_type=submission_type)
				submission_status = "submitted"
				submission_id = "pending"
		elif "GISAID" in database_name:
			# Don't submit to GISAID yet if any of NCBI databases is given and the submission position is set to secondary
			if  any(x in ["BIOSAMPLE", "SRA", "GENBANK"] for x in database) and int(config_dict["GISAID"]["Submission_Position"]) == 2:
				submission_position = 2
				submission_status = "---"
				submission_id = ""
			else:
				submission_position = 1
				submission_status = submit_gisaid(organism=organism, database=database_name, submission_name=submission_name, config_dict=config_dict["GISAID"], gisaid_cli=gisaid_cli,  submission_status_file=submission_status_file, submission_type=submission_type)
				submission_id = ""
		create_submission_log(database=database_name, submission_position=submission_position, organism=organism, submission_name=submission_name, config_file=config_file, submission_status=submission_status, submission_id=submission_id, annotation_file=annotation_file, submission_type=submission_type)




if __name__ == "__main__":
	main() 