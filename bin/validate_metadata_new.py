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

	# call the load_meta function passing in the path to the metadata file
	meta_to_df.run_get_meta_df()
	filled_df = meta_to_df.final_df

	# handle case where we're only fetching reports
	if parameters['find_paths']:
		sample_dfs = {}
		col_name = "sequence_name" if "sequence_name" in filled_df.columns else "sample_name" # allow flexibility in col name
		for row in range(len(filled_df)):
			sample_df = filled_df.iloc[row].to_frame().transpose()
			sample_df = sample_df.set_index(col_name)
			sample_dfs[filled_df.iloc[row][col_name]] = sample_df
		missing_tsvs = []
		for sample in sample_dfs.keys():
			tsv_file = f'{parameters["path_to_existing_tsvs"]}/{parameters["file_name"]}/tsv_per_sample/{sample}.tsv'
			dest_tsv_file = f'{parameters["output_dir"]}/{parameters["file_name"]}/tsv_per_sample/{sample}.tsv'
			if os.path.exists(tsv_file):
				shutil.copy(tsv_file, dest_tsv_file) # copy to local directory
			else:
				missing_tsvs.append(tsv_file) # add to missing tsvs list if not found
		if not missing_tsvs:
			print(f'\nPaths to existing sample metadata tsvs were found!\n')
		else:
			print("\nERROR: The following expected TSV files are missing:\n", file=sys.stderr)
			for missing in missing_tsvs:
				print(f"  - {missing}", file=sys.stderr)
			sys.exit(1)		
	else:
		# if fetch_reports_only is false, we run validation steps
		validate_checks = ValidateChecks(filled_df, parameters, parameters_class)
		validate_checks.validate_main()

class ValidateChecks:
	""" Class constructor for performing a variety of checks on metadata
	"""
	def __init__(self, filled_df, parameters, get_params):
		# passed into class constructor
		self.metadata_df = filled_df
		self.parameters = parameters

		# Get the correct BioSample package
		self.biosample_package = get_params.load_config()

		# Set required and "at least one" fields dynamically
		self.required_fields_dict = get_params.load_required_fields(parameters['biosample_fields_key'])
		self.at_least_one_required_fields_dict = self.required_fields_dict.get("At_least_one_required", {})
		self.required_core = self.required_fields_dict.get(self.biosample_package, [])
		self.optional_core = self.at_least_one_required_fields_dict.get(self.biosample_package, [])
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

		# Set flags for error reporting
		self.nanopore_grades = {''}
		[self.meta_nanopore_grade, self.meta_illumina_grade, self.meta_core_grade, self.meta_case_grade,
		 self.author_valid, self.valid_date_flag] = [True] * 6
		self.repeated = False

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
				self.log_error(name, "'remove_demographic_info' flag is True. Sample demographic data will be removed if present.")
				self.metadata_df = self.check_meta_case(sample_info)
	


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
		missing_fields = [field for field in self.required_core if sample_info.get(field, [""])[0] == ""]
		missing_optionals = next((group for group in self.optional_core if not any(sample_info.get(field, [""])[0] for field in group)), [])

		if missing_fields:
			self.meta_core_grade = False
			self.log_error(sample_info["sample_name"].values[0], f"Missing Required Metadata: {', '.join(missing_fields)}")

		if missing_optionals:
			self.meta_core_grade = False
			self.log_error(sample_info["sample_name"].values[0], f"Missing 'At Least One Required' Metadata: {', '.join(missing_optionals)}")

	def check_meta_case(self, sample_info):
		"""Checks and removes demographic metadata if 'remove_demographic_info' is enabled."""
		invalid_case_data = [field for field in self.case_fields if field in sample_info.columns and sample_info[field].values[0] not in ["", None, "Not Provided"]]

		for field in invalid_case_data:
			sample_info.at[sample_info.index[0], field] = "Not Provided"  # Replace value

		if invalid_case_data:
			self.log_error(sample_info["sample_name"].values[0], f"Present Case Data found in: {', '.join(invalid_case_data)}. Case data has been removed.")

		self.metadata_df.update(sample_info)
		return self.metadata_df