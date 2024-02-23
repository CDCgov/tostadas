
# Python Libraries
import ftplib
import os
import sys
import time
import subprocess
import pandas as pd
from Bio import SeqIO
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

# Local imports
import submission_process


# Get program directory
PROG_DIR = os.path.dirname(os.path.abspath(__file__))

# Submit to NCBI
def submit_ncbi(database, submission_name, submission_dir, config_dict, submission_type):
	# Get the directory that stores all submission files
	submission_files_dir = os.path.join(submission_dir, submission_name, "submission_files", database)
	# Create submission name
	ncbi_submission_name = submission_name + "_" + database
	# Check user credentials
	submission_process.check_credentials(config_dict=config_dict, database="NCBI")
	# Create an empty submit.ready file if it not exists
	submit_ready_file = os.path.join(submission_dir, "submit.ready")
	open(submit_ready_file, 'w+').close()
	# Submit sequences to NCBI via FTP Server
	try:
		# Login into NCBI FTP Server
		FTP_HOST = submission_process.get_main_config()["PORTAL_NAMES"]["NCBI"]["FTP_HOST"]
		ftp = ftplib.FTP(FTP_HOST)
		ftp.login(user=config_dict["Username"], passwd=config_dict["Password"])
		print("\n"+"Uploading submission files to NCBI-"+database, file=sys.stdout)
		print("Performing a '" + submission_type + "' submission", file=sys.stdout)
		print("If this is not a '" + submission_type + "' submission, interrupts submission immediately.", file=sys.stdout)
		print("\n"+"Connecting to NCBI FTP Server", file=sys.stdout)
		print("Submission name: " + submission_name, file=sys.stdout)
		# CD to to test/production folder
		ftp.cwd(submission_type)
		# Create submission directory if it does not exist
		if ncbi_submission_name not in ftp.nlst():
			ftp.mkd(ncbi_submission_name)
		# CD to submission folder
		ftp.cwd('submit')
		ftp.cwd(ncbi_submission_name)
		print("Submitting '" + submission_name + "'", file=sys.stdout)
		# Upload submission xml
		res = ftp.storlines("STOR " + "submission.xml", open(os.path.join(submission_files_dir, "submission.xml"), 'rb'))
		if not res.startswith('226 Transfer complete'):
			print('Submission.xml upload failed.', file=sys.stderr)
			sys.exit(1)
		# Upload raw reads
		if "SRA" in database:
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
							res = ftp.storbinary("STOR " + os.path.basename(line), open(line, 'rb'))
							if not res.startswith('226 Transfer complete'):
								print('SRA file upload failed. Try again.', file=sys.stderr)
								sys.exit(1)
						else:
							print("Error: Uploading files to SRA database failed. Possibly files have been moved or this is not a valid file: " + line, file=sys.stderr)
							sys.exit(1)
		elif "GENBANK" in database:
			res = ftp.storbinary("STOR " + submission_name + ".zip", open(os.path.join(submission_files_dir, submission_name + ".zip"), 'rb'))
			if not res.startswith('226 Transfer complete'):
				print("Uploading " + os.path.join(submission_files_dir, submission_name + ".zip") + " failed.", file=sys.stderr)
				sys.exit(1)
		try:
			res = ftp.storlines("STOR " + "submit.ready", open(submit_ready_file, 'rb'))
			complete = True
		except Exception as err: 
			if str(err).startswith('Error:550 submit.ready: Permission denied'):
				print('The submission has been submitted and currently in pending.', file=sys.stdout)
			else:
				print(err, file=sys.stderr)
				sys.exit(1)
		if (complete == True) and (not res.startswith('226 Transfer complete')):
			print('submit.ready upload failed.', file=sys.stderr)
			sys.exit(1)
	except ftplib.all_errors as e:
		print("\n" + 'Error:' + str(e), file=sys.stderr)
		sys.exit(1)

# Submit to GISAID
def submit_gisaid(organism, database, submission_dir, submission_name, config_dict, gisaid_cli, submission_status_file, submission_type):
	# Get the directory that stores all submission files
	submission_files_dir = os.path.join(submission_dir, submission_name, "submission_files", database)
	# Gather all required files
	metadata = os.path.join(submission_files_dir, "metadata.csv")
	orig_metadata = os.path.join(submission_files_dir, "orig_metadata.csv")
	fasta = os.path.join(submission_files_dir, "sequence.fsa")
	orig_fasta = os.path.join(submission_files_dir, "orig_sequence.fsa")
	# Extract user credentials (e.g. username, password, client-id)
	submission_process.check_credentials(config_dict=config_dict, database="GISAID")	
	# Output message
	print("\n"+"Uploading submission files to GISAID-"+organism, file=sys.stdout)
	print("Performing a '" + submission_type + "' submission with Client-Id: " + config_dict["Client-Id"], file=sys.stdout)
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
		command = subprocess.run([gisaid_cli, "upload", "--username", config_dict["Username"], "--password", config_dict["Password"], "--clientid", config_dict["Client-Id"], "--metadata", metadata, "--fasta", fasta, "--log", log_file, "--debug"],
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
def sendmail(database, submission_name, submission_dir, config_dict, test):
	# Create a database subfolder within the submission directory to dump all submission files
	submission_files_dir = os.path.join(submission_dir, submission_name, "submission_files", database)
	# Create submission files directory
	os.makedirs(submission_files_dir, exist_ok=True)
	TABLE2ASN_EMAIL = submission_process.get_main_config()["PORTAL_NAMES"]["NCBI"]["TABLE2ASN_EMAIL"]
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
