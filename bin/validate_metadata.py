#!/usr/bin/env python3

# Adapted from Perl scripts by MH Seabolt and Python scripts by J Heuser
# Refactored and updated by J Rowell, AK Gupta, and KA O'Connell

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
from collections import defaultdict

def metadata_validation_main():
	""" Main for initiating metadata validation steps
	"""
	warnings.filterwarnings('ignore')

	# get all parameters needed for running the steps
	parameters_class = GetParams()
	parameters_class.get_parameters()
	parameters = parameters_class.parameters

	# call the constructor class for converting meta to df
	meta_to_df = GetMetaAsDf(parameters)
  
	# print error message if ValueError is raised when GetMetaAsDf is run
	try:
		meta_to_df.load_meta()
		print("Metadata loaded and validated successfully.")
	except ValueError as e:
		print(f"Error: {e}")
		sys.exit(1)
	
	filled_df = meta_to_df.df
		
	# call the main function for validating the metadata
	validate_checks = ValidateChecks(filled_df, parameters, parameters_class)
	validate_checks.validate_main()
	print(f"Available keys after validate_checks: {filled_df.keys().tolist()}")

	# insert necessary columns in metadata dataframe
	insert = HandleDfInserts(filled_df, parameters)
	final_df = insert.handle_df_inserts() # final updated, validated dataframe

	# normalize all values here before batching
	final_df = final_df.applymap(validate_checks.normalize_value)

	# output the batched tsv files  
	batch_size = parameters['batch_size']
	output_dir = ("batched_tsvs")
	os.makedirs(output_dir, exist_ok=True)

	total_rows = len(final_df)
	num_batches = math.ceil(total_rows / batch_size)
	batch_log = {}
	print(f"batch size is {parameters['batch_size']} and number of batches is {num_batches}") # debug
	
	for i in range(num_batches):
		start_idx = i * batch_size
		end_idx = min(start_idx + batch_size, total_rows)
		batch_df = final_df.iloc[start_idx:end_idx]
		batch_file = os.path.join(output_dir, f'batch_{i+1}.tsv')
		batch_df.to_csv(batch_file, sep='\t', index=False)
		batch_log[f"batch_{i+1}.tsv"] = batch_df["sample_name"].tolist()

	# Write the JSON batch-to-sample dictionary 
	summary_path = os.path.join(output_dir, "batch_summary.json")
	with open(summary_path, "w") as json_file:
		json.dump(batch_log, json_file, indent=4)

	print(f"\n Metadata successfully split into {num_batches} batch file(s) in {output_dir}.\n")
	print(f"Summary written to: {summary_path}\n")

# Will need to move this somewhere else (before GENBANK runs, need to run this check)
def retrieve_existing_batch_tsvs(filled_df: pd.DataFrame, parameters: dict):
	"""Retrieve and verify existing batch TSVs and their associated samples."""
	summary_path = os.path.join(parameters["path_to_existing_tsvs"], "batched_tsvs", "batch_summary.json")

	if not os.path.exists(summary_path):
		print(f"\nERROR: batch_summary.json not found at {summary_path}\n", file=sys.stderr)
		sys.exit(1)

	with open(summary_path, "r") as f:
		batch_summary = json.load(f)

	missing_batches = []

	expected_samples = set(filled_df['sample_name'])
	found_samples = set()

	for batch_file, samples in batch_summary.items():
		src_batch_path = os.path.join(parameters["path_to_existing_tsvs"], "batched_tsvs",	batch_file)
		dest_batch_path = os.path.join("batched_tsvs", batch_file)

		if os.path.exists(src_batch_path):
			os.makedirs(os.path.dirname(dest_batch_path), exist_ok=True)
			shutil.copy(src_batch_path, dest_batch_path)
			found_samples.update(samples)
		else:
			missing_batches.append(batch_file)

	missing_samples = expected_samples - found_samples

	if not missing_batches and not missing_samples:
		print(f'\nAll batch TSV files and expected samples were found!\n')
	else:
		if missing_batches:
			print("\nERROR: The following batch TSV files are missing:\n", file=sys.stderr)
			for missing in missing_batches:
				print(f"  - {missing}", file=sys.stderr)

		if missing_samples:
			print("\nERROR: The following samples were not found in any batch file:\n", file=sys.stderr)
			for sample in missing_samples:
				print(f"  - {sample}", file=sys.stderr)
		sys.exit(1)

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

	# read in parameters
	def get_inputs(self):
		""" Gets the user inputs from the argparse
		"""
		args = self.get_args().parse_args()
		parameters = vars(args)
		return parameters

	def load_config(self):
		""" Parse config file and return BioSample package
		"""
		with open(self.parameters["config_file"], "r") as f:
			config_dict = yaml.load(f, Loader=yaml.BaseLoader) # Load yaml as str only
			return config_dict.get("BioSample_package", "Pathogen.cl.1.0") # if no key default to Pathogen.cl.1.0
	
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
		parser.add_argument("--meta_path", type=str, help="Path to excel spreadsheet for Metadata")
		# optional parameters
		parser.add_argument("--batch_size", type=int, default=1, 
					  		help="Number of samples to process per batch")
		parser.add_argument("-o", "--output_dir", type=str, default='validation_outputs',
							help="Output Directory for final files, default is current directory")
		parser.add_argument("--overwrite_output_files", action="store_true", default=True, 
					  		help='Flag for whether to overwrite the output dir')
		parser.add_argument("-k", "--remove_demographic_info", action="store_true", default=False,
							help="Flag to remove potentially identifying demographic info if provided otherwise no change will be made " +
								 "Applies to host_sex, host_age, race, ethnicity.")
		parser.add_argument("-d", "--date_format_flag", type=str, default="s", choices=['s', 'o', 'v'],
							help="Flag to differ date output, s = default (YYYY-MM), " +
								 "o = original(this skips date validation), v = verbose(YYYY-MM-DD)")
		parser.add_argument("--custom_fields_file", type=str, 
					  		help="File containing custom fields, datatypes, and which samples to check")
		parser.add_argument("--validate_custom_fields", action="store_true", default=True, 
					  		help="Flag for whether or not validate custom fields ")
		parser.add_argument("--config_file", type=str, 
					  		help="Path to submission config file with a valid BioSample_package key")
		parser.add_argument("--biosample_fields_key", type=str, 
					  		help="Path to file with BioSample required fields information")
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
									 "Illumina Genome Analyzer II", "Illumina Genome Analyzer IIx", "Illumina HiScanSQ", "Illumina HiSeq 1000",
									 "Illumina HiSeq 1500", "Illumina HiSeq 2000", "Illumina HiSeq 2500", "Illumina HiSeq 3000",
									 "Illumina HiSeq 4000", "Illumina iSeq 100", "Illumina NovaSeq 6000", "Illumina MiniSeq", 
									 "Illumina MiSeq", "NextSeq 500", "NextSeq 550", "NextSeq 1000", "NextSeq 2000", "Illumina HiSeq X"]
		self.parameters['nanopore_instrument_restrictions'] = ["GridION", "MinION", "PromethION"]


class GetMetaAsDf:
	""" Class constructor to get the metadata into proper df format before running checks on it
	"""
	def __init__(self, parameters):
		self.parameters = parameters
		self.df = self.load_meta()

	def load_meta(self):
		""" Loads the metadata file in as a dataframe from an Excel file (.xlsx)
		"""
		df = pd.read_excel(self.parameters['meta_path'], header=[1], dtype = str, engine = "openpyxl", index_col=None, na_filter=False)
		df = df.loc[:, ~df.columns.str.contains('^Unnamed')] # Remove "Unnamed" col that sometimes gets imported due to trailing commas
		# Check for duplicate columns - pandas imports duplicate columns with .1, .2 endings so detect these and return an error if found
		duplicate_pattern = r"\.\d+$"  # Matches column names ending with .1, .2, etc.
		mangled_columns = [re.sub(duplicate_pattern, "", col) for col in df.columns if any(re.match(rf"^{re.escape(base)}{duplicate_pattern}$", col) for base in df.columns if base != col)]
		duplicate_bases = list(set(mangled_columns))
		if duplicate_bases:
			raise ValueError(f"Duplicate columns detected in the metadata due to renaming: {duplicate_bases}.\n"
					"Please check your metadata, remove duplicate columns, and try again.")
		# Check for empty dataframe
		if df.empty:
			raise ValueError("The metadata Excel sheet is empty. Please provide a valid file with data.")
		
		# Check if 'sample_name' column exists
		if 'sample_name' not in df.columns:
			error_message = "Error: The metadata file is missing the 'sample_name' column. Please provide a valid file with the 'sample_name' column."
			print(error_message, file=sys.stderr)  # Print the error message to stderr
			sys.stderr.flush()  # Ensure the error message is flushed to stderr
			sys.exit(1)
		
		# Check for missing sample_name values
		if df['sample_name'].isnull().any() or (df['sample_name'].str.strip() == "").any():
			missing_indices = df[df['sample_name'].isnull() | (df['sample_name'].str.strip() == "")].index.tolist()
			error_message = f"Error: The metadata file contains missing values in the 'sample_name' column at rows: {missing_indices}. Please provide valid sample names."
			print(error_message, file=sys.stderr)  # Print the error message to stderr
			sys.exit(1)

		return df

class ValidateChecks:
	""" Class constructor for performing a variety of checks on metadata
	"""
	def __init__(self, filled_df, parameters, get_params):
		# passed into class constructor
		self.metadata_df = filled_df
		self.parameters = parameters
		self.global_log = []
		self.sample_log = defaultdict(list)  # sample_name -> list of messages

		# Set required and "at least one" fields dynamically
		self.biosample_package = get_params.load_config() # get the correct BioSample package
		self.required_fields_dict = get_params.load_required_fields(parameters['biosample_fields_key'])
		self.at_least_one_required_fields_dict = self.required_fields_dict.get("At_least_one_required", {})
		self.required_core = self.required_fields_dict.get(self.biosample_package, {}).get("required", [])
		self.optional_core = self.required_fields_dict.get(self.biosample_package, {}).get("at_least_one_required", [])
		self.case_fields = ["host_sex", "host_age", "race", "ethnicity"]

		# normalize authors column
		self.normalize_author_columns()

	def validate_main(self):
		""" Main function that performs metadata validation
		"""
		# check ncbi-spuid uniqueness
		self.check_unique_spuid()

		# checks date
		if self.parameters['date_format_flag'].lower() != 'o':
			self.check_date()

		# check authors
		try:
			self.check_authors()
		except:
			self.global_log.append("\n\t Invalid Author Name, please list as full names separated by ;")
		
		# checks required and optional BioSample package fields 
		self.check_meta_core()

		# removes demographic data if user requested
		if self.parameters['remove_demographic_info'] is True:
			self.global_log.append(f"\n\t\t'remove_demographic_info' flag is True. Sample demographic data will be removed if present.")
			self.check_meta_case()

		# check SRA data fields
		self.check_illumina_nanopore()

		# check custom data fields
		self.check_custom_fields(self.parameters['custom_fields_file'])

		# write error file
		self.report_errors()
				
	def report_errors(self):
		with open('error.txt', "w") as f:
			# Write Global Errors
			f.write("General Errors:\n\n")
			if self.global_log:
				for line in self.global_log:
					f.write(f"\t{line}\n")
			else:
				f.write("\tPassed all global checks!\n")

			f.write("\nSample Errors:\n\n")
			valid_samples = sum(1 for s in self.sample_log if not any("ERROR" in msg for msg in self.sample_log[s]))
			f.write(f"\tNumber of Valid Samples: {valid_samples}/{len(self.metadata_df)}\n\n")

			# Write Sample Errors
			for sample in self.metadata_df["sample_name"]:
				f.write(f"\t{sample}:\n")
				if sample in self.sample_log and self.sample_log[sample]:
					for log in self.sample_log[sample]:
						f.write(f"\t\t{log.strip()}\n")
				else:
					f.write("\t\tPassed all sample checks!\n")
				f.write("\n")
		
	def normalize_author_columns(self):
		""" Normalize author/authors column to always be 'authors' 
		"""
		# Rename 'author' to 'authors' if 'authors' doesn't already exist
		if 'author' in self.metadata_df.columns and 'authors' not in self.metadata_df.columns:
			self.metadata_df.rename(columns={'author': 'authors'}, inplace=True)
		elif 'authors' in self.metadata_df.columns and 'author' in self.metadata_df.columns:
			# Merge both columns if they exist, prioritizing 'authors'
			self.metadata_df['authors'] = self.metadata_df['authors'].fillna(self.metadata_df['author'])
			self.metadata_df.drop(columns=['author'], inplace=True)
	
	def check_unique_spuid(self):
		"""Ensure all ncbi-spuid values are unique across the metadata."""
		if 'ncbi-spuid' not in self.metadata_df.columns:
			self.global_log.append("ERROR: Metadata is missing required column 'ncbi-spuid'.")
			return

		duplicates = self.metadata_df[self.metadata_df.duplicated(subset=['ncbi-spuid'], keep=False)]
		if not duplicates.empty:
			dup_values = duplicates['ncbi-spuid'].tolist()
			self.global_log.append(
				f"ERROR: Duplicate ncbi-spuid values found: {set(dup_values)}"
			)
			for _, row in duplicates.iterrows():
				sample = row['sample_name']
				spuid = row['ncbi-spuid']
				self.sample_log[sample].append(f"ERROR: Duplicate ncbi-spuid '{spuid}'")

	def check_date(self):
		""" Validates and reformats dates based on date_format_flag value
		"""
		flag = self.parameters.get("date_format_flag", "").lower()
		if flag not in {"v", "s"}:
			raise ValueError(f"Unknown date_format_flag: {flag}")

		def validate_and_format(row):
			date_str = str(row['collection_date'])
			sample = row['sample_name']

			if not date_str or date_str.strip() == "":
				self.sample_log[sample].append("ERROR: Missing collection_date.")
				return date_str

			match = re.match(r"^(\d{4})(?:[-/](\d{1,2}))?(?:[-/](\d{1,2}))?", date_str)
			if not match:
				self.sample_log[sample].append(f"ERROR: Invalid date format: '{date_str}'")
				return date_str

			year, month, day = match.groups()
			if len(year) == 2:
				self.sample_log[sample].append(f"ERROR: Year is two digits: '{year}'")
				return date_str

			month = month.zfill(2) if month else "01"
			day = day.zfill(2) if day else "01"

			return f"{year}-{month}-{day}" if flag == "v" else f"{year}-{month}"

		self.metadata_df["collection_date"] = self.metadata_df.apply(validate_and_format, axis=1)

	def check_authors(self):
		"""Checks and reformats the 'authors' column to ensure consistent First Last or F.M. Last format.
		"""
		if 'authors' not in self.metadata_df.columns:
			self.global_log.append("No 'authors' column found in metadata.")
			return
		
		def fix_name(raw_name):
			# Remove digits and leading/trailing whitespace
			cleaned = ''.join([char for char in raw_name if not char.isdigit()]).strip()

			# Remove unwanted tokens/characters
			for token in ['...', 'Name:', 'author', ',', 'dtype:', ':', 'object', '\\', '/']:
				cleaned = cleaned.replace(token, '')
			parts = cleaned.split()

			# Convert First Middle Last to F.M. Last
			if len(parts) == 3 and len(parts[0]) > 1:
				new_name = f"{parts[0][0]}.{parts[1][0]}. {parts[2]}"
				return new_name if (new_name.count('.') == 2 and len(new_name.split()) == 2) else cleaned

		# Apply to the full dataframe
		for idx, row in self.metadata_df.iterrows():
			raw = row.get('authors', '')
			if pd.isna(raw) or str(raw).strip() == '':
				continue  # Skip if authors field is empty or NaN

			raw_authors = str(raw).split(';')
			cleaned_authors = [fix_name(author.strip()) for author in raw_authors if author.strip()]
			fixed_authors_str = '; '.join(cleaned_authors)

			# Optional logging if the cleaned string differs from original
			if fixed_authors_str != row.get('authors', ''):
				sample_name = row.get('sample_name', f'Row {idx}')
				self.sample_log[sample_name].append("Author names were cleaned and reformatted.")
				self.metadata_df.at[idx, 'authors'] = fixed_authors_str

	
	def check_meta_core(self):
		"""Check and update the metadata DataFrame with required and optional fields.
		"""
		# Drop any columns containing 'test_field' 
		self.metadata_df.drop(
			columns=[c for c in self.metadata_df.columns if 'test_field' in c.lower()],
			inplace=True, errors='ignore'
		)

		missing_fields, missing_optionals = [], []

		# Ensure all required columns are present
		for field in self.required_core:
			if field in self.metadata_df.columns:
				missing_mask = self.metadata_df[field].isna() | (self.metadata_df[field].astype(str).str.strip() == "")
				if missing_mask.any():
					self.metadata_df.loc[missing_mask, field] = "Not Provided"
					for sample_name in self.metadata_df.loc[missing_mask, 'sample_name']:
						self.sample_log[sample_name].append(f"WARNING: {field} is missing for sample {sample_name}, setting to 'Not Provided'\n")
			else:
				# If column is completely missing
				missing_fields.append(field)

		# Process optional groups: at least one column in each group must exist and have non-empty values
		if self.optional_core:
			for group in self.optional_core:
				group_in_df = [field for field in group if field in self.metadata_df.columns]

				if not group_in_df:
					# Entire group is missing
					missing_optionals.append(group)
					continue

				group_values = self.metadata_df[group_in_df].astype(str).apply(lambda col: col.str.strip())
				group_missing = group_values.apply(lambda col: col == "", axis=0).all(axis=1)

				if group_missing.any():
					for field in group_in_df:
						empty_field_mask = group_values[field] == ""
						self.metadata_df.loc[empty_field_mask, field] = "Not Provided"
						for sample_name in self.metadata_df.loc[empty_field_mask, 'sample_name']:
							self.sample_log[sample_name].append(
								f"WARNING: {field} in optional group is missing for sample {sample_name}, "
								f"setting to 'Not Provided'\n")
		# Final check
		if missing_fields:
			self.global_log.append("Missing required fields: " + ", ".join(missing_fields))
		if missing_optionals:
			opt_str = ["[" + ", ".join(group) + "]" for group in missing_optionals]
			self.global_log.append("Missing optional field groups: " + ", ".join(opt_str))

		# Check lat_lon field
		if 'lat_lon' in self.metadata_df.columns:
			for _, row in self.metadata_df.iterrows():
				sample_name = row.get('sample_name', 'UNKNOWN_SAMPLE')
				latlon_val = row.get('lat_lon', '')
				if not self._valid_latlon(latlon_val):
					self.sample_log[sample_name].append(
						f"WARNING: lat_lon looks misformatted: '{latlon_val}' (expected 'lat lon')\n"
					)

	def _valid_latlon(self, s: str) -> bool:
		"""Return True if s is a valid 'latitude longitude' string in decimal degrees."""
		try:
			lat_str, lon_str = map(str.strip, s.split())
			lat = float(lat_str)
			lon = float(lon_str)

			return -90 <= lat <= 90 and -180 <= lon <= 180
		except (ValueError, AttributeError):
			return False
	
	def check_meta_case(self):
		"""Checks and removes demographics metadata for cases (sex, age, race, and ethnicity) if present.
		"""
		try:
			invalid_mask = pd.DataFrame(False, index=self.metadata_df.index, columns=self.case_fields)

			for field in self.case_fields:
				if field in self.metadata_df.columns:
					field_values = self.metadata_df[field].astype(str).str.strip()
					invalid_mask[field] = ~field_values.isin(["", "None", "Not Provided"])

			rows_with_invalid = invalid_mask.any(axis=1)

			for idx in self.metadata_df[rows_with_invalid].index:
				sample_name = self.metadata_df.at[idx, "sample_name"]
				fields_to_clean = [field for field in self.case_fields if invalid_mask.at[idx, field]]

				if fields_to_clean:
					self.sample_log[sample_name].append(
						f"Present Case Data found in: {', '.join(fields_to_clean)}. "
						f"The case data has been removed automatically."
					)
					self.metadata_df.loc[idx, fields_to_clean] = "Not Provided"
		
		except Exception as e:
			self.global_log.append(f"Unexpected error during case metadata check: {str(e)}")

	def check_illumina_nanopore(self):
		"""Validates Illumina and Nanopore metadata fields and file paths.
		"""
		# Add default 'library_name' column if missing (preserves backwards compatibility with older templates)
		for col in ['illumina_library_name', 'nanopore_library_name']:
			if col not in self.metadata_df.columns:
				self.metadata_df[col] = "Not Provided"

		# Rename internal-use-only SRA path columns to avoid submission metadata prefix
		self.metadata_df.rename(columns={
			'illumina_sra_file_path_1': 'int_illumina_sra_file_path_1',
			'illumina_sra_file_path_2': 'int_illumina_sra_file_path_2',
			'nanopore_sra_file_path_1': 'int_nanopore_sra_file_path_1',
		}, inplace=True)

		required_illumina = [
			"illumina_sequencing_instrument",
			"illumina_library_strategy",
			"illumina_library_source",
			"illumina_library_selection",
			"illumina_library_layout",
			"illumina_library_name"
		]

		required_nanopore = [
			"nanopore_sequencing_instrument",
			"nanopore_library_strategy",
			"nanopore_library_source",
			"nanopore_library_selection",
			"nanopore_library_layout",
			"nanopore_library_name"
		]

		for idx, row in self.metadata_df.iterrows():
			sample_name = row["sample_name"]
			illumina_found = bool(row.get("int_illumina_sra_file_path_1")) and bool(row.get("int_illumina_sra_file_path_2"))
			nanopore_found = bool(row.get("int_nanopore_sra_file_path_1"))

			# Illumina check
			if illumina_found:
				for field in required_illumina:
					if not row.get(field):  # missing or empty
						self.metadata_df.at[idx, field] = "Not Provided"
						self.sample_log[sample_name].append(f"INFO: Filled missing {field} with 'Not Provided'")
				
				illumina_invalid = []
				if row.get("illumina_library_layout") == "paired" and not row.get("int_illumina_sra_file_path_2"):
					illumina_invalid.append("int_illumina_sra_file_path_2 (missing for paired layout)")
				if row.get("illumina_sequencing_instrument") not in self.parameters.get("illumina_instrument_restrictions", []):
					illumina_invalid.append("illumina_sequencing_instrument (invalid or missing)")
				if illumina_invalid:
					self.sample_log[sample_name].append(
						f"ERROR: Illumina metadata is incomplete or invalid. Issues: {', '.join(set(illumina_invalid))}"
					)
			else:
				self.sample_log[sample_name].append("INFO: Illumina Not Found")

			# Nanopore check
			if nanopore_found:
				for field in required_nanopore:
					if not row.get(field):  # missing or empty
						self.metadata_df.at[idx, field] = "Not Provided"
						self.sample_log[sample_name].append(f"INFO: Filled missing {field} with 'Not Provided'")

				nanopore_invalid = []
				if row.get("nanopore_sequencing_instrument") not in self.parameters.get("nanopore_instrument_restrictions", []):
					nanopore_invalid.append("nanopore_sequencing_instrument (invalid or missing)")

				if nanopore_invalid:
					self.sample_log[sample_name].append(
						f"ERROR: Nanopore metadata is incomplete or invalid. Issues: {', '.join(set(nanopore_invalid))}"
					)
			else:
				self.sample_log[sample_name].append("INFO: Nanopore Not Found")

	def check_custom_fields(self, json_path: str):
		"""Validate and process custom fields defined in a JSON config.
		"""
		try:
			with open(json_path, 'r') as f:
				custom_fields = json.load(f)
		except (FileNotFoundError, json.JSONDecodeError) as e:
			self.global_log.append(f"[CustomFields] Error loading JSON: {e}")
			return
		
		# Remove the test_field examples
		custom_fields = {
			k: v for k, v in custom_fields.items()
			if 'test_field' not in k.lower()
		}

		static_columns = {
			"sample_name", "sequence_name", "ncbi-spuid", "ncbi-bioproject", "title", "description",
			"authors", "submitting_lab", "submitting_lab_division", "submitting_lab_address", "publication_status", "publication_title",
			"isolate", "isolation_source", "host_disease", "host", "organism", "collection_date", "country", "state",
			"collected_by", "sample_type", "lat_lon", "purpose_of_sampling", "host_sex", "host_age", "race", "ethnicity",
			"assembly_protocol", "assembly_method", "mean_coverage", "fasta_path", "gff_path", "ncbi-spuid-sra",
			"illumina_sequencing_instrument", "illumina_library_strategy", "illumina_library_source", "illumina_library_selection",
			"illumina_library_layout", "illumina_library_protocol", "illumina_library_name", "illumina_sra_file_path_1", "illumina_sra_file_path_2",
			"file_location", "fastq_path_1", "fastq_path_2", "nanopore_sequencing_instrument", "nanopore_library_strategy",
			"nanopore_library_source", "nanopore_library_selection", "nanopore_library_layout", "nanopore_library_protocol",
			"nanopore_library_name", "nanopore_sra_file_path_1", "nanopore_sra_file_path_2",
			"int_illumina_sra_file_path_1", "int_illumina_sra_file_path_2","int_nanopore_sra_file_path_1", "int_nanopore_sra_file_path_2"
		}

		existing_cols = set(self.metadata_df.columns)
		unexpected_fields = existing_cols - static_columns - set(custom_fields)


		for field, props in custom_fields.items():
			field_errors = []

			# Replace empty values
			if 'replace_empty_with' in props and field in self.metadata_df.columns:
				self.metadata_df[field].fillna(props['replace_empty_with'], inplace=True)

			# Rename field
			if 'new_field_name' in props and props['new_field_name']:
				if field in self.metadata_df.columns:
					self.metadata_df.rename(columns={field: props['new_field_name']}, inplace=True)
				else:
					field_errors.append(f"Cannot rename missing field '{field}'")

			# Extra unexpected keys
			extra_keys = set(props.keys()) - {'replace_empty_with', 'new_field_name'}
			if extra_keys:
				field_errors.append(f"Extra keys in '{field}': {', '.join(extra_keys)}")

			# Log field-specific issues
			if field_errors:
				self.global_log.append(f"[CustomFields] Issues in '{field}': {'; '.join(field_errors)}")

		if unexpected_fields:
			self.global_log.append(f"[CustomFields] Unexpected fields in metadata: {', '.join(unexpected_fields)}")

	def normalize_value(self, val):
		"""
		Normalize placeholder/empty metadata values.
		Converts Not Provided, NA, N/A, empty strings, and non-breaking spaces to None.
		"""
		if pd.isna(val):
			return None
		if isinstance(val, str):
			val = val.replace("\u00A0", " ").strip()  # normalize NBSP
			if val == "":
				return None
		return val

class HandleDfInserts:
	""" Class constructor for handling the insert operations on the metadata df once all the checks are completed
	"""
	def __init__(self, filled_df, parameters):
		self.parameters = parameters
		self.metadata_df = filled_df
		self.list_of_country = self.metadata_df["country"].tolist() if "country" in self.metadata_df.columns else []
		self.list_of_state = self.metadata_df["state"].tolist() if "state" in self.metadata_df.columns else []
		self.new_combination_list = []

	def handle_df_inserts(self):
		""" Main function to call sub-insert routines and return the final metadata dataframe
		"""
		# adds the Geolocation field
		if self.list_of_country:
			self.insert_loc_data()
		self.insert_additional_columns()
		try:
			assert 'geo_loc_name' in self.metadata_df.columns.values
			assert True not in [math.isnan(x) for x in self.metadata_df['geo_loc_name'].tolist() if isinstance(x, str) is False]
			assert 'structuredcomment' in self.metadata_df.columns.values
			assert True not in [math.isnan(x) for x in self.metadata_df['structuredcomment'].tolist() if isinstance(x, str) is False]
		except AssertionError:
			raise AssertionError(f'Columns were not properly inserted into dataframe')
		return self.metadata_df

	def insert_loc_data(self):
		""" Inserts modified location data with the country:state into dataframe
		"""
		for i in range(len(self.list_of_country)):
			if i < len(self.list_of_state) and self.list_of_state[i] not in ("", None):
				self.new_combination_list.append(f'{self.list_of_country[i]}: {self.list_of_state[i]}')
			else:
				self.new_combination_list.append(str(self.list_of_country[i]))

		self.metadata_df['geo_loc_name'] = self.new_combination_list

	def insert_additional_columns(self):
		""" Inserts additional columns into the metadata dataframe if they don't exist
		"""
		additional_columns = {
        "structuredcomment": ["Assembly-Data"] * len(self.metadata_df.index)
    	}
		for col_name, col_values in additional_columns.items():
			if col_name not in self.metadata_df.columns:
				self.metadata_df.insert(self.metadata_df.shape[1], col_name, col_values)


if __name__ == "__main__":
	metadata_validation_main()
