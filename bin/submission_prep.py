#!/usr/bin/env python3

# Python Libraries
import os
import sys
import yaml
import shutil
import subprocess
import time
from datetime import datetime
import argparse
from lxml import etree
from zipfile import ZipFile
from nameparser import HumanName
import pandas as pd
#import pathlib
#from datetime import datetime
#from distutils.util import strtobool

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
		help="Fasta file to be submitted",
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
				if not k.startswith('NCBI') and not v:
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
	if "genbank" not in database:
		contact = etree.SubElement(organization, "Contact", email=config_dict["Description"]["Organization"]["Submitter"]["@email"])
		name = etree.SubElement(contact, "Name")
		first_name = etree.SubElement(name, "First")
		first_name.text = config_dict["Description"]["Organization"]["Submitter"]["Name"]["First"]
		last_name = etree.SubElement(name, "Last")
		last_name.text = config_dict["Description"]["Organization"]["Submitter"]["Name"]["Last"]
	# XML actions
	if "genbank" in database:
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
	if "biosample" in database:
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
	if "sra" in database:
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

# create the submission status csv
def create_submission_status_csv(database, sequence_names, submission_status_file):
	status_submission_df = sequence_names.copy()
	if "biosample" in database:
		status_submission_df.loc[:, "biosample_status"] = ""
		status_submission_df.loc[:, "biosample_accession"] = ""
		status_submission_df.loc[:, "biosample_message"] = ""
	if "sra" in database:
		status_submission_df.loc[:, "sra_status"] = ""
		status_submission_df.loc[:, "sra_accession"] = ""
		status_submission_df.loc[:, "sra_message"] = ""
	if "genbank" in database:
		status_submission_df.loc[:, "genbank_status"] = ""
		status_submission_df.loc[:, "genbank_accession"] = ""
		status_submission_df.loc[:, "genbank_message"] = ""
	if "gisaid" in database:
		status_submission_df.loc[:, "gisaid_accession_epi_isl_id"] = ""
		status_submission_df.loc[:, "gisaid_accession_epi_id"] = ""
		status_submission_df.loc[:, "gisaid_message"] = ""
	status_submission_df.to_csv(submission_status_file, header = True, index = False)


# Create a authorset file
def create_authorset(config_dict, metadata, submission_name, submission_files_dir):
	submitter_first = config_dict["Description"]["Submitter"]["Name"]["First"]
	submitter_last = config_dict["Description"]["Submitter"]["Name"]["Last"]
	submitter_email = config_dict["Description"]["Submitter"]["@email"]
	alt_submitter_email = config_dict["Description"]["Submitter"]["@alt_email"]
	affil = config_dict["Description"]["Address"]["Affil"]
	div = config_dict["Description"]["Address"]["Div"]
	publication_status = metadata["gb-publication_status"].unique()[0]
	publication_title = metadata["gb-publication_title"].unique()[0]
	street = config_dict["Description"]["Address"]["Street"]
	city = config_dict["Description"]["Address"]["City"]
	sub = config_dict["Description"]["Address"]["State"]
	country = config_dict["Description"]["Address"]["Country"]
	email = config_dict["Description"]["Address"]["Email"]
	phone = config_dict["Description"]["Address"]["Phone"]
	zip_code = config_dict["Description"]["Address"]["Postal_code"]
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

# get locus tag from gff file for Table2asn submission
def get_gff_locus_tag(gff_file):
	""" Read the locus lag from the GFF3 file for use in table2asn command"""
	locus_tag = None
	with open(gff_file, 'r') as file:
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

# Create a zip file for genbank submission
def create_genbank_files(config_dict, metadata, fasta_file, submission_name, submission_files_dir):
	# Create authorset file
	create_authorset(config_dict=config_dict, metadata=metadata, submission_name=submission_name, submission_files_dir=submission_files_dir)
	shutil.copy(fasta_file, os.path.join(submission_files_dir, "sequence.fsa"))
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

# Detect multiple contig fasta
def is_multicontig_fasta(fasta):
	headers = set()
	with open(fasta, 'r') as file:
		for line in file:
			if line.startswith('>'):
				headers.add(line.strip())
				if len(headers) > 1:
					return True
	return False

# Run Table2asn to generate sqn file for submission
def create_genbank_table2asn(submission_name, submission_files_dir, annotation_file=None):
	submission_status = "processed-ok"
	submission_id = "Table2asn"
	# Create a temp file to store the downloaded table2asn
	table2asn_dir = os.getcwd() + "/table2asn"
	# Download the table2asn
	# Command to generate table2asn submission file
	fasta = os.path.join(submission_files_dir, "sequence.fsa")
	if annotation_file.endswith('tbl'):
		locus_tag_val = "-no-locus-tags-needed"
	else:
		locus_tag_val = f'"-locus-tag-prefix", {get_gff_locus_tag(annotation_file)}'
	command = [table2asn_dir, "-t", os.path.join(submission_files_dir, "authorset.sbt"), "-i", fasta, \
		"-src-file", os.path.join(submission_files_dir, "source.src"), "-o", os.path.join(submission_files_dir, submission_name + ".sqn")]
	command.append(locus_tag_val)
	if is_multicontig_fasta(fasta):
		command.append("-M")
		command.append("n")
		command.append("-Z")
	if os.path.isfile(os.path.join(submission_files_dir, "comment.cmt")):
		command.append("-w")
		command.append( os.path.join(submission_files_dir, "comment.cmt"))
	if annotation_file is not None:
		command.append("-f")
		command.append(os.path.join(os.getcwd(), annotation_file))
	print("Running Table2asn.", file=sys.stdout)
	print(command)
	proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd = os.path.join(os.path.dirname(os.path.abspath(__file__))))
	if proc.returncode != 0:
		print("Table2asn-Error", file=sys.stderr)
		print(proc.stdout, file=sys.stdout)
		print(proc.stderr, file=sys.stderr)
		sys.exit(1)
	return submission_id, submission_status

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



# Check raw reads files listed in metadata file
def check_raw_read_files(submission_name, metadata):
	# Check raw reads files if SRA is provided
	raw_reads_path = os.path.join(os.getcwd(), submission_name, "raw_reads")
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

# Create directory and files for NCBI database submissions
def create_ncbi_submission(organism, database, submission_name, config_dict, metadata, fasta_file=None, annotation_file=None):
	# Create a database subfolder within the submission directory to dump all submission files
	submission_files_dir = os.path.join(os.getcwd(), submission_name, database)
	# Create submission files directory
	os.makedirs(submission_files_dir, exist_ok=True)
	# Output message
	print("\n" + "Creating submission files for "+database, file=sys.stdout)
	# Create submission status csv
	if "biosample" in database:
		sequence_names = metadata["ncbi-spuid"].drop_duplicates()
	elif "sra" in database:
		sequence_names = metadata["ncbi-spuid"].drop_duplicates()
		# Validate and write raw reads location
		raw_files_list = check_raw_read_files(submission_name=submission_name, metadata=metadata)
		with open(os.path.join(submission_files_dir, "raw_reads_location.txt"), "w+") as file:
			for line in raw_files_list:
				file.write(line + "\n")
	elif "genbank" in database:
		sequence_names = metadata["gb-seq_id"]
		# Create genbank specific files
		create_genbank_files(submission_name=submission_name, submission_files_dir=submission_files_dir, config_dict=config_dict, metadata=metadata, fasta_file=fasta_file)
		# Use Table2asn to generate output files for submission (ASN.1 files, validation reports, sequence files, feature table files)
		# Note: maybe move these to submission script
		create_genbank_table2asn(submission_name=submission_name, submission_files_dir=submission_files_dir, annotation_file=annotation_file)
	# Generate NCBI database submission xml
	xml_str = create_submission_xml(organism=organism, database=database, submission_name=submission_name, metadata=metadata, config_dict=config_dict, failed_seqs_auto_removed=True)
	save_xml(submission_xml=xml_str, submission_files_dir=submission_files_dir)
	# Save submission xml
	print("Files are stored at: " + os.path.join(submission_files_dir), file=sys.stdout)


# Create directory and files for GISAID submission
# Note: probably need to rework some of this, haven't tested
def create_gisaid_submission(organism, database, submission_name, config_dict, metadata, fasta_file):
	# Create a database subfolder within the submission directory to dump all submission files
	submission_files_dir = os.path.join(os.getcwd(), submission_name, database)
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
	shutil.copy(fasta_file, os.path.join(submission_files_dir, "orig_sequence.fsa"))
	print("\n"+"Creating submission files for " + database, file=sys.stdout)
	print("Files are stored at: " + os.path.join(submission_files_dir), file=sys.stdout)

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
	
	# Check config file
	config_dict = get_config(config_file=config_file, gisaid_submission=gisaid_submission)
	# Check metadata file
	metadata = get_metadata(metadata_file=metadata_file)

	for database_name in database:
		if database_name in ["biosample", "sra", "genbank"]:
			create_ncbi_submission(organism=organism, database=database_name, submission_name=submission_name, config_dict=config_dict["NCBI"], metadata=metadata, fasta_file=fasta_file, annotation_file=annotation_file)
		elif "gisaid" in database_name:
			create_gisaid_submission(organism=organism, database=database_name, submission_name=submission_name, config_dict=config_dict["GISAID"], metadata=metadata, fasta_file=fasta_file)

	# Get sequence names
	# Note: these IDs are all kinds of messed up and need to be updated in metadata validation, leaving for now
	for database_name in database:
		if database_name in ["biosample", "sra", "genbank"]:
			sequence_names = metadata[["ncbi-spuid","ncbi_sequence_name_sra"]]
		elif "gisaid" in database_name:
			if "FLU" in organism:
				sequence_names = metadata[["sample_name","ncbi_sequence_name_sra"]]
			elif "COV" in organism:
				sequence_names = metadata[["sample_name"]]
	
	# Create submission status csv
	submission_status_file = os.path.join(os.getcwd(), submission_name, "submission_report_status.csv")
	create_submission_status_csv(database=database, sequence_names=sequence_names, submission_status_file=submission_status_file)
	
if __name__ == "__main__":
	main() 