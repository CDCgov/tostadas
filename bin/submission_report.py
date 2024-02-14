# Python Libraries
import pathlib
import pandas as pd
import sys
import os
import time
import re
import xmltodict
import xml.etree.ElementTree as ET
import requests
from Bio import SeqIO
import ftplib

# Local imports
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import submission_process

# Get program directory
PROG_DIR = os.path.dirname(os.path.abspath(__file__))

# Process NCBI Report file
def get_ncbi_process_report(database, submission_name, submission_files_dir, config_dict, submission_type):
	# Check user credentials
	submission_process.check_credentials(config_dict=config_dict, database="NCBI")
	# Create submission name
	ncbi_submission_name = submission_name + "_" + database
	# Login into NCBI FTP Server
	try:
		FTP_HOST = submission_process.get_main_config()["PORTAL_NAMES"]["NCBI"]["FTP_HOST"]
		ftp = ftplib.FTP(FTP_HOST)
		ftp.login(user=config_dict["Username"], passwd=config_dict["Password"])
		# CD to to test or production folder
		ftp.cwd(submission_type)
		# Check if submission name exists
		if ncbi_submission_name not in ftp.nlst():
			print("There is no submission with the name of '"+ ncbi_submission_name +"' on NCBI FTP server.", file=sys.stderr)
			print("Please try the submission again.", file=sys.stderr)
			sys.exit(1)
		# CD to submission folder
		ftp.cwd(ncbi_submission_name)
		# Check if report.xml exists
		if "report.xml" in ftp.nlst():
			print("Pulling down report.xml", file=sys.stdout)
			report_file = os.path.join(submission_files_dir, "report.xml")
			with open(report_file, 'wb') as f:
				ftp.retrbinary('RETR report.xml', f.write, 262144)
			return report_file
		else:
			print("The report.xml has not yet been generated.", file=sys.stdout)
			return None
	except ftplib.all_errors as e:
		print("\n" + "Error: " + str(e), file=sys.stderr)
		sys.exit(1)

# Read xml report and get status of the submission
def process_biosample_sra_report(database, report_file, submission_status_file):
	# # Read in report.xml
	tree = ET.parse(report_file)
	root = tree.getroot()
	xmlstr = ET.tostring(root, encoding='utf8', method='xml')
	# Read in submission status csv
	status_submission_df = pd.read_csv(submission_status_file, header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False)
	status_submission_df = status_submission_df.fillna("")
	status_submission_df.columns = status_submission_df.columns.str.strip()
	# Create sample ids that match ids in report.xml
	status_submission_df['report_sample_id'] = [re.sub(r"/", "_", x.lower()) for x in status_submission_df["ncbi-sample_name"].values.tolist()]
	# Convert xml to dictionary
	report_dict = xmltodict.parse(xmlstr)
	# Get submission status from report.xml
	try:
		submission_status = report_dict["SubmissionStatus"]["@status"]
	except:
		submission_status = "submitted"
	# Get submission id from report.xml
	try:
		submission_id = report_dict["SubmissionStatus"]["@submission_id"]
	except:
		submission_id = "pending"
	# Get status of individual samples from report.xml
	try:
		report_action_dict = report_dict["SubmissionStatus"]["Action"]
		# CHECK SUBMISSION ACTIONS ON THE REPORT
		try:
			for i in range(len(report_action_dict)):
				rp_spuid = re.sub(submission_id+"-", "", report_action_dict[i]["@action_id"])
				rp_spuid = re.sub(r"-sra", "", rp_spuid)
				rp_spuid = re.sub(r"-bs", "", rp_spuid)
				rp_target_db = report_action_dict[i]["@target_db"]
				# CHECK THE RESPONSE SECTION OF THE REPORT
				try:
					if (rp_target_db.upper() == "BIOSAMPLE") and (rp_spuid in status_submission_df["report_sample_id"].values.tolist()):
						df_partial = status_submission_df.loc[status_submission_df["report_sample_id"] == rp_spuid]
						status_submission_df.loc[df_partial.index.values, 'biosample_status'] = report_action_dict[i]["@status"]
						try:
							status_submission_df.loc[df_partial.index.values, 'biosample_message'] = report_action_dict[i]["Response"][0]["Message"]["#text"]
						except:
							pass
						if report_action_dict[i]["@status"] == "processed-ok":
							status_submission_df.loc[df_partial.index.values, 'biosample_accession'] = report_action_dict[i]["Response"][0]["Object"]["@accession"]
							status_submission_df.loc[df_partial.index.values , 'bioproject'] = report_action_dict[i]["Response"][0]["Object"]["Meta"]["BioProject"]["#text"]
					elif (rp_target_db.upper() == "SRA") and (rp_spuid in status_submission_df["report_sample_id"].values.tolist()):
						df_partial = status_submission_df.loc[status_submission_df["report_sample_id"] == rp_spuid]
						status_submission_df.loc[df_partial.index.values, 'sra_status'] = report_action_dict[i]["@status"]
						try:
							status_submission_df.loc[df_partial.index.values, 'sra_message'] = report_action_dict[i]["Response"][0]["Message"]["#text"]
						except:
							pass
						if report_action_dict[i]["@status"] == "processed-ok":
							status_submission_df.loc[df_partial.index.values , 'sra_accession'] = report_action_dict[i]["Response"][0]["Object"]["@accession"]
							status_submission_df.loc[df_partial.index.values , 'bioproject'] = report_action_dict[i]["Response"][0]["Object"]["Meta"]["BioProject"]["#text"]
				# CHECK THE RESPONSE SECTION OF THE REPORT
				except:
					try:
						if (rp_target_db.upper() == "BIOSAMPLE") and (rp_spuid in status_submission_df["report_sample_id"].values.tolist()):
							df_partial = status_submission_df.loc[status_submission_df["report_sample_id"] == rp_spuid]
							status_submission_df.loc[df_partial.index.values, 'biosample_status'] = report_action_dict[i]["@status"]
							status_submission_df.loc[df_partial.index.values , 'bioproject'] = report_action_dict[i]["Response"]["Object"]["Meta"]["BioProject"]["#text"]
							try:
								status_submission_df.loc[df_partial.index.values, 'biosample_message'] = report_action_dict[i]["Response"]["Message"]["#text"]
							except:
								pass
							if report_action_dict[i]["@status"] == "processed-ok":
								status_submission_df.loc[df_partial.index.values, 'biosample_accession'] = report_action_dict[i]["Response"]["Object"]["@accession"]
						elif (rp_target_db.upper() == "SRA") and (rp_spuid in status_submission_df["report_sample_id"].values.tolist()):
							df_partial = status_submission_df.loc[status_submission_df["report_sample_id"] == rp_spuid]
							status_submission_df.loc[df_partial.index.values, 'sra_status'] = report_action_dict[i]["@status"]
							try:
								status_submission_df.loc[df_partial.index.values, 'sra_message'] = report_action_dict[i]["Response"]["Message"]["#text"]
							except:
								pass
							if report_action_dict[i]["@status"] == "processed-ok":
								status_submission_df.loc[df_partial.index.values , 'sra_accession'] = report_action_dict[i]["Response"]["Object"]["@accession"]
								status_submission_df.loc[df_partial.index.values , 'bioproject'] = report_action_dict[i]["Response"]["Object"]["Meta"]["BioProject"]["#text"]
					except:
						pass
		except:
			pass
	except:
		pass
	# Save a copy of submission status df without report_sample_id
	status_submission_df = status_submission_df.loc[:, status_submission_df.columns != 'report_sample_id']
	status_submission_df.to_csv(submission_status_file, header = True, index = False)
	return submission_status, submission_id

def process_genbank_report(report_file, submission_status_file, submission_files_dir):
	API_URL = submission_process.get_main_config()["PORTAL_NAMES"]["NCBI"]["API_URL"]
	# Read in report.xml
	tree = ET.parse(report_file)
	root = tree.getroot()
	xmlstr = ET.tostring(root, encoding='utf8', method='xml')
	# Read in submission status csv
	status_submission_df = pd.read_csv(submission_status_file, header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False)
	status_submission_df = status_submission_df.fillna("")
	status_submission_df.columns = status_submission_df.columns.str.strip()
	# Convert xml to dictionary
	report_dict = xmltodict.parse(xmlstr)
	# Get submission status
	try:
		# Get submission status and id from report.xml
		submission_status = report_dict["SubmissionStatus"]["@status"]
	except:
		submission_status = "submitted"
	# Get submission id
	try:
		submission_id = report_dict["SubmissionStatus"]["@submission_id"]
	except:
		submission_id = "pending"
	# CHECK SUBMISSION STATUS ON THE REPORT
	try:
		if report_dict["SubmissionStatus"]["Action"]["@status"] == "processed-ok":
			try:
				for item in report_dict["SubmissionStatus"]["Action"]["Response"]:
					if "File" in item:
						filename_dict = item["File"]
						break
				for file in filename_dict:
					file_name = file["@file_path"]
					file_path = file["@file_id"]
					r = requests.get(API_URL.replace("FILE_ID", file_path), allow_redirects=True)
					open(os.path.join(submission_files_dir, file_name), 'wb').write(r.content)
					# Waiting for the file to write
					while not os.path.exists(os.path.join(submission_files_dir, file_name)):
						time.sleep(10)
					if file_name == "AccessionReport.tsv":
						accession_report_df = pd.read_csv(os.path.join(submission_files_dir, file_name), header = 0, sep = "\t", dtype = str, engine = "python", encoding="utf-8", index_col=False)
						for index, row in accession_report_df.iterrows():
							status_submission_df.loc[status_submission_df["ncbi-sequence_name"] == row["Sequence ID"].strip(), "genbank-status"] = "processed-ok"
							status_submission_df.loc[status_submission_df["ncbi-sequence_name"] == row["Sequence ID"].strip(), "genbank-accession"] = row["#Accession"]
							status_submission_df.loc[status_submission_df["ncbi-sequence_name"] == row["Sequence ID"].strip(), "genbank-message"] = row["Release Date"]
						status_submission_df.to_csv(submission_status_file, header = True, index = False)
			except:
				pass
	except:
		pass
	return submission_status, submission_id

# Check if it has BioSample and BioProject accession number (update status report)
def update_genbank_files(database, organism, submission_files_dir, submission_status_file):
	# Read in the submission status report
	status_df = pd.read_csv(submission_status_file, header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False)
	# Read in genbank source file
	if os.path.isfile(os.path.join(submission_files_dir, "source.src")):
		source_df = pd.read_csv(os.path.join(submission_files_dir, "source.src"), header = 0, sep="\t", dtype = str, engine = "python", encoding="utf-8", index_col=False)
	else:
		print("Error: submission source file does not exist at "+os.path.join(submission_files_dir, "source.src"), file=sys.stderr)
		sys.exit(1)
	# Read in genbank comment file
	if os.path.isfile(os.path.join(submission_files_dir, "comment.cmt")):
		cmt_df = pd.read_csv(os.path.join(submission_files_dir, "comment.cmt"), header = 0, dtype = str, engine = "python", sep="\t", encoding = "utf-8", index_col = False)
	# Retrieve accession info
	src_accessions = dict()
	cmt_accessions = dict()
	# Pull accessions only if field has valid info
	if ("BIOSAMPLE" in database) and ("biosample_accession" in status_df) and (status_df["biosample_accession"].isna().all() == False):
		src_accessions["biosample_accession"] = "BioSample"
	if ("SRA" in database) and ("sra_accession" in status_df) and (status_df["sra_accession"].isna().all() == False):
		src_accessions["sra_accession"] = "SRA"
	if ("GISAID" in database) and ("gisaid_accession_epi_isl_id" in status_df) and (status_df["gisaid_accession_epi_isl_id"].isna().all() == False):
		cmt_accessions["gisaid_accession_epi_isl_id"] = "EPI_ISOLATE_ID"
	if ("GISAID" in database) and ("gisaid_accession_epi_id" in status_df) and (status_df["gisaid_accession_epi_id"].isna().all() == False):
		cmt_accessions["gisaid_accession_epi_id"] = "EPI_SEQUENCE_ID"
	# Update source_df
	if len(src_accessions) > 0:
		# If accession columns exist drop to overwrite
		source_df = source_df.drop(columns=src_accessions.values(), errors="ignore")
		src_accessions["ncbi-sequence_name"] = "Sequence_ID"
		# Merge and rewrite source file
		src_accessions_df = status_df[src_accessions.keys()].copy()
		src_accessions_df = src_accessions_df.rename(columns=src_accessions)
		source_df = pd.merge(source_df, src_accessions_df, how="left", on="Sequence_ID")
		source_df.to_csv(os.path.join(submission_files_dir, "source.src"), index=False, sep="\t")
	# Update CMT file
	if len(cmt_accessions) > 0:
		if os.path.isfile(os.path.join(submission_files_dir, "comment.cmt")):
			cmt_df = pd.read_csv(os.path.join(submission_files_dir, "comment.cmt"), header = 0, dtype = str, engine = "python", sep="\t", encoding = "utf-8", index_col = False)
			# If accession columns exist drop to overwrite
			cmt_df = cmt_df.drop(columns=cmt_accessions.values(), errors="ignore")
			cmt_accessions["ncbi-sequence_name"] = "SeqID"
			# merge fields
			cmt_accessions_df = status_df[cmt_accessions.keys()].copy()
			cmt_accessions_df = cmt_accessions_df.rename(columns=cmt_accessions)
			cmt_df = pd.merge(cmt_df, cmt_accessions_df, how="left", on="SeqID")
		else:
			# If cmt field doesn't exist and must to write accessions then create it
			cmt_df = status_df[cmt_accessions.keys()].copy()
			cmt_df = cmt_df.rename(columns=cmt_accessions)
			if "FLU" in organism:
				cmt_df["StructuredCommentPrefix"] = "FluData"
				cmt_df["StructuredCommentSuffix"] = "FluData"
			elif "COV" in organism:
				cmt_df["StructuredCommentPrefix"] = "Assembly-Data"
				cmt_df["StructuredCommentSuffix"] = "Assembly-Data"
		# Correct order of cmt file columns
		cmt_start = ["SeqID", "StructuredCommentPrefix"]
		cmt_end = ["StructuredCommentSuffix"]
		if "EPI_ISOLATE_ID" in cmt_df:
			cmt_start.append("EPI_ISOLATE_ID")
		if "EPI_SEQUENCE_ID" in cmt_df:
			cmt_end.insert(0, "EPI_SEQUENCE_ID")
		columns_no_prefix_suffix = list(filter(lambda x: (x not in ["SeqID", "StructuredCommentPrefix", "StructuredCommentSuffix", "EPI_ISOLATE_ID", "EPI_SEQUENCE_ID"])==True, cmt_df.columns))
		ordered_columns = cmt_start + columns_no_prefix_suffix + cmt_end
		cmt_df = cmt_df.reindex(columns=ordered_columns)
		cmt_df.to_csv(os.path.join(submission_files_dir, "comment.cmt"), index=False, sep="\t")
		
def update_gisaid_files(organism, submission_files_dir, submission_status_file):
	# Read in the submission status report
	status_df = pd.read_csv(submission_status_file, header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False)
	# Gather all required files
	metadata = os.path.join(submission_files_dir, "metadata.csv")
	orig_metadata = os.path.join(submission_files_dir, "orig_metadata.csv")
	fasta = os.path.join(submission_files_dir, "sequence.fsa")
	orig_fasta = os.path.join(submission_files_dir, "orig_sequence.fsa")
	# Filter out genbank that has accession number
	genbank_status_df = status_df[status_df["genbank-status"].str.contains("processed-ok", na=False)].copy()
	gisaid_status_df = genbank_status_df[["gs-sample_name", "gs-sequence_name"]]
	# Add required gisaid fields
	metadata_df = pd.read_csv(metadata, header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False)
	if "FLU" in organism:
		column_name = "Isolate_Name"
	elif "COV" in organism:
		column_name = "virus_name"
	metadata_df = metadata_df.merge(gisaid_status_df, how="inner", left_on=column_name, right_on="gs-sample_name")
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
