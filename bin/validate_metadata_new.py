#!/usr/bin/env python3

# Adapted from Perl scripts by MH Seabolt and Python scripts by J Heuser
# Refactored and updated by AK Gupta and KA O'Connell

# necessary packages
import os
import pandas as pd
import warnings
import re
import argparse
import sys
import math
import yaml
import json
import shutil
from collections import Counter
from typing import List, Dict, Union
import logging

# main function
def metadata_validation_main():
	"""Main function to initiate metadata validation."""
	warnings.filterwarnings('ignore')
	
	# Load parameters
	parameters_class = GetParams()
	parameters_class.get_parameters()
	parameters = parameters_class.parameters
	
	# Load metadata
	meta_to_df = GetMetaAsDf(parameters)
	filled_df = meta_to_df.get_meta_df()
	
	if parameters['find_paths']:
		fetch_validated_metadata(filled_df, parameters) # fetch paths to already-validated metadata
	else:
		process_validation(filled_df, parameters, parameters_class) # main validation work here

# functions and classes
def fetch_validated_metadata(filled_df, parameters):
	"""Handles fetching existing report paths."""
	col_name = "sequence_name" if "sequence_name" in filled_df.columns else "sample_name" # allow flexibility in col name
	missing_tsvs = []
	for _, row in filled_df.iterrows():
		sample = row[col_name]
		src = f'{parameters["path_to_existing_tsvs"]}/{parameters["file_name"]}/tsv_per_sample/{sample}.tsv'
		dest = f'{parameters["output_dir"]}/{parameters["file_name"]}/tsv_per_sample/{sample}.tsv'
		
		if os.path.exists(src):
			shutil.copy(src, dest)
		else:
			missing_tsvs.append(src)
	
	if missing_tsvs:
		print("\nERROR: The following expected TSV files are missing:", *missing_tsvs, file=sys.stderr)
		sys.exit(1)
	else:
		print("\nPaths to existing sample metadata TSVs were found!\n")

def process_validation(filled_df, parameters, parameters_class):
	"""Runs metadata validation steps."""
	validate_checks = ValidateChecks(filled_df, parameters, parameters_class)
	validate_checks.validate_main()
	
	insert = HandleDfInserts(parameters=parameters, filled_df=validate_checks.metadata_df)
	insert.handle_df_inserts()
	
	if validate_checks.did_validation_work:
		export_validated_data(validate_checks.metadata_df, parameters)
		print("\nMetadata Validation was Successful!!!\n")
	else:
		print("\nMetadata Validation Failed. Check errors in output directory.\n")
		sys.exit(1)

def export_validated_data(metadata_df, parameters):
	"""Exports validated metadata to TSV files."""
	output_dir = f'{parameters["output_dir"]}/{parameters["file_name"]}/tsv_per_sample'
	os.makedirs(output_dir, exist_ok=True)
	
	metadata_df.rename(columns={'sample_name': 'sequence_name'}, inplace=True)
	for _, row in metadata_df.iterrows():
		sample = row['sequence_name']
		row.to_frame().transpose().set_index('sequence_name').to_csv(f'{output_dir}/{sample}.tsv', sep="\t")

class GetParams:
	""" Class constructor for getting all necessary parameters (input args from argparse and hard-coded ones)
	"""
	def __init__(self):
		self.parameters = self.get_inputs()
		# get the file name and put it in parameters dict
		self.parameters['file_name'] = self.parameters['meta_path'].split("/")[-1].split(".")[0]

	def get_parameters(self):
		""" Main function for calling others in getting parameters + setting up dirs
		"""
		# get the restrictions 
		self.get_restrictions()

		# create new directory for output if it does not exist and user does not pass in preference
		if os.path.isdir(f'{self.parameters["output_dir"]}/{self.parameters["file_name"]}'):
			os.system(f'rm -r -f {self.parameters["output_dir"]}/{self.parameters["file_name"]}')
		os.system(f'mkdir -p -m777 {self.parameters["output_dir"]}/{self.parameters["file_name"]}/errors')
		os.system(f'mkdir -p -m777 {self.parameters["output_dir"]}/{self.parameters["file_name"]}/tsv_per_sample')

	# read in parameters
	def get_inputs(self):
		""" Gets the user inputs from the argparse
		"""
		args = self.get_args().parse_args()
		parameters = vars(args)
		return parameters

	# debug (check for the key, if no key default to Pathogen.cl.1.0)
	def load_config(self):
		""" Parse config file and return BioSample package
		"""
		with open(self.parameters["config_file"], "r") as f:
			config_dict = yaml.load(f, Loader=yaml.BaseLoader) # Load yaml as str only
			return config_dict.get("BioSample_package", "Pathogen.cl.1.0")
	
	def load_required_fields(self, yaml_path):
		with open(yaml_path, "r") as f:
			fields_dict = yaml.load(f, Loader=yaml.SafeLoader)
		return fields_dict.get("BioSample_packages", {})  # Return the nested dictionary

	@staticmethod
	def get_args():
		""" Expected args from user and default values associated with them
		"""
		# initialize parser
		parser = argparse.ArgumentParser(description="Parameters for Running Metadata Validation")
		# required parameters (do not have default)
		parser.add_argument("--meta_path", type=str, help="Path to excel spreadsheet for MetaData")
		# optional parameters
		parser.add_argument("-o", "--output_dir", type=str, default='validation_outputs',
							help="Output Directory for final Files, default is current directory")
		parser.add_argument("--overwrite_output_files", type=bool, default=True, help='whether to overwrite the output dir')
		parser.add_argument("-k", "--remove_demographic_info", action="store_true", default=False,
							help="Flag to remove potentially identifying demographic info if provided otherwise no change will be made " +
								 "Applies to host_sex, host_age, race, ethnicity.")
		parser.add_argument("-d", "--date_format_flag", type=str, default="s", choices=['s', 'o', 'v'],
							help="Flag to differ date output, s = default (YYYY-MM), " +
								 "o = original(this skips date validation), v = verbose(YYYY-MM-DD)")
		parser.add_argument("--custom_fields_file", type=str, help="File containing custom fields, datatypes, and which samples to check")
		parser.add_argument("--validate_custom_fields", type=bool, help="Flag for whether or not validate custom fields ")
		parser.add_argument("--find_paths", action="store_true", help="Only check for existing TSV file paths (for use with fetch_reports_only)")
		parser.add_argument("--path_to_existing_tsvs", type=str, required=False, help="Path to existing per-sample TSVs (for use with fetch_reports_only)")
		parser.add_argument("--config_file", type=str, help="Path to submission config file with a valid BioSample_package key")
		parser.add_argument("--biosample_fields_key", type=str, help="Path to file with BioSample required fields information")
		return parser

	def get_restrictions(self):
		""" Specifies the set of values to restrict multiple variables to (strategy, source, selection, layout, and instruments)
		"""
		# Term Restrictions
		strategy_restrictions = ["WGA", "WGS", "WXS", "RNA-Seq", "miRNA-Seq", "WCS", "CLONE", "POOLCLONE", "AMPLICON",
								 "CLONEEND", "FINISHING", "ChIP-Seq", "MNase-Seq", "DNase-Hypersensitivity",
								 "Bisulfite-Seq", "Tn-Seq", "EST", "FL-cDNA", "CTS", "MRE-Seq", "MeDIP-Seq", "MBD-Seq",
								 "Synthetic-Long-Read", "ATAC-seq", "ChIA-PET", "FAIRE-seq", "Hi-C", "ncRNA-Seq",
								 "RAD-Seq", "RIP-Seq", "SELEX", "ssRNA-seq", "Targeted-Capture",
								 "Tethered Chromatin Conformation Capture", "OTHER"]
		source_restrictions = ["GENOMIC", "TRANSCRIPTOMIC", "METAGENOMIC", "METATRANSCRIPTOMIC", "SYNTHETIC", "VIRAL RNA",
							   "GENOMIC SINGLE CELL", "TRANSCRIPTOMIC SINGLE CELL", "OTHER"]
		selection_restrictions = ["RANDOM", "PCR", "RANDOM PCR", "RT-PCR", "HMPR", "MF", "CF-S", "CF-M", "CF-H", "CF-T",
								  "MDA", "MSLL", "cDNA", "ChIP", "MNase", "DNAse", "Hybrid Selection",
								  "Reduced Representation", "Restriction Digest", "5-methylcytidine antibody",
								  "MBD2 protein methyl-CpG binding domain", "CAGE", "RACE", "size fractionation",
								  "Padlock probes capture method", "other", "unspecified", "cDNA_oligo_dT",
						   		  "cDNA_randomPriming", "Inverse rRNA", "Oligo-dT", "PolyA", "repeat fractionation"]
		layout_restrictions =["single", "paired"]

		self.parameters['restricted_terms'] = [strategy_restrictions, source_restrictions,
											   selection_restrictions, layout_restrictions]
		self.parameters['illumina_instrument_restrictions'] = ["HiSeq X Five", "HiSeq X Ten", "Illumina Genome Analyzer",
									 "Illumina Genome Analyzer II",
									 "Illumina Genome Analyzer IIx", "Illumina HiScanSQ", "Illumina HiSeq 1000",
									 "Illumina HiSeq 1500", "Illumina HiSeq 2000", "Illumina HiSeq 2500",
									 "Illumina HiSeq 3000",
									 "Illumina HiSeq 4000", "Illumina iSeq 100", "Illumina NovaSeq 6000",
									 "Illumina MiniSeq",
									 "Illumina MiSeq", "NextSeq 500", "NextSeq 550", "NextSeq 1000", "NextSeq 2000",
									 "Illumina HiSeq X"]
		self.parameters['nanopore_instrument_restrictions'] = ["GridION", "MinION", "PromethION"]

class GetMetaAsDf:
	"""Loads and formats metadata into a DataFrame before validation."""
	def __init__(self, parameters):
		self.parameters = parameters
	def get_meta_df(self):
		"""Loads metadata and returns the formatted DataFrame."""
		df = self.load_meta()
		return self.populate_fields(df)
	def load_meta(self):
		"""Loads metadata from an Excel file into a DataFrame and checks for issues."""
		df = pd.read_excel(
			self.parameters['meta_path'], 
			header=[1], 
			dtype=str, 
			engine="openpyxl", 
			index_col=None, 
			na_filter=False
		)
		df = df.loc[:, ~df.columns.str.contains('^Unnamed')]  # Remove unintended columns
		# Detect duplicate columns
		duplicate_pattern = r"\.\d+$"  # Matches column names ending with .1, .2, etc.
		mangled_columns = [re.sub(duplicate_pattern, "", col) for col in df.columns if any(re.match(rf"^{re.escape(base)}{duplicate_pattern}$", col) for base in df.columns if base != col)]
		duplicate_bases = list(set(mangled_columns))
		if duplicate_bases:
			raise ValueError(f"Duplicate columns detected: {duplicate_cols}.\n"
							 "Please check your metadata file and remove duplicates.")
		if df.empty:
			raise ValueError("The metadata Excel sheet is empty. Please provide a valid file with data.")
		return df
	def populate_fields(self, df):
		"""Replace NaN values in certain columns with 'Not Provided' or an empty string."""
		
		terms_to_replace = [
			"collected_by", "sample_type", "lat_lon", "host_age", 
			"host_disease", "host_sex", "isolation_source", "purpose_of_sampling"
		]
		# Filter to include only existing columns
		existing_terms = [term for term in terms_to_replace if term in df.columns]
		# Replace empty values and NaNs with "Not Provided"
		df[existing_terms] = df[existing_terms].replace(["", None, "N/A", "NA", "n/A", "N/a"], "Not Provided").fillna("")
		# Validate populated fields
		if not all(df[col].map(lambda x: isinstance(x, str)).all() for col in existing_terms):
			raise AssertionError("Populating certain fields in the metadata df with 'Not Provided' or '' was unsuccessful.")
		return df

class ValidateChecks:
	""" Class constructor for performing a variety of checks on metadata
	"""
	def __init__(self, filled_df, parameters, get_params):
		self.metadata_df = filled_df
		self.parameters = parameters

		# set flags for error reporting
		self.nanopore_grades = {''}
		[self.meta_nanopore_grade, self.meta_illumina_grade, self.meta_core_grade, self.meta_case_grade,
		 self.author_valid, self.valid_date_flag] = [True] * 6
		self.repeated = False
		
		# error messages
		self.errors = {}
		self.error_tsv = pd.DataFrame(index=self.metadata_df['sample_name'].tolist())
		[self.sample_error_msg, self.repeat_error, self.sra_msg, self.date_error_msg, self.matchup_error,
		 				self.illumina_error_msg, self.nanopore_error_msg] = [''] * 7
		
		# actual error files 
		self.final_error_file = open(f'{self.parameters["output_dir"]}/{self.parameters["file_name"]}/errors/full_error.txt', "w")
		self.custom_fields_error_file = open(f'{self.parameters["output_dir"]}/{self.parameters["file_name"]}/errors/custom_fields_error.txt', "w")

		# global variables for keeping track of sample properties
		self.did_validation_work = True
		self.valid_sample_num = 0
		self.list_of_sample_errors = []
		self.final_cols = []

		# Set required and "at least one" fields dynamically
		self.biosample_package = get_params.load_config() # get the correct BioSample package
		self.required_fields_dict = get_params.load_required_fields(parameters['biosample_fields_key'])
		self.at_least_one_required_fields_dict = self.required_fields_dict.get("At_least_one_required", {})
		self.required_core = self.required_fields_dict.get(self.biosample_package, {}).get("required", [])
		self.optional_core = self.required_fields_dict.get(self.biosample_package, {}).get("at_least_one_required", [])
		self.case_fields = ["host_sex", "host_age", "race", "ethnicity"]
		
		## Instantiate CustomFieldsProcessor class
		self.custom_fields_processor = CustomFieldsProcessor(
			json_file=parameters['custom_fields_file'],
			error_file=self.custom_fields_error_file
		)

		# Normalize authors column
		self.normalize_author_columns()

	# Define function for logging errors
	def log_error(self, sample_name: str, error_msg: str):
		self.errors.setdefault("samples", {}).setdefault(sample_name, []).append(error_msg)

	def normalize_author_columns(self):
		""" Normalize author/authors column to always be 'authors' """
		# Rename 'author' to 'authors' if 'authors' doesn't already exist
		if 'author' in self.metadata_df.columns and 'authors' not in self.metadata_df.columns:
			self.metadata_df.rename(columns={'author': 'authors'}, inplace=True)
		elif 'authors' in self.metadata_df.columns and 'author' in self.metadata_df.columns:
			# Merge both columns if they exist, prioritizing 'authors'
			self.metadata_df['authors'] = self.metadata_df['authors'].fillna(self.metadata_df['author'])
			self.metadata_df.drop(columns=['author'], inplace=True)

	def validate_main(self):
		""" Main validation function for the metadata
		Performs these checks: duplicate samples, date, custom fields, 
		"""
		metadata_samp_names = self.metadata_df['sample_name'].tolist()

		# Ff there are repeat samples then check them and replace the names
		if len(self.metadata_df['sample_name']) != len(set(self.metadata_df['sample_name'])):
			self.check_for_repeats_in_meta()

		# Check date
		if self.parameters['date_format_flag'].lower() != 'o':
			self.check_date()

		# Check custom fields
		if self.parameters.get('validate_custom_fields', True):
			self.metadata_df = self.custom_fields_processor.process(self.metadata_df)

		for name in self.metadata_df["sample_name"]:
			sample_info = self.metadata_df.loc[self.metadata_df['sample_name'] == name].copy()
			sample_info.columns = sample_info.columns.str.lower()  # Normalize column names

			self.check_meta_core(sample_info)

			# Validate authors
			authors = sample_info["authors"].values[0] if "authors" in sample_info.columns else ""
			if authors:
				try:
					self.metadata_df.loc[self.metadata_df['sample_name'] == name, 'author'] = self.check_authors(authors)
				except Exception:
					self.author_valid = False
					self.log_error(name, "Invalid Author Name, please list as full names separated by ';'")

			# Validate metadata case (PI info)
			if self.parameters.get("remove_demographic_info", False):
				try:
					self.log_error(name, "'remove_demographic_info' flag is True. Sample demographic data will be removed if present.")
					self.metadata_df = self.check_meta_case(sample_info)
				except Exception:
					self.meta_case_grade = False
					self.log_error(name, "Unable to remove demographic data")

			# Validate SRA data
			if str(sample_info.get("ncbi_sequence_name_sra", "")).strip():
				self.sra_msg = "\n\t\tSRA Submission Detected: "
				sra_check = CheckIlluminaNanoporeSRA(
					sample_info, self.sra_msg, self.parameters,
					self.meta_nanopore_grade, self.meta_illumina_grade,
					self.nanopore_error_msg, self.illumina_error_msg
				)
				sra_check.handle_sra_submission_check()
				self.sra_msg, self.meta_nanopore_grade = sra_check.sra_msg, sra_check.meta_nanopore_grade
				self.nanopore_error_msg, self.meta_illumina_grade = sra_check.nanopore_error_msg, sra_check.meta_illumina_grade
				self.illumina_error_msg = sra_check.illumina_error_msg
	
			# Capture sample-level errors
			errors_class = HandleErrors(
				grades={
					'meta_case_grade': self.meta_case_grade, 
					'meta_illumina_grade': self.meta_illumina_grade,
					'meta_nanopore_grade': self.meta_nanopore_grade, 
					'author_valid': self.author_valid,
					'meta_core_grade': self.meta_core_grade
				},
				errors={
					'sample_error_msg': self.sample_error_msg, 
					'sra_msg': self.sra_msg,
					'illumina_error_msg': self.illumina_error_msg, 
					'nanopore_error_msg': self.nanopore_error_msg,
					'list_of_sample_errors': self.list_of_sample_errors
				},
				valid_sample_num=self.valid_sample_num,
				sample_info=sample_info,
				sample_flag=True,
				parameters=self.parameters,
				tsv=self.error_tsv,
				valid_date_flag=self.valid_date_flag
			)

			# Capture and update sample errors
			errors_class.capture_errors_per_sample()
			self.list_of_sample_errors = errors_class.list_of_sample_errors
			self.valid_sample_num = errors_class.valid_sample_num

			# Reset all checks and error messages
			self.meta_case_grade = self.meta_illumina_grade = self.meta_nanopore_grade = self.author_valid = self.meta_core_grade = True
			self.sra_msg = self.illumina_error_msg = self.nanopore_error_msg = ""

			# Trim final DataFrame if custom fields exist
			if self.final_cols:
				self.metadata_df = self.metadata_df.loc[:, self.final_cols]

			# Generate final error message
			self.did_validation_work = errors_class.capture_final_error(
				final_error_file=self.final_error_file, 
				repeat_error=self.repeat_error,
				matchup_error=self.matchup_error, 
				valid_date_flag=self.valid_date_flag,
				date_error_msg=self.date_error_msg, 
				valid_sample_num=self.valid_sample_num,
				metadata_df=self.metadata_df, 
				list_of_sample_errors=self.list_of_sample_errors, 
				repeated=self.repeated,
				did_validation_work=self.did_validation_work
			)

	def check_for_repeats_in_meta(self):
		"""Check if the metadata file has repeated samples and rename them if necessary."""
		
		sample_list = self.metadata_df['sample_name'].tolist()
		sample_counts = Counter(sample_list)

		# Identify samples that are repeated
		repeated_samples = {sample: 0 for sample, count in sample_counts.items() if count > 1}
		if repeated_samples:
			self.repeated = True
			new_samp_list = []
			# Rename repeated samples
			for sample in sample_list:
				if sample in repeated_samples:
					new_name = f"{sample}_Copy_Sample_Num_{repeated_samples[sample]}"
					self.log_error(sample, f"Sample name repeated; renamed to {new_name}")
					repeated_samples[sample] += 1
					new_samp_list.append(new_name)
				else:
					new_samp_list.append(sample)
				self.metadata_df['sample_name'] = new_samp_list
				self.repeat_error = f"\n\tRepeated Sample Names: {', '.join(repeated_samples.keys())}"
		else:
			self.repeated = False
		
	def check_date(self):
		"""
		Reformats the date based on the input flag. Accepts date formats as YYYY, YYYY-MM, YYYY-MM-DD, MMDDYYYY, MMYYYY.
		Flags dates with two-digit years (YY) as invalid.
		Uses log_error() to record missing or invalid dates and raises an error if the flag is not valid.
		"""

		# Precompile regex patterns for efficiency
		date_patterns = [
			re.compile(r"^(\d{4})(?:[-/](\d{1,2}))?(?:[-/](\d{1,2}))?(?:\s\d{2}:\d{2}:\d{2})?$"),  # YYYY, YYYY-MM, YYYY-MM-DD
			re.compile(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{4})$"),  # MM/DD/YYYY, M/D/YYYY
			re.compile(r"^(\d{1,2})[-/](\d{4})$"),  # MM/YYYY, M/YYYY
			re.compile(r"^(\d{1,2})[-/](\d{1,2})[-/](\d{2})$")  # MM/DD/YY, M/D/YY
		]

		flag = self.parameters.get('date_format_flag', '').lower()
		format_map = {'v': '{year}-{month}-{day}', 's': '{year}-{month}'}

		if flag not in format_map:
			raise ValueError(f"Unknown date_format_flag: {flag}")

		for i, (date_value, sample_name) in enumerate(zip(self.metadata_df["collection_date"], self.metadata_df["sample_name"])):
			if not date_value:  # Missing date
				self.log_error(sample_name, "Missing collection date")
				self.valid_date_flag = False
				continue

			date_value_str = str(date_value)
			match = next((p.match(date_value_str) for p in date_patterns if p.match(date_value_str)), None)

			if not match:
				self.log_error(sample_name, f"Invalid date format: {date_value_str}")
				self.valid_date_flag = False
				continue

			year, month, day, *_ = match.groups()
			if len(year) == 2:
				self.log_error(sample_name, "Two-digit year detected. Use a four-digit year.")
				self.valid_date_flag = False
				continue

			# Ensure month and day are always two digits
			month = (month or "01").zfill(2)
			day = (day or "01").zfill(2)

			# Apply the correct format based on flag
			self.metadata_df.at[i, "collection_date"] = format_map[flag].format(year=year, month=month, day=day)
	
	def check_authors(self, authors):
		"""Ensures author names follow First Last or F.M. Last format."""
		cleaned_authors = []
		author_list = authors.split(";")

		for author in author_list:
			cleaned_name = re.sub(r"[^\w\s.]", "", author).strip()  # Remove unwanted characters
			name_parts = cleaned_name.split()

			# Format as "F.M. Last" if 3 names are present
			if len(name_parts) == 3 and len(name_parts[0]) > 1:
				formatted_name = f"{name_parts[0][0]}.{name_parts[1][0]}. {name_parts[2]}"
			else:
				formatted_name = cleaned_name

			cleaned_authors.append(formatted_name)

		if len(cleaned_authors) != len(author_list):
			raise ValueError("Mismatch between input and processed author names.")
		return "; ".join(cleaned_authors)

	def check_meta_core(self, sample_info):
		"""Checks that the necessary metadata is present for the sample."""
		missing_fields = []
		missing_optionals = []

		# Check required fields
		for field in self.required_core:
			value = sample_info.get(field, pd.Series([""])).iloc[0]  # Fix the indexing issue
			if not str(value).strip():  # Check for empty values
				missing_fields.append(field)

		# Check "at least one required" groups
		for group in self.optional_core:
			if not any(str(sample_info.get(field, [""])[0]).strip() for field in group if field in sample_info):
				missing_optionals.append(group)  # Track missing groups
	
		# Log errors for required fields
		if missing_fields:
			self.meta_core_grade = False
			self.log_error(
				sample_info["sample_name"].values[0],
				f"Missing Required Metadata: {', '.join(missing_fields)}"
			)

		# Log errors for missing optional groups
		if missing_optionals:
			self.meta_core_grade = False
			missing_optional_str = "; ".join([" | ".join(group) for group in missing_optionals])
			self.log_error(
				sample_info["sample_name"].values[0],
				f"Missing 'At Least One Required' Metadata: {missing_optional_str}"
			)

	def check_meta_case(self, sample_info):
		"""Checks and removes demographic metadata if 'remove_demographic_info' is enabled."""
		invalid_case_data = [field for field in self.case_fields if field in sample_info.columns and sample_info[field].values[0] not in ["", None, "Not Provided"]]

		for field in invalid_case_data:
			sample_info.at[sample_info.index[0], field] = "Not Provided"  # Replace value

		if invalid_case_data:
			self.log_error(sample_info["sample_name"].values[0], f"Present Case Data found in: {', '.join(invalid_case_data)}. Case data has been removed.")

		self.metadata_df.update(sample_info)
		return self.metadata_df
	

class CheckIlluminaNanoporeSRA:
	def __init__(self, sample_info, sra_msg, parameters, meta_nanopore_grade, meta_illumina_grade, nanopore_error_msg, illumina_error_msg):
		self.sample_info, self.sra_msg, self.parameters = sample_info, sra_msg, parameters
		self.meta_nanopore_grade, self.meta_illumina_grade = meta_nanopore_grade, meta_illumina_grade
		self.nanopore_error_msg, self.illumina_error_msg = nanopore_error_msg, illumina_error_msg
		self.required = {
			"illumina": ["illumina_sequencing_instrument", "illumina_library_strategy", "illumina_library_source",
					 "illumina_library_selection", "illumina_library_layout"],
			"nanopore": ["nanopore_sequencing_instrument", "nanopore_library_strategy", "nanopore_library_source",
					  "nanopore_library_selection", "nanopore_library_layout"]
		}

	def handle_sra_submission_check(self):
		illum_paths = [
			str(self.sample_info.get("illumina_sra_file_path_1", "")).strip(),
			str(self.sample_info.get("illumina_sra_file_path_2", "")).strip()
		]
		nano_path = str(self.sample_info.get("nanopore_sra_file_path_1", "")).strip()

		if all(illum_paths):  # Now it will correctly check if both paths are non-empty strings
			self.check_instruments("illumina")
			self.sra_msg += " Illumina Found\t"
		else:
			self.sra_msg += " Illumina Not Found\t"

		if nano_path:  # Ensuring it's a proper string
			self.check_instruments("nanopore")
			self.sra_msg += " Nanopore Found"
		else:
			self.sra_msg += " Nanopore Not Found"

	def check_instruments(self, instrument_type):
		required_fields = self.required[instrument_type]
		instrument = str(self.sample_info.get(f"{instrument_type}_sequencing_instrument", "")).strip()
		file_paths = [
			str(self.sample_info.get(f"{instrument_type}_sra_file_path_1", "")).strip()
		] if instrument_type == "nanopore" else [
			str(self.sample_info.get("illumina_sra_file_path_1", "")).strip(),
			str(self.sample_info.get("illumina_sra_file_path_2", "")).strip()
			if str(self.sample_info.get("illumina_library_layout", "")).strip().lower() == "paired" else ""
		]
		restricted_terms = [
			str(term).strip() for term in self.parameters.get(f"{instrument_type}_instrument_restrictions", [])
		]
		missing_data = [field for field in required_fields if field not in self.sample_info]
		invalid_data = [instrument] if instrument not in restricted_terms else []
		path_failed = any(not os.path.isfile(path) for path in file_paths if path)

		if missing_data or invalid_data or path_failed:
			grade_attr = f"meta_{instrument_type}_grade"
			setattr(self, grade_attr, False)
			error_attr = f"{instrument_type}_error_msg"
			if missing_data:
				setattr(self, error_attr, getattr(self, error_attr) + f'\n\t\t{instrument_type.capitalize()} Missing Data: {", ".join(missing_data)}')
			if invalid_data:
				setattr(self, error_attr, getattr(self, error_attr) + f'\n\t\t{instrument_type.capitalize()} Invalid Data: {", ".join(invalid_data)}')
			if path_failed:
				setattr(self, error_attr, getattr(self, error_attr) + '\n\t\tOne or more SRA files do not exist or have permission issues' )

class HandleErrors:
	""" Class for handling errors at the sample and global levels. """
	
	def __init__(self, grades, errors, valid_sample_num, sample_info, sample_flag, parameters, tsv, valid_date_flag):
		self.grades = grades  # Store grades as a dictionary
		self.errors = errors  # Store errors as a dictionary
		self.valid_sample_num = valid_sample_num
		self.sample_info = sample_info
		self.sample_flag = sample_flag
		self.valid_date_flag = valid_date_flag
		self.parameters = parameters
		self.tsv = tsv
		self.list_of_sample_errors = errors['list_of_sample_errors']
		# get the other necessary values
		self.valid_sample_num = valid_sample_num

		# Ensure error list is always a list
		if not isinstance(self.errors["list_of_sample_errors"], list):
			self.errors["list_of_sample_errors"] = []

	def capture_errors_main(self):
		""" Main function for handling sample-level errors. """
		if self.sample_flag:
			self.capture_errors_per_sample()

	def capture_errors_per_sample(self):
		""" Handles errors at the sample level. """
		
		sample_passed = all(self.grades.values())  # Check if all grades are True

		# Capture SRA-related errors
		if str(self.sample_info.get("ncbi_sequence_name_sra", "")).strip():
			self.errors["sample_error_msg"] += self.errors["sra_msg"]

		# Append appropriate error messages
		self.errors["sample_error_msg"] += "\n\t\tErrors:"
		if sample_passed:
			self.errors["sample_error_msg"] += "\n\t\t\tPassed all sample checks!"
			self.valid_sample_num += 1
		else:
			for key, value in self.grades.items():
				if not value:
					error_key = f"{key.replace('meta_', '')}_error_msg"  # Match grade with its error message
					if error_key in self.errors:
						self.errors["sample_error_msg"] += self.errors[error_key]

		# Store the error message for this sample
		self.errors["list_of_sample_errors"].append(self.errors["sample_error_msg"])

		# Write the result to the TSV file
		self.write_tsv_file(sample_passed)

	def capture_final_error(self, final_error_file, repeat_error, matchup_error, valid_date_flag, date_error_msg, valid_sample_num, metadata_df, list_of_sample_errors, repeated, did_validation_work):
		""" Handles the final error message at the global level. """

		final_error = ""
		if repeated:
			did_validation_work = False
			final_error += repeat_error
		if not valid_date_flag:
			did_validation_work = False
			final_error += f"{date_error_msg}\n"

		final_error_file.write("General Errors:\n\n")
		final_error_file.write(final_error if final_error else "\tPassed all global checks!")

		# Write sample errors
		final_error_file.write(f"\n\nSample Errors:\n")
		final_error_file.write(f"\n\tNumber of Valid Samples: {valid_sample_num}/{len(metadata_df['sample_name'])}\n")
		for sample in list_of_sample_errors:
			final_error_file.write(f"{sample}\n")

		# Save errors as TSV
		self.tsv.to_csv(f"{self.parameters['output_dir']}/{self.parameters['file_name']}/errors/checks.tsv", sep="\t")

		return did_validation_work

	def write_tsv_file(self, sample_passed):
		""" Writes the validation results to a TSV file. """
		self.tsv["passed"] = "Yes" if sample_passed else "No"

		for key, value in self.grades.items():
			column_name = key.replace("meta_", "")  # Extract column name (e.g., "nanopore", "illumina")
			self.tsv[column_name] = u'\u2713' if value else 'X'

import pandas as pd

class HandleDfInserts:
	"""Handles insert operations on the metadata dataframe after all checks are completed."""
	
	def __init__(self, parameters, filled_df):
		self.parameters = parameters
		self.filled_df = filled_df

	def handle_df_inserts(self):
		"""Runs all insert operations and validates the final dataframe."""
		self.insert_loc_data()
		self.insert_additional_columns()
		self.change_illumina_paths()
		self.validate_inserts()

	def insert_loc_data(self):
		"""Creates 'geo_loc_name' by combining 'country' and 'state'."""
		self.filled_df["geo_loc_name"] = self.filled_df.apply(
			lambda row: f"{row['country']}: {row['state']}" if pd.notna(row['state']) and row['state'].strip() else row['country'],
			axis=1
		)

	def insert_additional_columns(self):
		"""Adds required metadata columns."""
		self.filled_df["structuredcomment"] = "Assembly-Data"

	def change_illumina_paths(self):
		"""Renames and reformats Illumina paths."""
		# Extract file names from paths
		self.filled_df["fastq_path_1"] = self.filled_df["illumina_sra_file_path_1"].apply(lambda path: path.split("/")[-1] if isinstance(path, str) else path)
		self.filled_df["fastq_path_2"] = self.filled_df["illumina_sra_file_path_2"].apply(lambda path: path.split("/")[-1] if isinstance(path, str) else path)
		
		# Drop old columns (optional, remove if you want to keep the original paths)
		self.filled_df.drop(columns=["illumina_sra_file_path_1", "illumina_sra_file_path_2"], inplace=True, errors="ignore")

	def validate_inserts(self):
		"""Ensures required columns were correctly added."""
		required_columns = ["geo_loc_name", "structuredcomment"]
		missing_columns = [col for col in required_columns if col not in self.filled_df.columns]
		if missing_columns:
			raise AssertionError(f"Missing required columns: {', '.join(missing_columns)}")
		# Ensure no NaN values in required fields
		for col in required_columns:
			if not self.filled_df[col].notna().all():
				raise AssertionError(f"Column '{col}' contains missing values.")

class CustomFieldsProcessor:
	def __init__(self, json_file: str, error_file: str):
		self.json_file = os.path.abspath(json_file)
		self.error_file = error_file

	def load_json(self) -> Dict[str, Dict[str, Union[str, int]]]:
		"""Load JSON data from a file."""
		print(f'Custom file: {self.json_file}')
		try:
			with open(self.json_file, 'r') as custom_file:
				return json.load(custom_file)
		except FileNotFoundError:
			raise FileNotFoundError(f"File not found: {self.json_file}")
		except json.JSONDecodeError as e:
			raise ValueError(f"Error decoding JSON: {e}")
		
	def validate_metadata_fields(self, metadata_df: pd.DataFrame):
		"""
		Flag fields in the metadata dataframe that are not present in the JSON custom fields.
		"""
		custom_fields_dict = self.load_json()
		json_keys = set(custom_fields_dict.keys())
		# Find metadata fields that are not in the JSON keys
		static_metadata_columns = ["sample_name","sequence_name","ncbi-spuid","ncbi-spuid_namespace","ncbi-bioproject","title","description","authors","submitting_lab",
			"submitting_lab_division","submitting_lab_address","publication_status","publication_title","isolate", "isolation_source","host","organism","collection_date",
			"country","state","collected_by","sample_type","lat_lon","purpose_of_sampling","host_sex","host_age","race","ethnicity","assembly_protocol","assembly_method",
			"mean_coverage","fasta_path","gff_path","ncbi_sequence_name_sra","illumina_sequencing_instrument","illumina_library_strategy","illumina_library_source",
			"illumina_library_selection","illumina_library_layout","illumina_library_protocol","illumina_sra_file_path_1", "illumina_sra_file_path_2","file_location",
			"fastq_path_1","fastq_path_2","nanopore_sequencing_instrument","nanopore_library_strategy","nanopore_library_source","nanopore_library_selection",
			"nanopore_library_layout","nanopore_library_protocol","nanopore_sra_file_path_1","nanopore_sra_file_path_2"]
		metadata_columns = set(metadata_df.columns) - set(static_metadata_columns).intersection(metadata_df.columns) # inrtersection method ensures we only compare columns that exist in metadata_df
		unexpected_fields = metadata_columns - json_keys
		if unexpected_fields:
			print(f"The following fields in the metadata dataframe are not in the JSON custom fields: {unexpected_fields}")
		else:
			print("All metadata fields are accounted for in the JSON custom fields.")
		return unexpected_fields
	
	def validate_and_process_fields(
		self, 
		custom_fields_dict: Dict[str, Dict[str, Union[str, int]]], 
		metadata_df: pd.DataFrame,
		unexpected_fields: set ) -> pd.DataFrame:
		"""Validate custom fields and integrate with metadata."""
		errors = []
		for field_name, properties in custom_fields_dict.items():
			field_errors = []
			# Handle "replace_empty_with" key
			for key in properties:
				# make backwards compatible with the old custom fields JSON (which includes other keys)
				if key not in ['replace_empty_with', 'new_field_name']:
					errors.append(f"Warning: Extra key '{key}' found under field '{field_name}' and will be ignored.")
			if "replace_empty_with" in properties:
				replace_value = properties["replace_empty_with"]
				if field_name in metadata_df.columns:
					metadata_df[field_name].fillna(replace_value, inplace=True)
			# Handle "new_field_name" key
			if "new_field_name" in properties and properties["new_field_name"]:
				new_field_name = properties["new_field_name"]
				if field_name in metadata_df.columns:
					metadata_df.rename(columns={field_name: new_field_name}, inplace=True)
				else:
					field_errors.append(f"Field '{field_name}' not found in metadata for renaming.")
			# Log errors for the current field
			if field_errors:
				errors.append({"field_name": field_name, "errors": field_errors})
		# Include unexpected fields as-is with a warning
		if unexpected_fields:
			print(f"WARNING: {unexpected_fields} were not found in the custom fields JSON and were not validated. They are included as-is.")
		# Write errors to the error file
		if errors:
			self.write_errors(errors)
		return metadata_df

	def write_errors(self, errors: Dict[str, Union[Dict, List]]):
		"""Write errors to a file."""
		json.dump(errors, self.error_file, indent=4)

	def process(self, metadata_df: pd.DataFrame) -> pd.DataFrame:
		"""Main processing function."""
		# Flag unexpected fields in the metadata file
		unexpected_fields = self.validate_metadata_fields(metadata_df)
		data = self.load_json()
		return self.validate_and_process_fields(data, metadata_df, unexpected_fields)

if __name__ == "__main__":
	metadata_validation_main()
