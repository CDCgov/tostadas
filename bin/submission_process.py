# Python Libraries
import pathlib
import pandas as pd
import sys
import os
import re
import yaml
from Bio import SeqIO

# Local imports
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import submission_create
import submission_report
import submission_submit

# Get program directory
PROG_DIR = os.path.dirname(os.path.abspath(__file__))

# Get main config file
def get_main_config():
	main_config_path = os.path.join(PROG_DIR, "config", "main_config.yaml")
	if os.path.isfile(main_config_path) == True:
		with open(main_config_path, "r") as f:
			main_config = yaml.load(f, Loader=yaml.BaseLoader) # Load yaml as str only
		if type(main_config) is dict:
			try:
				main_config = main_config["SUBMISSION_PORTAL"]
				return main_config
			except:
				print("Error: there is no SUBMISSION_PORTAL information in config file.", file=sys.stderr)
				sys.exit(1)
		else:
			print("Error: Config file is incorrect. File must has a valid yaml format.", file=sys.stderr)
			sys.exit(1)
	else:
		print("Error: Main config file does not exist at " + main_config_path, file=sys.stderr)
		sys.exit(1)

# Extract required column fields from main config file
def get_required_colnames(database, organism):
	# Get main fig file
	main_config = get_main_config()
	# Get all common fields across all portals
	if "COMMON_FIELDS" in list(main_config.keys()):
		all_required_colnames = list(main_config["COMMON_FIELDS"].keys())
	else:
		all_required_colnames = []
	# Get a list of submission portals from main config file
	for portal in list(main_config["PORTAL_NAMES"].keys()):
		database_list = [name for name in database if (name in list(main_config["PORTAL_NAMES"][portal]["DATABASE"].keys()) or (name in portal))]
		if len(database_list) > 0:
			# Get all common fields across all databases in a portal
			if "COMMON_FIELDS" in list(main_config["PORTAL_NAMES"][portal].keys()):
				all_required_colnames += list(main_config["PORTAL_NAMES"][portal]["COMMON_FIELDS"].keys())	
			# Get required fields for given organism
			if organism in list(main_config["PORTAL_NAMES"][portal]["DATABASE"].keys()):
				all_required_colnames += list(main_config["PORTAL_NAMES"][portal]["DATABASE"][organism].keys())
			# Get required fields for each given database
			for database_name in database_list:
				if database_name in list(main_config["PORTAL_NAMES"][portal]["DATABASE"].keys()):
					all_required_colnames += list(main_config["PORTAL_NAMES"][portal]["DATABASE"][database_name].keys())
	# Extract the unique metadata fields
	return set(all_required_colnames)		

# Check the config file
def get_config(config_file, database):
	# Determine which portal is the database belongs to
	submission_portals = ["NCBI" if x in ["BIOSAMPLE", "SRA", "GENBANK"] else "GISAID" for x in database]
	# Read in config file
	with open(config_file, "r") as f:
		config_dict = yaml.load(f, Loader=yaml.BaseLoader) # Load yaml as str only
	if type(config_dict) is dict:
		try:
			config_dict = config_dict['Submission']
		except:
			print("Error: there is no Submission information in the config file.", file=sys.stderr)
			sys.exit(1)
		else:
			# Check if each database has portal information listed in the config file
			for d in range(len(database)):
				if submission_portals[d] not in config_dict.keys():
					print("\n"+"Error: " +  database[d] + " is listed as one of the submitting databases in the command.", file=sys.stderr)
					print("Error: However, there is no " + submission_portals[d] + " submission information provided in the config file.", file=sys.stderr)
					print("Error: Either remove " + database[d] + " from the submitting databases or update your config file."+"\n", file=sys.stderr)
					sys.exit(1)
	else:	
		print("Error: Config file is incorrect. File must has a valid yaml format.", file=sys.stderr)
		sys.exit(1)

# Read in metadata file
def get_metadata(database, organism, metadata_file):
	# Read in metadata file
	metadata = pd.read_csv(metadata_file, header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False, na_filter=False)
	# Remove rows if entirely empty
	metadata = metadata.dropna(how="all")
	# Remove extra spaces from column names
	metadata.columns = metadata.columns.str.strip()
	# Extract the required fields for specified database
	db_required_colnames = get_required_colnames(database=database, organism=organism)
	# Obtain the column fields with "*". Those fields must contain the sample names
	required_sample_colnames = list(filter(lambda x: ("*" in x)==True, db_required_colnames))
	# Obtain the column fields with "?". If a value is missing in those fields, use the term "unknown"
	required_unknown_colnames = list(filter(lambda x: ("?" in x)==True, db_required_colnames))
	# Obtain the column fields with & sign. Those fields contain date values.
	required_date_colnames = list(filter(lambda x: ("&" in x)==True, db_required_colnames))
	# Obtain the real required column names without the asterisks and & signs
	required_colnames = [re.sub("[*?#&]", "", x) for x in db_required_colnames]
	# Check if required column names are existed in metadata file
	if not set(required_colnames).issubset(set(metadata.columns)):
		failed_required_colnames = list(filter(lambda x: (x in metadata.columns)==False, required_colnames))
		print("Error: Metadata file must have the following required column names: " + ", ".join(failed_required_colnames), file=sys.stderr)
		sys.exit(1)
	# Run some checks to make sure the required column fields are populated correctly
	for name in required_colnames:
		# Make sure specific fields have a correct date format
		if name in [re.sub("[*?#&]", "", x) for x in required_date_colnames]:
			metadata[name] = pd.to_datetime(metadata[name], errors="coerce")
			if pd.isna(metadata[name]).any():
				print("Error: The required 'collection_date' field in metadata file contains incorrect date format. Date must be in the ISO format: YYYYMMDD/YYYYDDMM/DDMMYYYY/MMDDYYYY. For example: 2020-03-25.", file=sys.stderr)
				sys.exit(1)
			metadata[name] = metadata[name].dt.strftime("%Y-%m-%d")
		# Make sure specific column fields with empty values are filled with "Unknown"
		if (name in [re.sub("[*?#&]", "", x) for x in required_unknown_colnames]) and any(metadata[name] == ""):
			metadata[name] = metadata[name].replace(r'^\s*$', "Unknown", regex=True)
		# Extract fields that contain sample names and append to overall list
		if name in [re.sub("[*?#&]", "", x) for x in required_sample_colnames]:
			# Make sure that samples are not duplicated
			if metadata.duplicated(subset=[name]).any():
				print("Error: The required '" + name + "' field in metadata file must have sample names that are unique.", file=sys.stderr)
				sys.exit(1)
	return metadata

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

# Check user credentials information
def check_credentials(config_dict, database):
	# Check username
	if "Username" not in config_dict.keys():
		print("Error: there is no Submission > " + database + " > Username information in config file.", file=sys.stderr)
		sys.exit(1)
	elif ("Username" in config_dict.keys()) and ((config_dict["Username"] is not None) and (config_dict["Username"] != "")):
		pass
	else:
		print("Error: Submission > " + database + " > Username in the config file cannot be empty.", file=sys.stderr)
		sys.exit(1)
	# Check password
	if "Password" not in config_dict.keys():
		print("Error: there is no Submission > " + database + " > Password information in config file.", file=sys.stderr)
		sys.exit(1)
	elif ("Password" in config_dict.keys()) and ((config_dict["Password"] is not None) and (config_dict["Password"] != "")):
		pass
	else:
		print("Error: Submission > " + database + " > Password in the config file cannot be empty.", file=sys.stderr)
		sys.exit(1)
	# Check client-id if database is GISAID
	if database != "GISAID":
		return
	elif "Client-Id" not in config_dict.keys():
		print("Error: there is no Submission > " + database + " > Client-Id information in config file.", file=sys.stderr)
		sys.exit(1)
	elif ("Client-Id" in config_dict.keys() and ((config_dict["Client-Id"] is not None) and (config_dict["Client-Id"] != ""))):
		pass
	else:
		print("Error: Submission > " + database + " > Client-Id in the config file cannot be empty.", file=sys.stderr)
		sys.exit(1)

# Check raw reads files listed in metadata file
def check_raw_read_files(submission_name, submission_dir, metadata):
	# Check raw reads files if SRA is provided
	raw_reads_path = os.path.join(submission_dir, submission_name, "raw_reads")
	# If database is SRA, check if the raw reads path exists
	if os.path.exists(raw_reads_path) == False:
		print("Checking SRA - Sequence Read Archives", file=sys.stderr)
		print("Cannot find the 'raw_reads' subfolder at "+ raw_reads_path, file=sys.stderr)
		print("Please create the subfolder and place all raw reads files in that directory", file=sys.stderr)
		sys.exit(1)
	# Check if raw reads files are stored locally or on cloud
	if metadata["sra-file_location"].str.contains("local|cloud").all() == False:
		print("Error: the value of sra-file_location in metadata file can only be 'local' or 'cloud'.", file=sys.stderr)
		sys.exit(1)
	# Separate samples stored in local and cloud
	local_df = metadata[metadata["sra-file_location"] == "local"]
	validated_files = set()
	for index, row in local_df.iterrows():
		# If multiple files check each one
		for file in row["sra-file_name"].split(","):
			file = file.strip()
			file_path = ""
			if os.path.isabs(file):
				file_path = file
			else:
				file_path = os.path.join(raw_reads_path, file)
			if os.path.isfile(file_path) == False:
				print("Error: Raw read files for " + row["ncbi-spuid"] + " does not exist at: " + file_path, file=sys.stderr)
				print("Error: Please check the path or the name of the file again.", file=sys.stderr)
				sys.exit(1)
			else:
				validated_files.add(file_path)
	return validated_files

# Check sample names in metadata file are listed in fasta file
def process_fasta_samples(metadata, fasta_file):
	fasta_dict = []
	# Convert fasta into df
	with open(fasta_file, "r") as fsa:
		records = SeqIO.parse(fsa, "fasta")
		for record in records:
			fasta_dict.append({"fasta_name_orig":record.id, "fasta_sequence_orig":record.seq, "fasta_description_orig":record.description})
	fasta_df = pd.DataFrame(fasta_dict)
	# Remove rows if they contain all Nan
	fasta_df = fasta_df.dropna(how='all')
	# Check duplicates in fasta_df
	duplicated_df = fasta_df[fasta_df.duplicated(subset = ["fasta_name_orig"], keep = False)]
	if not duplicated_df.empty:
		print("Error: Sequences in fasta file must be unique at: " + fasta_file + "\nDuplicate Sequences\n" + df["fasta_sequence_orig"].to_string(index=False), file=sys.stderr)
		sys.exit(1)
	# Validate duplicates don't appear on merge
	try:
		merged_df = metadata.merge(fasta_df, how = "outer", left_on = "sequence_name", right_on = "fasta_name_orig", validate = "1:1")
	except:
		print("Error: Unable to merge fasta file to metadata file. Please validate there are not duplicate sequences in both files.", file=sys.stderr)
		sys.exit(1)
	# Check if fasta file has sequences not in metadata
	if merged_df["sequence_name"].isnull().any():
		print("Error: Sequences in fasta file do not have an associated sequence in metadata file. Please update sequences below:\n" + merged_df[merged_df["sequence_name"].isnull()]["fasta_name_orig"].to_string(), file=sys.stderr)
		sys.exit(1)
	# Check if metadata has sequences not in fasta file
	if merged_df["fasta_name_orig"].isnull().any():
		print("Error: Sequences in metadata file do not have an associated sequence in fasta file. Please update sequences below:\n" + merged_df[merged_df["fasta_name_orig"].isnull()]["sequence_name"].to_string(), file=sys.stderr)
		sys.exit(1)
	return merged_df

# Update submission log
def update_submission_status(submission_dir, submission_name, organism, test):
	# Check if submission log exists
	submission_dir = os.path.abspath(submission_dir)
	submission_log_file = os.path.join(submission_dir, "submission_log.csv")
	if os.path.isfile(submission_log_file):
		df = pd.read_csv(submission_log_file, header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False)
	else:
		print("There is no submission log located at " + submission_log_file, file=sys.stderr)
		print("Error: Either a submission has not been made or submission_log.csv has been moved.", file=sys.stderr)
		sys.exit(1)
	# Get the submission type: test or production
	if test == True:
		submission_type = "Test"
	else:
		submission_type = "production"
	# Check if given organism exist in the log
	df_partial = df.loc[(df["Organism"] == organism) & (df["Submission_Name"] == submission_name) & (df["Submission_Directory"] == submission_dir) & (df["Submission_Type"] == submission_type)]
	if df_partial.shape[0] == 0:
		print("Error: Submission name: " + submission_name + " for "+organism+" "+submission_type+"-data is not found in the submission log file.", file=sys.stderr)
		print("Error: Either a submission has not been made or an entry has been moved.", file=sys.stderr)
		sys.exit(1)
	# Order get a list of submitting databases
	df_partial = df_partial.sort_values(by=["Submission_Position"])
	database = df_partial["Database"].tolist()
	# Output message
	print("\n"+"Checking submission status for:"+"\n", file=sys.stdout)
	print("Submission name: " + submission_name, file=sys.stdout)
	print("Submission organism: " + organism, file=sys.stdout)
	print("Submission type: " + submission_type, file=sys.stdout)
	# Check the status of each database in its order of submission
	for database_name in database:
		print("\n" + "Submission database: " + database_name, file=sys.stdout)
		df = pd.read_csv(submission_log_file, header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False).sort_values('Submission_Position', ascending=True)
		df_processing = df[(df["Organism"] == organism) & (df["Database"] == database_name) & (df["Submission_Directory"] == submission_dir) & (df["Submission_Name"] == submission_name) & (df["Submission_Type"] == submission_type)]		
		df_processing = df_processing.reset_index(drop=True)
		submission_dir = df_processing["Submission_Directory"][0]		
		submission_position = df_processing["Submission_Position"][0]	
		submission_id, submission_status = df_processing["Submission_Status"][0].strip().split(";")
		config_file = df_processing["Config_File"][0]
		table2asn = df_processing["Table2asn"][0]
		gff_file = df_processing["GFF_File"][0]
		# Check if submission files exist in parent directory
		submission_files_dir = os.path.join(submission_dir, submission_name, "submission_files", database_name)
		if os.path.exists(submission_files_dir) == False:
			print("Error: Submission files for "+submission_name+" does not exist at "+submission_files_dir, file=sys.stderr)
			sys.exit(1)
		# Check if submission report status csv exists
		submission_status_file = os.path.join(submission_dir, submission_name, "submission_report_status.csv")
		if os.path.isfile(submission_status_file) == False:
			print("Error: Submission status report for "+submission_name+" does not exist at "+submission_status_file, file=sys.stderr)
			sys.exit(1)
		# Check if config file exists
		if os.path.isfile(config_file) == False:
			print("Error: Config file for "+submission_name+" does not exist at "+config_file, file=sys.stderr)
			sys.exit(1)
		else:
			config_dict = get_config(config_file=config_file, database=database_name)
		# IF GISAID in a list of submitting databases, check if CLI is downloaded and store in the correct directory
		gisaid_cli = os.path.join(submission_dir, "gisaid_cli", organism.lower()+"CLI", organism.lower()+"CLI") if "GISAID" in database_name else None
		# Check if the gisaid_cli exists
		if (gisaid_cli is not None) and os.path.isfile(gisaid_cli) == False:
			print("There is no GISAID CLI package for " + organism + " located at "+ gisaid_cli, file=sys.stderr)
			print("Please download the CLI package from GISAID platform", file=sys.stderr)
			print("Then place a copy of the CLI binary at "+ gisaid_cli, file=sys.stderr)
			sys.exit(1)	
		# Check the status of the submission
		if "processed-ok" in submission_status:
			print("Submission status: " + submission_status, file=sys.stdout)
		else:		
			# Pull download submission report and update its status
			if database_name in ["BIOSAMPLE", "SRA", "GENBANK"]:
				# If report exists, processing the report and output status of the submission
				if database_name in ["BIOSAMPLE", "SRA"]:
					report_file = submission_report.get_ncbi_process_report(database=database_name, submission_name=submission_name, submission_files_dir=submission_files_dir, config_dict=config_dict['NCBI'], submission_type=submission_type)
					if report_file is not None and os.path.isfile(report_file):
						submission_status, submission_id = submission_report.process_biosample_sra_report(database=database, report_file=report_file, submission_status_file=submission_status_file)
				elif database_name == "GENBANK":
					# Update submission
					if "---" in submission_status:
						# Check if biosample, sra, and gisaid are in a list of submitting databases
						if int(submission_position) == 1:
							other_submitting_db = [x for x in database if x in ["BIOSAMPLE", "SRA"]]
						elif int(submission_position) == 2:
							other_submitting_db = [x for x in database if x in ["BIOSAMPLE", "SRA", "GISAID"]]
						# Update biosample, sra, gisaid accession on genbank submission
						if len(other_submitting_db) > 0:
							all_status = []
							for db in other_submitting_db:
								db_df = df.loc[df["Database"] == db]
								db_df = db_df.reset_index(drop=True)
								db_status = db_df["Submission_Status"][0]	
								# If the status of biosample or sra is processed-ok, then go ahead and submit to Genbank 	
								if "processed-ok" in db_status:
									all_status += [1]
									submission_report.update_genbank_files(database=database, organism=organism, submission_files_dir=submission_files_dir, submission_status_file=submission_status_file)
								else:
									all_status += [0]
							# Submit via Table2asn
							if all(all_status):
								if table2asn == True:
									if os.path.isfile(str(gff_file)) == False:
										gff_file = None
									submission_id, submission_status = submission_create.create_genbank_table2asn(submission_name=submission_name, submission_files_dir=submission_files_dir, gff_file=gff_file)
									if submission_status == "processed-ok":
										submission_status = submit.sendmail(database=database_name, submission_name=submission_name, submission_dir=submission_dir, config_dict=config_dict['NCBI'], test=test)
								else:
									# Submit via FTP
									submission_create.create_genbank_zip(submission_name=submission_name, submission_files_dir=submission_files_dir)
									submission_submit.submit_ncbi(database=database_name, submission_name=submission_name, submission_dir=submission_dir, config_dict=config_dict["NCBI"], submission_type=submission_type)
									submission_status = "submitted"
									submission_id = "pending"
					else:
						# If report exists, processing the report and output status of the submission
						report_file = submission_report.get_ncbi_process_report(database=database_name, submission_name=submission_name, submission_files_dir=submission_files_dir, config_dict=config_dict['NCBI'], submission_type=submission_type)
						if report_file is not None and os.path.isfile(report_file):
							submission_status, submission_id = submission_report.process_genbank_report(report_file=report_file, submission_status_file=submission_status_file, submission_files_dir=submission_files_dir)
			elif database_name == "GISAID":
				if ("---" in submission_status) and (int(submission_position) == 1):
					submission_status = submission_submit.submit_gisaid(organism=organism, database=database_name, submission_dir=submission_dir, submission_name=submission_name, config_dict=config_dict["GISAID"], gisaid_cli=gisaid_cli, submission_status_file=submission_status_file, submission_type=submission_type)
					submission_id = ""
				elif ("---" in submission_status) and ("GENBANK" in database) and (int(submission_position) == 2):
					db_status = df[(df["Database"] == "GENBANK"), "Submission_Status"][0]
					if "processed-ok" in db_status:
						submission_report.update_gisaid_files(organism=organism, submission_files_dir=submission_files_dir, submission_status_file=submission_status_file)
						submission_status = submission_submit.submit_gisaid(organism=organism, database=database_name, submission_dir=submission_dir, submission_name=submission_name, config_dict=config_dict["GISAID"], gisaid_cli=gisaid_cli, submission_status_file=submission_status_file, submission_type=submission_type)
						submission_id = ""	  
			# Update status in the submission log
			submission_create.create_submission_log(database=database_name, submission_position=submission_position, organism=organism, submission_name=submission_name, submission_dir=submission_dir, config_file=config_file, submission_status=submission_status, submission_id=submission_id, table2asn=table2asn, gff_file=gff_file, submission_type=submission_type)
			# Print out the submission status
			print("Submission status: " + submission_status, file=sys.stdout)

