
# Python Libraries
import pathlib
import pandas as pd
import os
import subprocess
import sys
from lxml import etree
import datetime
from datetime import datetime
import shutil
import time
from zipfile import ZipFile
from Bio import SeqIO
from Bio.SeqRecord import SeqRecord
from nameparser import HumanName

# Local imports
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import submission_process

def download_table2asn(table2asn_dir):
	# Determine which platform to download table2asn
	if platform.system() == "Windows":
		zip_url = "https://ftp.ncbi.nlm.nih.gov/asn1-converters/by_program/table2asn/win64.table2asn.zip"
		with urlopen(zip_url) as zip_response:
			with ZipFile(BytesIO(zip_response.read())) as zip_file:
				zip_file.extractall(table2asn_dir)
		return
	elif platform.system() == "Darwin":
		zip_url = "https://ftp.ncbi.nlm.nih.gov/asn1-converters/by_program/table2asn/mac.table2asn.gz"
	elif platform.system() == "Linux":
		zip_url = "https://ftp.ncbi.nlm.nih.gov/asn1-converters/by_program/table2asn/linux64.table2asn.gz"
	else:
		print("Error: Cannot identify correct system platform. Please download correct Table2asn version for system and place it in script directory.", file=sys.stderr)
		sys.exit(1)
	# Extract table2asn to tmp folder
	try:
		with open(table2asn_dir, "wb") as file:
			with urlopen(zip_url) as zip_response:
				file.write(gzip.decompress(zip_response.read()))
		st = os.stat(table2asn_dir)
		os.chmod(table2asn_dir, st.st_mode | stat.S_IXOTH | stat.S_IRWXU)
	except Exception as error:
		print("Downloading table2asn error", file=sys.stderr)
		print(error, file=sys.stderr)
		sys.exit(1)

# Create directory and files for NCBI database submissions
def create_ncbi_submission(organism, database, submission_name, submission_dir, config_dict, metadata, fasta_file=None, table2asn=False, gff_file=None):
	# Create a database subfolder within the submission directory to dump all submission files
	submission_files_dir = os.path.join(submission_dir, submission_name, "submission_files", database)
	# Create submission files directory
	os.makedirs(submission_files_dir, exist_ok=True)
	# Output message
	print("\n" + "Creating submission files for "+database, file=sys.stdout)
	# Create submission status csv
	if "BIOSAMPLE" in database:
		sequence_names = metadata["ncbi-spuid"].drop_duplicates()
	elif "SRA" in database:
		sequence_names = metadata["ncbi-spuid"].drop_duplicates()
		# Validate and write raw reads location
		raw_files_list = submission_process.check_raw_read_files(submission_name=submission_name, submission_dir=submission_dir, metadata=metadata)
		with open(os.path.join(submission_files_dir, "raw_reads_location.txt"), "w+") as file:
			for line in raw_files_list:
				file.write(line + "\n")
	elif "GENBANK" in database:
		sequence_names = metadata["gb-seq_id"]
		# Create genbank specific files
		create_genbank_files(organism=organism, submission_name=submission_name, submission_files_dir=submission_files_dir, config_dict=config_dict, metadata=metadata, fasta_file=fasta_file)
		# If using Table2asn do not generate extra genbank files
		if table2asn == True:
			create_genbank_table2asn(submission_name=submission_name, submission_files_dir=submission_files_dir, gff_file=gff_file)
			return			
		else:
			# If FTP upload for Genbank, create ZIP file for upload if table2asn is set to False
			create_genbank_zip(submission_name=submission_name, submission_files_dir=submission_files_dir)
	# Generate NCBI database submission xml
	xml_str = create_submission_xml(organism=organism, database=database, submission_name=submission_name, metadata=metadata, config_dict=config_dict, failed_seqs_auto_removed=True)
	save_xml(submission_xml=xml_str, submission_files_dir=submission_files_dir)
	# Save submission xml
	print("Files are stored at: " + os.path.join(submission_files_dir), file=sys.stdout)

# Create directory and files for GISAID submission
def create_gisaid_submission(organism, database, submission_name, submission_dir, config_dict, metadata, fasta_file):
	# Create a database subfolder within the submission directory to dump all submission files
	submission_files_dir = os.path.join(submission_dir, submission_name, "submission_files", database)
	# Create submission files directory
	os.makedirs(submission_files_dir, exist_ok=True)
	# Get column names for gisaid submission only
	gisaid_df = metadata.filter(regex="^gs-|^collection_date$|^authors").copy()
	gisaid_df.columns = gisaid_df.columns.str.replace("gs-","").str.strip()
	#Add required gisaid fields
	if "COV" in organism :
		gisaid_df["submitter"] = config_dict["Username"]
		gisaid_df["fn"] = ""
		first_cols = ["submitter", "fn", "virus_name"]
	elif "FLU" in organism:
		gisaid_df["Isolate_Id"] = ""
		gisaid_df["Segment_Ids"] = ""
		# Rename column names
		gisaid_df = gisaid_df.rename(columns = {"authors": "Authors"})
		gisaid_df = gisaid_df.rename(columns = {"collection_date": "Collection_Date"})
		gisaid_df['Collection_Month'] = pd.to_datetime(gisaid_df['Collection_Date']).dt.month
		gisaid_df['Collection_Year'] = pd.to_datetime(gisaid_df['Collection_Date']).dt.year
		# Pivot FLU segment names from long form to wide form
		gisaid_df["segment"] = "Seq_Id (" + gisaid_df["segment"].astype(str) + ")"
		group_df = gisaid_df.pivot(index="Isolate_Name", columns="segment", values="seq_id").reset_index()
		gisaid_df = gisaid_df.drop(columns=["seq_id","segment"])
		gisaid_df = gisaid_df.drop_duplicates(keep="first")
		gisaid_df = gisaid_df.merge(group_df, on="Isolate_Name", how="inner", validate="1:1")
		first_cols = ["Isolate_Id","Segment_Ids","Isolate_Name"]
	# Restructure column order
	last_cols = [col for col in gisaid_df.columns if col not in first_cols]
	gisaid_df = gisaid_df[first_cols + last_cols]
	# Create submission files
	gisaid_df.to_csv(os.path.join(submission_files_dir, "metadata.csv"), index=False, sep=",")
	shutil.copy(os.path.join(submission_files_dir, "metadata.csv"), os.path.join(submission_files_dir, "orig_metadata.csv"))
	create_fasta(organism=organism, database="GISAID", metadata=metadata, submission_files_dir=submission_files_dir, fasta_file=fasta_file)
	shutil.copy(os.path.join(submission_files_dir, "sequence.fsa"), os.path.join(submission_files_dir, "orig_sequence.fsa"))
	print("\n"+"Creating submission files for " + database, file=sys.stdout)
	print("Files are stored at: " + os.path.join(submission_files_dir), file=sys.stdout)
	
def create_submission_xml(organism, database, submission_name, config_dict, metadata, failed_seqs_auto_removed=True):
	# Submission XML header
	root = etree.Element("Submission")
	description = etree.SubElement(root, "Description")
	title = etree.SubElement(description, "Title")
	title.text = config_dict["Description"]["Title"]
	comment = etree.SubElement(description, "Comment")
	comment.text = config_dict["Description"]["Comment"]
	# Description info including organization and contact info
	organization = etree.SubElement(description, "Organization", type=config_dict["Description"]["Organization"]["@type"], role=config_dict["Description"]["Organization"]["@role"])
	if config_dict["Description"]["Organization"]["@org_id"]:
		organization.set("org_id", config_dict["Description"]["Organization"]["@org_id"])
	org_name = etree.SubElement(organization, "Name")
	org_name.text = config_dict["Description"]["Organization"]["Name"]
	if "GENBANK" not in database:
		contact = etree.SubElement(organization, "Contact", email=config_dict["Description"]["Organization"]["Submitter"]["@email"])
		name = etree.SubElement(contact, "Name")
		first_name = etree.SubElement(name, "First")
		first_name.text = config_dict["Description"]["Organization"]["Submitter"]["Name"]["First"]
		last_name = etree.SubElement(name, "Last")
		last_name.text = config_dict["Description"]["Organization"]["Submitter"]["Name"]["Last"]
	# XML actions
	if  "GENBANK" in database:
		action = etree.SubElement(root, "Action")
		addfiles = etree.SubElement(action, "AddFiles", target_db="GenBank")
		file = etree.SubElement(addfiles, "File", file_path=submission_name + ".zip")
		datatype = etree.SubElement(file, "DataType")
		datatype.text = "genbank-submission-package"
		wizard = etree.SubElement(addfiles, "Attribute", name="wizard")
		if "FLU" in organism:
			wizard.text = "BankIt_influenza_api"
		elif "COV" in organism:
			wizard.text = "BankIt_SARSCoV2_api"
		if failed_seqs_auto_removed == True:
			auto_remove = etree.SubElement(addfiles, "Attribute", name="auto_remove_failed_seqs")
			auto_remove.text = "yes"
		identifier = etree.SubElement(addfiles, "Identifier")
		spuid = etree.SubElement(identifier, "SPUID")
		spuid.text = submission_name
		if "FLU" in organism:
			spuid.set("spuid_namespace", "ncbi-influenza-genbank")
		elif "COV" in organism:
			spuid.set("spuid_namespace", "ncbi-sarscov2-genbank")
	if "BIOSAMPLE" in database:
		database_df = metadata.filter(regex="^ncbi-|^bs-|^organism$|^collection_date$").copy()
		database_df = database_df.drop_duplicates()
		for index, row in database_df.iterrows():
			action = etree.SubElement(root, "Action")
			add_data = etree.SubElement(action, "AddData", target_db="BioSample")
			data = etree.SubElement(add_data, "Data", content_type="xml")
			xmlcontent = etree.SubElement(data, "XmlContent")
			biosample = etree.SubElement(xmlcontent, "BioSample", schema_version="2.0")
			sampleid = etree.SubElement(biosample, "SampleId")
			spuid = etree.SubElement(sampleid, "SPUID", spuid_namespace=row["ncbi-spuid_namespace"])
			spuid.text = row["ncbi-spuid"]
			descriptor = etree.SubElement(biosample, "Descriptor")
			title = etree.SubElement(descriptor, "Title")
			title.text = row["bs-description"]
			organism = etree.SubElement(biosample, "Organism")
			organismname = etree.SubElement(organism, "OrganismName")
			organismname.text = row["organism"]
			if pd.notnull(row["ncbi-bioproject"]) and row["ncbi-bioproject"].strip() != "":
				bioproject = etree.SubElement(biosample, "BioProject")
				primaryid = etree.SubElement(bioproject, "PrimaryId", db="BioProject")
				primaryid.text = row["ncbi-bioproject"]
			package = etree.SubElement(biosample, "Package")
			package.text = row["bs-package"]
			# Attributes
			attributes = etree.SubElement(biosample, "Attributes")
			# Remove columns with bs-prefix that are not attributes
			biosample_cols = [col for col in database_df if (col.startswith('bs-')) and (col not in ["bs-package","bs-description"])]
			for col in biosample_cols:
				attribute = etree.SubElement(attributes, "Attribute", attribute_name=col.replace("bs-",""))
				attribute.text = row[col]
			# Add collection date to Attributes
			attribute = etree.SubElement(attributes, "Attribute", attribute_name="collection_date")
			attribute.text = row["collection_date"]
			identifier = etree.SubElement(add_data, "Identifier")
			spuid = etree.SubElement(identifier, "SPUID", spuid_namespace=row["ncbi-spuid_namespace"] + "_bs")
			spuid.text = row["ncbi-spuid"]
	if "SRA" in database:
		database_df = metadata.filter(regex="^ncbi-|^sra-|^organism$|^collection_date$").copy()
		database_df = database_df.drop_duplicates()
		for index, row in database_df.iterrows():
			action = etree.SubElement(root, "Action")
			addfiles = etree.SubElement(action, "AddFiles", target_db="SRA")
			for sra_file in row["sra-file_name"].split(","):
				if row["sra-file_location"].strip().lower() == "cloud":
					file = etree.SubElement(addfiles, "File", cloud_url = sra_file.strip())
				elif row["sra-file_location"].strip().lower() == "local":
					file = etree.SubElement(addfiles, "File", file_path = os.path.basename(sra_file.strip()))
				else:
					print("Error: Metadata field file_location must be either cloud or local. Field currently contains: " + row["sra-file_location"].strip().lower(), file=sys.stderr)
					sys.exit(1)
				datatype = etree.SubElement(file, "DataType")
				datatype.text = "generic-data"
			# Remove columns with sra- prefix that are not attributes
			sra_cols = [col for col in database_df if (col.startswith('sra-')) and (col not in ["sra-file_location","sra-file_name"])]
			for col in sra_cols:
				attribute = etree.SubElement(addfiles, "Attribute", name=col.replace("sra-",""))
				attribute.text = row[col]
			if pd.notnull(row["ncbi-bioproject"]) and row["ncbi-bioproject"].strip() != "":
				attribute_ref_id = etree.SubElement(addfiles, "AttributeRefId", name="BioProject")
				refid = etree.SubElement(attribute_ref_id, "RefId")
				primaryid = etree.SubElement(refid, "PrimaryId")
				primaryid.text = row["ncbi-bioproject"]
			if metadata.columns.str.contains("bs-").any():
				attribute_ref_id = etree.SubElement(addfiles, "AttributeRefId", name="BioSample")
				refid = etree.SubElement(attribute_ref_id, "RefId")
				spuid = etree.SubElement(refid, "SPUID", spuid_namespace=row["ncbi-spuid_namespace"] + "_bs")
				spuid.text = row["ncbi-spuid"]
			identifier = etree.SubElement(addfiles, "Identifier")
			spuid = etree.SubElement(identifier, "SPUID", spuid_namespace=row["ncbi-spuid_namespace"] + "_sra")
			spuid.text = row["ncbi-spuid"]
	# Pretty print xml
	xml_str = etree.tostring(root, encoding="utf-8", pretty_print=True, xml_declaration=True)
	return xml_str

# Save submission xml
def save_xml(submission_xml, submission_files_dir):
	# Save string as submission.xml
	with open(os.path.join(submission_files_dir, "submission.xml"), "wb") as f:
		f.write(submission_xml)
	# Waiting for the xml file to write
	while not os.path.exists(os.path.join(submission_files_dir, "submission.xml")):
		time.sleep(10)

# create the submission df for biosample
def create_submission_status_csv(database, sequence_names, submission_status_file):
	status_submission_df = sequence_names
	if "BIOSAMPLE" in database:
		status_submission_df["biosample_status"] = ""
		status_submission_df["biosample_accession"] = ""
		status_submission_df["biosample_message"] = ""
	if "SRA" in database:
		status_submission_df["sra_status"] = ""
		status_submission_df["sra_accession"] = ""
		status_submission_df["sra_message"] = ""
	if "GENBANK" in database:
		status_submission_df["genbank_status"] = ""
		status_submission_df["genbank_accession"] = ""
		status_submission_df["genbank_message"] = ""
	if "GISAID" in database:
		status_submission_df["gisaid_accession_epi_isl_id"] = ""
		status_submission_df["gisaid_accession_epi_id"] = ""
		status_submission_df["gisaid_message"] = ""
	# Save df
	status_submission_df.to_csv(submission_status_file, header = True, index = False)

# Create a authorset file
def create_authorset(config_dict, metadata, submission_name, submission_files_dir):
	submitter_first = config_dict["Description"]["Organization"]["Submitter"]["Name"]["First"]
	submitter_last = config_dict["Description"]["Organization"]["Submitter"]["Name"]["Last"]
	submitter_email = config_dict["Description"]["Organization"]["Submitter"]["@email"]
	alt_submitter_email = config_dict["Description"]["Organization"]["Submitter"]["@alt_email"]
	affil = config_dict["Description"]["Organization"]["Address"]["Affil"]
	div = config_dict["Description"]["Organization"]["Address"]["Div"]
	publication_status = metadata["gb-publication_status"].unique()[0]
	publication_title = metadata["gb-publication_title"].unique()[0]
	street = config_dict["Description"]["Organization"]["Address"]["Street"]
	city = config_dict["Description"]["Organization"]["Address"]["City"]
	sub = config_dict["Description"]["Organization"]["Address"]["Sub"]
	country = config_dict["Description"]["Organization"]["Address"]["Country"]
	email = config_dict["Description"]["Organization"]["Address"]["Email"]
	phone = config_dict["Description"]["Organization"]["Address"]["Phone"]
	zip_code = config_dict["Description"]["Organization"]["Address"]["Postal_code"]
	# Create authorset file
	with open(os.path.join(submission_files_dir, "authorset.sbt"), "w+") as f:
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
		authors = [HumanName(x.strip()) for x in metadata["authors"].unique()[0].split(";") if x.strip() != ""]
		total_names = len(authors)
		for index, name in enumerate(authors, start = 1):
			f.write("        {\n")
			f.write("          name name {\n")
			f.write("            last \"" + name.last + "\",\n")
			f.write("            first \"" + name.first + "\"")
			if name.middle != "":
				f.write(",\n            middle \"" + name.middle + "\"")
			if name.suffix != "":
				f.write(",\n            suffix \"" + name.suffix + "\"")
			if name.title != "":
				f.write(",\n            title \"" + name.title + "\"")
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
		authors = [HumanName(x.strip()) for x in metadata["authors"].unique()[0].split(";") if x.strip() != ""]
		for index, name in enumerate(authors, start = 1):
			f.write("          {\n")
			f.write("            name name {\n")
			f.write("              last \"" + name.last + "\",\n")
			f.write("              first \"" + name.first + "\"")
			if name.middle != "":
				f.write(",\n              middle \"" + name.middle + "\"")
			if name.suffix != "":
				f.write(",\n              suffix \"" + name.suffix + "\"")
			if name.title != "":
				f.write(",\n              title \"" + name.title + "\"")
			f.write("\n            }\n")
			if index == total_names:
				f.write("          }\n")
			else:
				f.write("          },\n")
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
		f.write("      data str \"Submission Title: " + submission_name + "\"\n")
		f.write("    }\n")
		f.write("  }\n")
		f.write("}\n")

# Create fasta file based on database
def create_fasta(organism, database, metadata, fasta_file, submission_files_dir):
	# Make sure sequence name is found in fasta file header
	fasta_df = submission_process.process_fasta_samples(metadata=metadata, fasta_file=fasta_file)
	# Now replace fasta header with appropriate sequence ids
	# Extract the required fields for specified database
	db_required_colnames = submission_process.get_required_colnames(database=database, organism=organism)
	# Get the sample names with "#" symbol
	sample_colname = list(filter(lambda x: ("#" in x)==True, db_required_colnames))[0].replace("#","").replace("*","")
	# Create fasta file
	records = []
	for index, row in fasta_df.iterrows():
		records.append(SeqRecord(row["fasta_sequence_orig"], id = row[sample_colname], description = ""))
	with open(os.path.join(submission_files_dir, "sequence.fsa"), "w+") as f:
		SeqIO.write(records, f, "fasta")

# Create a zip file for genbank submission
def create_genbank_files(organism, config_dict, metadata, fasta_file, submission_name, submission_files_dir):
	# Create authorset file
	create_authorset(config_dict=config_dict, metadata=metadata, submission_name=submission_name, submission_files_dir=submission_files_dir)
	create_fasta(organism=organism, database=["GENBANK"], metadata=metadata, fasta_file=fasta_file, submission_files_dir=submission_files_dir)
	# Retrieve the source df
	source_df = metadata.filter(regex="^gb-seq_id$|^src-|^ncbi-spuid$|^ncbi-bioproject$|^organism$|^collection_date$").copy()
	source_df.columns = source_df.columns.str.replace("src-","").str.strip()
	source_df = source_df.rename(columns = {"gb-seq_id":"Sequence_ID", "collection_date":"Collection_date", "ncbi-spuid":"strain"})
	# Add BioProject if available
	if "ncbi-bioproject" in source_df:
		source_df = source_df.rename(columns={"ncbi-bioproject": "BioProject"})
	# Make sure Sequence_ID stays in first column
	shift_col = source_df.pop("Sequence_ID")
	source_df.insert(0, "Sequence_ID", shift_col)
	source_df.to_csv(os.path.join(submission_files_dir, "source.src"), index=False, sep="\t")
	# Retrieve Structured Comment df
	comment_df = metadata.filter(regex="^cmt-")
	if not comment_df.empty:
		comment_df = metadata.filter(regex="^gb-seq_id$|^cmt-|^organism$|^collection_date$").copy()
		comment_df.columns = comment_df.columns.str.replace("cmt-", "").str.strip()
		comment_df = comment_df.rename(columns = {"gb-seq_id": "SeqID"})
		columns_no_prefix_suffix = list(filter(lambda x: (x not in ["SeqID", "StructuredCommentPrefix", "StructuredCommentSuffix"])==True, comment_df.columns))
		ordered_columns = ["SeqID", "StructuredCommentPrefix"] + columns_no_prefix_suffix + ["StructuredCommentSuffix"]
		comment_df = comment_df.reindex(columns=ordered_columns)
		comment_df.to_csv(os.path.join(submission_files_dir, "comment.cmt"), index=False, sep="\t")

# Create a zip file for genbank submission
def create_genbank_zip(submission_name, submission_files_dir):
	with ZipFile(os.path.join(submission_files_dir, submission_name + ".zip"), 'w') as zip:
		zip.write(os.path.join(submission_files_dir, "authorset.sbt"), "authorset.sbt")
		zip.write(os.path.join(submission_files_dir, "sequence.fsa"), "sequence.fsa")
		zip.write(os.path.join(submission_files_dir, "source.src"), "source.src")
		if os.path.isfile(os.path.join(submission_files_dir, "comment.cmt")):
			zip.write(os.path.join(submission_files_dir, "comment.cmt"), "comment.cmt")
	# Waiting for the zip file to write
	while not os.path.isfile(os.path.join(submission_files_dir, submission_name + ".zip")):
		time.sleep(10)

# Run Table2asn to generate sqn file for submission
def create_genbank_table2asn(submission_name, submission_files_dir, gff_file=None):
	submission_status = "processed-ok"
	submission_id = "Table2asn"
	# Create a temp file to store the downloaded table2asn
	table2asn_dir = "/tmp/table2asn"
	# Download the table2asn
	print("Downloading Table2asn.", file=sys.stdout)
	download_table2asn(table2asn_dir=table2asn_dir)
	# Command to generate table2asn submission file
	command = [table2asn_dir, "-t", os.path.join(submission_files_dir, "authorset.sbt"), "-i", os.path.join(submission_files_dir, "sequence.fsa"), "-src-file", os.path.join(submission_files_dir, "source.src"), "-o", os.path.join(submission_files_dir, submission_name + ".sqn")]
	if os.path.isfile(os.path.join(submission_files_dir, "comment.cmt")):
		command.append("-w")
		command.append( os.path.join(submission_files_dir, "comment.cmt"))
	if gff_file is not None:
		command.append("-f")
		command.append(gff_file)
	print("Running Table2asn.", file=sys.stdout)
	proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd = os.path.join(os.path.dirname(os.path.abspath(__file__))))
	if proc.returncode != 0:
		print("Table2asn-Error", file=sys.stderr)
		print(proc.stdout, file=sys.stdout)
		print(proc.stderr, file=sys.stderr)
		sys.exit(1)
	return submission_id, submission_status

# Create submission log csv
def create_submission_log(database, submission_position, organism, submission_name, submission_dir, config_file, submission_status, submission_id, table2asn, gff_file, submission_type):
	# If file doesn't exist create it
	if os.path.isfile(os.path.join(submission_dir, "submission_log.csv")) == True:
		df = pd.read_csv(os.path.join(submission_dir, "submission_log.csv"), header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False)
	else:
		df = pd.DataFrame(columns = ["Submission_Name", "Organism", "Database", "Submission_Position", "Submission_Type", "Submission_Date", "Submission_Status", "Submission_Directory", "Config_File", "Table2asn", "GFF_File", "Update_Date"])
	# Fill in the log field if it exists, otherwise create new
	df_partial = df.loc[(df["Organism"] == organism) & (df["Database"] == database) & (df["Submission_Directory"] == submission_dir) & (df["Submission_Name"] == submission_name) & (df["Submission_Type"] == submission_type)]
	# Update existing field	
	if df_partial.shape[0] > 0:
		df.loc[df_partial.index.values, "Submission_Position"] = submission_position			
		df.loc[df_partial.index.values, "Submission_Status"] = submission_id + ";" + submission_status
		df.loc[df_partial.index.values, "Table2asn"] = table2asn
		df.loc[df_partial.index.values, "GFF_File"] = gff_file
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
					 'Submission_Directory': submission_dir,
					 'Config_File': config_file,
					 'Table2asn': table2asn,
					 'GFF_File': gff_file,
					 'Update_Date': datetime.now().strftime("%Y-%m-%d")
					}
		df.loc[len(df)] = new_entry
	df.to_csv(os.path.join(submission_dir, "submission_log.csv"), header = True, index = False)
