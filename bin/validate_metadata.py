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
from typing import List, Dict, Union

# module level import
from annotation_utility import MainUtility as main_util


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
		# now call the main function for validating the metadata
		validate_checks = ValidateChecks(filled_df, parameters, parameters_class)
		validate_checks.validate_main()

		# insert necessary columns in metadata dataframe
		insert = HandleDfInserts(parameters=parameters, filled_df=validate_checks.metadata_df)
		insert.handle_df_inserts()

		if validate_checks.did_validation_work:
			# now split the modified and checked dataframe into individual samples
			sample_dfs = {}
			final_df = insert.filled_df
			# todo: this rename is temporary - will be added in the class/fx to handle multiple tsvs (see lines 76 & 955)
			final_df = final_df.rename(columns={'sample_name': 'sequence_name'}) # seqsender expects sequence_name
			for row in range(len(final_df)):
				sample_df = final_df.iloc[row].to_frame().transpose()
				sample_df = sample_df.set_index('sequence_name')
				sample_dfs[final_df.iloc[row]['sequence_name']] = sample_df
			# now export the .xlsx file as a .tsv 
			for sample in sample_dfs.keys():
				tsv_file = f'{parameters["output_dir"]}/{parameters["file_name"]}/tsv_per_sample/{sample}.tsv'
				sample_dfs[sample].to_csv(tsv_file, sep="\t")
				print(f'\nMetadata Validation was Successful!!!\n')
		else:
			print(f'\nMetadata Validation Failed Please Consult : {parameters["output_dir"]}/{parameters["file_name"]}/errors/full_error.txt for a Detailed List\n')
			sys.exit(1)

		# todo: handle multiple tsvs for illumina vs. nanopore

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
	
	# debug: load the dict of required BioSample params (not from Excel)
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
	""" Class constructor to get the metadata into proper df format before running checks on it
	"""
	def __init__(self, parameters):
		self.parameters = parameters

	def run_get_meta_df(self):
		""" Main for getting the full dataframe for the metadata
		"""
		self.df = self.load_meta()
		self.final_df = self.populate_fields()

	def load_meta(self):
		""" Loads the metadata file in as a dataframe from an Excel file (.xlsx)
		"""
		df = pd.read_excel(self.parameters['meta_path'], header=[1], dtype = str, engine = "openpyxl", index_col=None, na_filter=False)
		df = df.loc[:, ~df.columns.str.contains('^Unnamed')] # Remove "Unnamed" col that sometimes gets imported due to trailing commas
		# Check for duplicate columns
		duplicate_pattern = r"\.\d+$"  # Matches column names ending with .1, .2, etc.
		mangled_columns = [re.sub(duplicate_pattern, "", col) for col in df.columns if any(re.match(rf"^{re.escape(base)}{duplicate_pattern}$", col) for base in df.columns if base != col)]
		duplicate_bases = list(set(mangled_columns))
		if duplicate_bases:
			raise ValueError(f"Duplicate columns detected in the metadata due to renaming: {duplicate_bases}.\n"
					"Please check your metadata, remove duplicate columns, and try again.")
		# Check for empty dataframe
		if df.empty:
			raise ValueError("The metadata Excel sheet is empty. Please provide a valid file with data.")
		return df

	def populate_fields(self):
		""" Replacing the NaN values in certain columns with "Not Provided" or ""
		"""
		terms_2_replace = ["collected_by", "sample_type", "lat_lon", "host_age", "host_disease", "host_sex", "isolation_source", "purpose_of_sampling"]
		# Filter terms to include only those present in the dataframe
		existing_terms = [term for term in terms_2_replace if term in self.df.columns]
		# Remove any NaNs
		field_value_mapping = {term: "Not Provided" for term in existing_terms}
		replaced_df = self.df.replace(to_replace={term: ["", None] for term in existing_terms}, value=field_value_mapping)
		final_df = replaced_df.fillna("")
		# Remove any N/A or na or N/a or n/A
		unwanted_vals = ['N/A', 'NA']
		for col in existing_terms:
			final_df[col] = final_df[col].apply(
				lambda x: "Not Provided" if str(x).strip().upper() in map(str.upper, unwanted_vals) else x
			)
		# Validate populated fields
		try:
			# Ensure all values, if absent, are either empty or "Not Provided"
			for field in existing_terms:
				final_df[field] = final_df[field].apply(
					lambda x: "Not Provided" if str(x).strip().lower() == "not provided" else x)
				assert all(isinstance(value, str) for value in final_df[field].values)
		except AssertionError:
			raise AssertionError(
				f'Populating certain fields in the metadata df with "" or "Not Provided" was unsuccessful'
			)		
		return final_df

class ValidateChecks:
	""" Class constructor for performing a variety of checks on metadata
	"""
	def __init__(self, filled_df, parameters, get_params):
		# passed into class constructor
		self.metadata_df = filled_df
		self.parameters = parameters

		# error messages
		self.error_tsv = pd.DataFrame(index=self.metadata_df['sample_name'].tolist())
		[self.sample_error_msg, self.repeat_error, self.sra_msg, self.date_error_msg, self.matchup_error,
		 				self.illumina_error_msg, self.nanopore_error_msg] = [''] * 7
		# actual error files 
		self.final_error_file = open(f'{self.parameters["output_dir"]}/{self.parameters["file_name"]}/errors/full_error.txt', "w")
		self.custom_fields_error_file = open(f'{self.parameters["output_dir"]}/{self.parameters["file_name"]}/errors/custom_fields_error.txt', "w")

		# check flags
		self.nanopore_grades = {''}
		[self.meta_nanopore_grade, self.meta_illumina_grade, self.meta_core_grade, self.meta_case_grade,
		 self.author_valid, self.valid_date_flag] = [True] * 6
		self.repeated = False

		# global variables for keeping track of sample properties
		self.did_validation_work = True
		self.valid_sample_num = 0
		self.list_of_sample_errors = []
		self.list_of_sample_dfs = {}
		self.final_cols = []

		# Set required and "at least one" fields dynamically
		self.biosample_package = get_params.load_config() # get the correct BioSample package
		self.required_fields_dict = get_params.load_required_fields(parameters['biosample_fields_key'])
		self.at_least_one_required_fields_dict = self.required_fields_dict.get("At_least_one_required", {})
		self.required_core = self.required_fields_dict.get(self.biosample_package, {}).get("required", [])
		self.optional_core = self.required_fields_dict.get(self.biosample_package, {}).get("at_least_one_required", [])
		self.case_fields = ["host_sex", "host_age", "race", "ethnicity"]
		
		## instantiate CustomFieldsProcessor class
		self.custom_fields_processor = CustomFieldsProcessor(
			json_file=parameters['custom_fields_file'],
			error_file=self.custom_fields_error_file
		)

		# get the main utility class 
		self.main_util = main_util()
		
		# normalize authors column
		self.normalize_author_columns()

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
		""" Main validation function for the metadata """
		# check if user would like to validate custom fields
		metadata_samp_names = self.metadata_df['sample_name'].tolist()

		# if there are repeat samples then check them and replace the names
		if len(self.metadata_df['sample_name']) != len(set(self.metadata_df['sample_name'])):
			self.check_for_repeats_in_meta()

		# checks date
		if self.parameters['date_format_flag'].lower() != 'o':
			self.check_date()

		# Check custom fields
		if self.parameters.get('validate_custom_fields', True):
			self.metadata_df = self.custom_fields_processor.process(self.metadata_df)
			
		# lists through the entire set of samples and runs the different checks below
		for name in metadata_samp_names:
			self.sample_error_msg = f"\n\t{str(name)}:"
			sample_info = self.metadata_df.loc[self.metadata_df['sample_name'] == name]
			sample_info.columns = sample_info.columns.str.lower() # normalize cols to lowercase

			self.check_meta_core(sample_info)

			# if the author for the sample is not empty then check to make sure it is properly formatted
			try:
				assert self.author_valid is True
			except AssertionError:
				raise AssertionError(f'Author valid flag does not have the proper default value of True')
			if str(sample_info["authors"]) != "" and str(sample_info["authors"]) != '':
				try:
					fixed_authors = self.check_authors(sample_info["authors"].to_list()[0].split(';'))
					self.metadata_df.loc[self.metadata_df['sample_name'] == name, 'author'] = fixed_authors
				except:
					self.author_valid = False
					self.sample_error_msg = "\n\t Invalid Author Name, please list as full names separated by ;"

			# run the check on the PI meta information if the remove_demographic_info flag is true
			try:
				assert self.meta_case_grade is True
			except AssertionError:
				raise AssertionError(f'meta_case_grade was not reset to True')
			if self.parameters['remove_demographic_info'] is True:
				self.sample_error_msg += (f"\n\t\t'remove_demographic_info' flag is True. Sample demographic data will be removed if present.")
				self.metadata_df = self.check_meta_case(sample_info)

			# check if the SRA submission is triggered, if it is, then run the class of functions for handling sra submission
			if str(sample_info["ncbi_sequence_name_sra"]) != "" or str(sample_info["ncbi_sequence_name_sra"]) != '':
				self.sra_msg = "\n\t\tSRA Submission Detected: "
				sra_check = Check_Illumina_Nanopore_SRA (
											sample_info=sample_info, sra_msg=self.sra_msg, parameters=self.parameters,
											meta_nanopore_grade=self.meta_nanopore_grade, meta_illumina_grade=self.meta_illumina_grade,
											nanopore_error_msg=self.nanopore_error_msg, illumina_error_msg=self.illumina_error_msg,
											)
				try:
					assert sra_check
				except AssertionError:
					raise AssertionError(f'check_illumina_nanopore_sra class was not properly instantiated')
				sra_check.handle_sra_submission_check()
				self.sra_msg = sra_check.sra_msg
				self.meta_nanopore_grade = sra_check.meta_nanopore_grade
				self.nanopore_error_msg = sra_check.nanopore_error_msg
				self.meta_illumina_grade = sra_check.meta_illumina_grade
				self.illumina_error_msg = sra_check.illumina_error_msg

			# capture the error messages at the sample level
			errors_class = HandleErrors(
				grades = {'meta_case_grade': self.meta_case_grade, 'meta_illumina_grade': self.meta_illumina_grade,
						  'meta_nanopore_grade': self.meta_nanopore_grade, 'author_valid': self.author_valid,
						  'meta_core_grade': self.meta_core_grade},
				errors = {'sample_error_msg': self.sample_error_msg, 'sra_msg': self.sra_msg,
						  'illumina_error_msg': self.illumina_error_msg, 'nanopore_error_msg': self.nanopore_error_msg,
						  'list_of_sample_errors': self.list_of_sample_errors},
				valid_sample_num = self.valid_sample_num,
				sample_info = sample_info,
				sample_flag = True,
				parameters= self.parameters,
				tsv = self.error_tsv,
				valid_date_flag = self.valid_date_flag
			)

			try:
				assert errors_class
			except AssertionError:
				raise AssertionError(f'errors_class was not properly instantiated')

			# update the list of sample errors in this class
			errors_class.capture_errors_per_sample()
			self.list_of_sample_errors = errors_class.list_of_sample_errors
			self.valid_sample_num = errors_class.valid_sample_num

			# reset all checks back to true (for each sample)
			[self.meta_case_grade, self.meta_illumina_grade, self.meta_nanopore_grade,
			 self.author_valid, self.meta_core_grade] = [True] * 5
			try:
				assert False not in [grade is True for grade in [self.meta_case_grade, self.meta_illumina_grade, self.meta_nanopore_grade,
																 self.author_valid, self.meta_core_grade]]
			except AssertionError:
				raise AssertionError(f'Grades were not properly reset after sample round')

			# reset all of the error messages
			[self.sra_msg, self.illumina_error_msg, self.nanopore_error_msg] = [''] * 3
			try:
				assert False not in [error == '' for error in [self.sra_msg, self.illumina_error_msg, self.nanopore_error_msg]]
			except AssertionError:
				raise AssertionError(f'Errors were not properly reset after sample round')

		# trim the final df based on cols to keep 
		if len(self.final_cols) != 0:  # this means that there were custom fields
			# only keep this set in final dataframe 
			self.metadata_df = self.metadata_df.loc[:, self.final_cols]

		# get the final error message
		self.did_validation_work = errors_class.capture_final_error (
			final_error_file = self.final_error_file, repeat_error = self.repeat_error,
			matchup_error = self.matchup_error, valid_date_flag = self.valid_date_flag,
			date_error_msg = self.date_error_msg, valid_sample_num = self.valid_sample_num,
			metadata_df = self.metadata_df, list_of_sample_errors = self.list_of_sample_errors, repeated = self.repeated,
			did_validation_work = self.did_validation_work,
		)

	def check_for_repeats_in_meta(self):
		""" Check if the metadata files has repeat samples
		"""
		try:
			assert self.repeated is False
		except AssertionError:
			raise AssertionError(f'repeated flag does not have proper default value of False')

		# convert the samples to a list
		samp_list = self.metadata_df['sample_name'].tolist()
		original_samp_list = samp_list.copy()
		assert samp_list == original_samp_list

		# populate the unique id dictionary
		uniqueid_dict = {}
		for i in set(original_samp_list):
			uniqueid_dict[i] = 0

		# loops through each sample and checks if it occurs more than twice
		for i in range(len(samp_list)):
			if samp_list.count(samp_list[i]) > 1:
				samp_list[i] = f'{samp_list[i]}_Copy_Sample_Num_{uniqueid_dict[samp_list[i]]}'
				uniqueid_dict[original_samp_list[i]] = uniqueid_dict[original_samp_list[i]] + 1
				self.repeated = True

		# replace the sample list column with new names
		self.metadata_df['sample_name'] = samp_list
		# output the repeat error with the sample names that are repeated
		if self.repeated:
			self.repeat_error = f'\n\tRepeated Sample Names: {", ".join([x for x in uniqueid_dict.keys() if uniqueid_dict[x] > 0])}'
			# check that those samples that are repeated actually were changed
			try:
				assert len([x for x in uniqueid_dict.keys() if uniqueid_dict[x] > 0]) != 0
				skip = []
				for sample, sample2 in zip(samp_list, original_samp_list):
					if uniqueid_dict[sample2] > 0 and sample2 not in skip:
						assert '_Copy_Sample_Num_' in sample
						skip.append(sample.split('_')[0])
			except AssertionError:
				raise AssertionError(f'Repeated flag was triggered but could not find >1 recordings or name changes to samples')
		else:
			try:
				assert len([x for x in uniqueid_dict.keys() if uniqueid_dict[x] > 0]) == 0
			except AssertionError:
				raise AssertionError(f'Repeated flag not triggered despite recording multiple repeats')

	def check_date(self):
		"""
		Reformats the date based on the input flag. Accepts date formats as YYYY, YYYY-MM, YYYY-MM-DD, MMDDYYYY, MMYYYY.
		Flags dates with two-digit years (YY) as invalid.
		Outputs error details in a text file for missing or invalid dates and raises an error if the flag is not valid.
		"""
		try:
			assert self.valid_date_flag is True
		except AssertionError:
			raise AssertionError(f"Valid date flag is not properly set to the default value of True")

		dates_list = self.metadata_df["collection_date"].tolist()
		samples_list = self.metadata_df["sample_name"].tolist()
		dates_holder = {'missing_dates': [], 'invalid_dates': []}
		
		# Updated regex patterns for different formats
		date_patterns = [
			# Matches different date forms, all patterns accept '-' or '/' separator, and all have optional time
			r"^(\d{4})(?:[-/](\d{1,2}))?(?:[-/](\d{1,2}))?(?:\s(\d{2}):(\d{2}):(\d{2}))?$",  # YYYY, YYYY/MM, YYYY/MM/DD, YYYY/M, YYYY/M/DD
			r"^(\d{1,2})(?:[-/](\d{1,2}))?(?:[-/](\d{4}))?(?:\s(\d{2}):(\d{2}):(\d{2}))?$",  # M/D/YYYY, MM/DD/YYYY
			r"^(\d{1,2})(?:[-/](\d{4}))?(?:\s(\d{2}):(\d{2}):(\d{2}))?$",                  # M/YYYY, MM/YYYY
			r"^(\d{1,2})(?:[-/](\d{1,2}))[-/](\d{2})(?:\s(\d{2}):(\d{2}):(\d{2}))?$"      # M/D/YY, MM/DD/YY
		]

		print(f"flag: {self.parameters['date_format_flag']}")
		for i, date_value in enumerate(dates_list):
			sample_name = samples_list[i]

			# Handle missing or empty dates
			if not date_value:
				dates_holder['missing_dates'].append(sample_name)
				self.valid_date_flag = False
				continue

			try:
				date_value_str = str(date_value)

				# Try matching against each pattern
				match = None
				for pattern in date_patterns:
					match = re.match(pattern, date_value_str)
					if match:
						break

				if match:
					# Extract date components
					year, month, day, *_ = match.groups()
					if not month:
						month = "00"
					if not day:
						day = "00"

					# Check if the year is only two digits
					if len(year) == 2:
						raise ValueError("Two-digit year detected. Use a four-digit year for clarity.")

					# Normalize month and day to two digits
					month = month.zfill(2)
					day = day.zfill(2)

					# Handle 'v' flag for YYYY-MM-DD format
					if self.parameters['date_format_flag'].lower() == 'v':
						# Ensure date is in YYYY-MM-DD format
						dates_list[i] = f"{year}-{month}-{day}"

					# Handle 's' flag for YYYY-MM format
					elif self.parameters['date_format_flag'].lower() == 's':
						# Ensure date is in YYYY-MM format
						dates_list[i] = f"{year}-{month}"

					else:
						print(f"3: {self.valid_date_flag}")
						raise ValueError(f"Unknown date_format_flag {self.parameters['date_format_flag']}")
				else:
					print(f"4: {self.valid_date_flag}")
					raise ValueError(f"Invalid date format {date_value_str}")

			except Exception as e:
				dates_holder['invalid_dates'].append(sample_name)
				self.valid_date_flag = False
				print(f"5: {self.valid_date_flag}")

		# Handle output or logging for missing and invalid dates
		with open("date_errors.txt", "w") as error_file:
			if dates_holder['missing_dates']:
				error_file.write(f"Missing dates for samples: {dates_holder['missing_dates']}\n")
			if dates_holder['invalid_dates']:
				error_file.write(f"Invalid dates for samples: {dates_holder['invalid_dates']}\n")

		if not self.valid_date_flag:
			print(f"6: {self.valid_date_flag}")
			raise ValueError("Date validation failed. Check 'date_errors.txt' for details.")

		# Update the dataframe with formatted dates
		self.metadata_df["collection_date"] = dates_list

	@staticmethod
	def check_authors(authors):
		""" Checks to make sure Author is in First Last or F.M. Last name format
		"""
		fixed_authors = []
		for i in range(len(authors)):
			# clean the name up a little bit
			remove_nums_spaces = (''.join([i for i in authors[i] if not i.isdigit()])).strip()
			remove_weird_chars = remove_nums_spaces.replace('...', '').replace('Name:', '').replace('author', '').replace(
				',', '').replace('dtype:', '').replace(':', '').replace('object', '').replace('\\', '').replace('/', '')

			# if the full name has a length of three
			if len(remove_weird_chars.split()) == 3 and len(remove_weird_chars.split()[0]) > 1:
				# change to F.M. Last Name
				new_name = f'{(remove_weird_chars.split()[0])[0]}.{remove_weird_chars.split()[1]} {remove_weird_chars.split()[-1]}'
				try:
					assert len(new_name.split(' ')) == 2
					assert new_name.count('.') == 2
				except AssertionError:
					raise AssertionError(f'Name was not properly converted from First Middle Last to F.M. Last')
			else:
				new_name = remove_weird_chars
			fixed_authors.append(new_name)
		try:
			assert len(fixed_authors) == len(authors)
		except AssertionError:
			raise AssertionError(f'# of fixed authors does not match the original number of authors')
		return '; '.join(fixed_authors)

	def check_meta_core(self, sample_line):
		""" Checks that the necessary metadata is present for the sample line
		"""
		try:
			assert self.meta_core_grade is True
		except AssertionError:
			raise AssertionError(f'Meta core grade was not properly reset to True after sample round')

		missing_fields, missing_optionals = [], []
		# check the required fields
		for field in self.required_core:
			if field in sample_line:
				if str(sample_line[field].values[0]) == "" or str(sample_line[field].values[0]) == '':
					missing_fields.append(field)
					self.meta_core_grade = False
			else:
				missing_fields.append(field)  # Treat missing columns as missing fields
				self.meta_core_grade = False

		# check the optional fields
		if self.optional_core:
			for group in self.optional_core:
				if not any(str(sample_line[field].values[0]).strip() for field in group if field in sample_line):
					self.meta_core_grade = False  # Validation fails if no values exist in this group
					missing_optionals.append(group)
					break  # No need to check further if one group fails

		if self.meta_core_grade is False:
			try:
				assert len(missing_fields) != 0
			except AssertionError:
				raise AssertionError(f'Meta core grade is false but did not record any missing fields')
			self.sample_error_msg += "\n\t\tMissing Required Metadata:  " + ", ".join(missing_fields)
			if len(missing_optionals) != 0:
				self.sample_error_msg += "\n\t\tMissing 'At Least One Required' Metadata:  " + ", ".join(missing_optionals)
	
	def check_meta_case(self, sample_info):
		""" Checks and removes demographics metadata for cases (sex, age, race, and ethnicity) if present. """
		try:
			assert self.meta_case_grade is True
		except AssertionError:
			raise AssertionError(f'Meta case grade was not properly reset back to True after sample round')
		invalid_case_data = []
		try:
			for field in self.case_fields:
				if field in sample_info.columns and str(sample_info[field].values[0]) not in ["", None, "Not Provided"]:
					invalid_case_data.append(field)
					# Remove the case data from the dataframe
					sample_info.at[sample_info.index[0], field] = "Not Provided"  # Replace value with Not Provided string
		except:
			self.meta_case_grade = False
		# Develop error message if case data was found and removed
		if invalid_case_data:
			self.sample_error_msg += (
				f'\n\t\tPresent Case Data found in: {", ".join(invalid_case_data)}.'
				f'\n\t\tThe case data has been removed automatically.'
			)
		self.metadata_df.update(sample_info)
		return self.metadata_df

class Check_Illumina_Nanopore_SRA:
	""" Class constructor for the various checks on instruments
	"""
	def __init__(self, sample_info, sra_msg, parameters, meta_nanopore_grade, meta_illumina_grade, nanopore_error_msg, illumina_error_msg):
		self.sample_info = sample_info
		self.sra_msg = sra_msg
		self.parameters = parameters
		self.required_illumina = ["illumina_sequencing_instrument", "illumina_library_strategy", "illumina_library_source",
					 "illumina_library_selection", "illumina_library_layout"]
		self.required_nanopore = ["nanopore_sequencing_instrument", "nanopore_library_strategy", "nanopore_library_source",
					   "nanopore_library_selection", "nanopore_library_layout"]
		self.meta_nanopore_grade = meta_nanopore_grade
		self.meta_illumina_grade = meta_illumina_grade
		self.nanopore_error_msg = nanopore_error_msg
		self.illumina_error_msg = illumina_error_msg

	def handle_sra_submission_check(self):
		""" Main function for the instrument checks
		"""
		# initialize a few file path values
		illum_file_path1 = self.sample_info["illumina_sra_file_path_1"].tolist()[0]
		illum_file_path2 = self.sample_info["illumina_sra_file_path_2"].tolist()[0]
		nano_file_path1 = self.sample_info["nanopore_sra_file_path_1"].tolist()[0]

		# check if the illumina file path for illumina is not empty
		if illum_file_path1 and illum_file_path2 and illum_file_path1 != "" and illum_file_path1 != "" and illum_file_path2 != "" and illum_file_path2 != '':
			self.check_instruments(instrument_type='illumina')
			self.sra_msg += " Illumina Found\t"
		else:
			self.sra_msg += " Illumina Not Found\t"

		# check if the nanopore file path for nanopore is not empty
		if nano_file_path1 and nano_file_path1 != "" and nano_file_path1 != '':
			self.check_instruments(instrument_type='nanopore')
			self.sra_msg += " Nanopore Found"
		else:
			self.sra_msg += " Nanopore Not found"

	def check_instruments(self, instrument_type):
		""" General function for checking properties of the illumina and nanopore instrument
		"""
		if instrument_type == 'nanopore':
			try:
				assert self.meta_nanopore_grade is True
			except AssertionError:
				raise AssertionError(f'Meta nanopore grade was not properly reset to default value of True')

			required = self.required_nanopore
			instrument = self.sample_info['nanopore_sequencing_instrument'].tolist()[0]
			file_path = self.sample_info['nanopore_sra_file_path_1'].tolist()[0]
			restricted_terms = self.parameters['nanopore_instrument_restrictions']

		elif instrument_type == 'illumina':
			try:
				assert self.meta_illumina_grade is True
			except AssertionError:
				raise AssertionError(f'Meta illumina grade was not properly reset to default value of True')
			if str(self.sample_info["illumina_library_layout"]) == "paired":
				self.required_illumina.append("illumina_sra_file_path_2")

			required = self.required_illumina
			instrument = self.sample_info['illumina_sequencing_instrument'].tolist()[0]
			file_path1 = self.sample_info["illumina_sra_file_path_1"].tolist()[0]
			file_path2 = self.sample_info["illumina_sra_file_path_2"].tolist()[0]
			restricted_terms = self.parameters['illumina_instrument_restrictions']

		missing_data, invalid_data = [], []
		# check if required fields are populated
		for field in required:
			if field not in self.sample_info.keys().tolist():
				missing_data.append(field)
				if instrument_type == 'nanopore':
					self.meta_nanopore_grade = False
				elif instrument_type == 'illumina':
					self.meta_illumina_grade = False

		# check if instrument is in the restricted fields
		if instrument not in restricted_terms: 
			invalid_data.append(instrument)
			if instrument_type == 'nanopore':
				self.meta_nanopore_grade = False
			elif instrument_type == 'illumina':
				self.meta_illumina_grade = False

		# check if the SRA file exists for the first file path
		path_failed = False
		if instrument_type == 'illumina':
			if self.sample_info["illumina_library_layout"].tolist()[0] == 'paired':
				paths = [file_path1, file_path2]
			else:
				paths = [file_path1]
			for path in paths:
				if not (os.path.isfile(path)):
					self.illumina_error_msg += f'\n\t\t{path} does not exist or there are permission problems'
					path_failed = True
					self.meta_illumina_grade = False
		elif instrument_type == 'nanopore':
			if not (os.path.isfile(file_path)):
				self.nanopore_error_msg += f'\n\t\t{file_path} does not exist or there are permission problems'
				path_failed = True
				self.meta_nanopore_grade = False

		if instrument_type == 'nanopore' and self.meta_nanopore_grade is False:
			try:
				assert True in [len(missing_data) != 0, len(invalid_data) != 0, path_failed]
			except AssertionError:
				raise AssertionError(f'Meta nanopore grade set to false eventhough missing or invalid data was not recorded and instrument paths exist')
			if len(missing_data) != 0:
				self.illumina_error_msg += f'\n\t\tNanopore Missing Data: {", ".join(missing_data)}'
			if len(invalid_data) != 0:
				self.illumina_error_msg += f'\n\t\tNanopore Invalid Data: {", ".join(invalid_data)}'
		elif instrument_type == 'illumina' and self.meta_illumina_grade is False:
			try:
				assert True in [len(missing_data) != 0, len(invalid_data) != 0, path_failed]
			except AssertionError:
				raise AssertionError(f'Meta illumina grade set to false eventhough missing or invalid data was not recorded and instrument paths exist')
			if len(missing_data) != 0:
				self.illumina_error_msg += f'\n\t\tIllumina Missing Data: {", ".join(missing_data)}'
			if len(invalid_data) != 0:
				self.illumina_error_msg += f'\n\t\tIllumina Invalid Data: {", ".join(invalid_data)}'

class HandleErrors:
	""" Class constructor for handling errors at the sample and global levels
	"""
	def __init__(self, grades, errors, valid_sample_num, sample_info, sample_flag, parameters, tsv, valid_date_flag):
		# get the grades from the dictionary that is passed in
		self.meta_case_grade = grades['meta_case_grade']
		self.meta_illumina_grade = grades['meta_illumina_grade']
		self.meta_nanopore_grade = grades['meta_nanopore_grade']
		self.author_valid = grades['author_valid']
		self.meta_core_grade = grades['meta_core_grade']
		# get the errors from dictionary that is passed in
		self.sample_error_msg = errors['sample_error_msg']
		self.sra_msg = errors['sra_msg']
		self.illumina_error_msg = errors['illumina_error_msg']
		self.nanopore_error_msg = errors['nanopore_error_msg']
		self.list_of_sample_errors = errors['list_of_sample_errors']
		# get the other necessary values
		self.valid_sample_num = valid_sample_num
		self.sample_info = sample_info
		# sample_flag
		self.valid_date_flag = valid_date_flag
		self.sample_flag = sample_flag
		# parameters
		self.parameters = parameters
		# tsv file 
		self.tsv = tsv

	def capture_errors_main(self):
		""" Main function for calling error sub functions
		"""
		if self.sample_flag is True:
			self.capture_errors_per_sample()

	def capture_errors_per_sample(self):
		""" Handles the errors at the sample level
		"""
		# getting flags to check for whether sample passed
		sample_passed = True
		# check whether instruments passed
		if str(self.sample_info["ncbi_sequence_name_sra"]) != "" or str(self.sample_info["ncbi_sequence_name_sra"]) != '':
			self.sample_error_msg += self.sra_msg
		# add errors in front of sample 
		self.sample_error_msg += f"\n\t\tErrors:"
		if self.meta_illumina_grade is True and self.meta_nanopore_grade is True:
			self.sample_error_msg += f"\n\t\t\tPassed all sample checks!"
		else:
			if self.meta_illumina_grade is False:
				self.sample_error_msg += self.illumina_error_msg
				sample_passed = False
			if self.meta_nanopore_grade is False:
				self.sample_error_msg += self.nanopore_error_msg
				sample_passed = False
		# check the core metadata validation
		if self.meta_core_grade is False:
			self.sample_error_msg += f"\n\t\t\tCore metadata validation failed!"
			sample_passed = False
		# check the personal information
		if self.meta_case_grade is False:
			sample_passed = False
		# check the author
		if self.author_valid is False:
			sample_passed = False

		if sample_passed:
			self.valid_sample_num += 1

		self.list_of_sample_errors.append(self.sample_error_msg)
		self.write_tsv_file(sample_passed)

	def capture_final_error(self, final_error_file, repeat_error, matchup_error,
							valid_date_flag, date_error_msg, valid_sample_num, metadata_df,
							list_of_sample_errors, repeated, did_validation_work):
		""" Handles the final error message
		"""

		# output the final error message after looping through the samples
		final_error = ''

		# write the final error for repeats
		if repeated:
			did_validation_work = False
			final_error += repeat_error

		# write the date error message to file
		if valid_date_flag is False:
			did_validation_work = False
			final_error += f"{date_error_msg}\n"

		# Check if any sample validation failed
		if valid_sample_num < len(metadata_df["sample_name"]):
			did_validation_work = False

		final_error_file.write("General Errors:\n\n")
		if final_error != '':
			final_error_file.write(final_error)
		else:
			final_error_file.write("\tPassed all global checks!")

		# write the final number of valid samples
		final_error_file.write(f'\n\nSample Errors:\n')
		final_error_file.write(f'\n\tNumber of Valid Samples: {str(valid_sample_num)}/{str(len(metadata_df["sample_name"]))}\n')
		for sample in list_of_sample_errors: 
			final_error_file.write(f'{sample}\n')
		
		# output the tsv file  
		self.tsv.to_csv(f'{self.parameters["output_dir"]}/{self.parameters["file_name"]}/errors/checks.tsv', sep="\t")

		return did_validation_work
	
	def write_tsv_file(self, sample_passed):
		if sample_passed is True:
			self.tsv['passed'] = 'Yes'
		elif sample_passed is False:
			self.tsv['passed'] = 'No'
		for x, y in zip(
			['nanopore', 'illumina', 'core', 'case', 'authors', 'dates'],
			[self.meta_nanopore_grade, self.meta_illumina_grade, self.meta_core_grade, self.meta_case_grade, self.author_valid, self.valid_date_flag]
		):
			if y is True:
				self.tsv[x] = u'\u2713'
			elif y is False:
				self.tsv[x] = 'X'

class HandleDfInserts:
	""" Class constructor for handling the insert operations on the metadata df once all the checks are completed
	"""
	def __init__(self, parameters, filled_df):
		self.parameters = parameters
		self.filled_df = filled_df
		self.list_of_country = self.filled_df["country"].tolist()
		self.list_of_state = self.filled_df["state"].tolist()
		self.new_combination_list = []

	def handle_df_inserts(self):
		""" Main function to call sub-insert routines and return the final metadata dataframe
		"""
		# adds the Geolocation field
		self.insert_loc_data()
		self.insert_additional_columns()
		self.change_illumina_paths()
		try:
			assert 'geo_loc_name' in self.filled_df.columns.values
			assert True not in [math.isnan(x) for x in self.filled_df['geo_loc_name'].tolist() if isinstance(x, str) is False]
			assert 'structuredcomment' in self.filled_df.columns.values
			assert True not in [math.isnan(x) for x in self.filled_df['structuredcomment'].tolist() if
								isinstance(x, str) is False]
		except AssertionError:
			raise AssertionError(f'Columns were not properly inserted into dataframe')

	def insert_loc_data(self):
		""" Inserts modified location data with the country:state into dataframe
		"""
		for i in range(len(self.list_of_country)):
			if self.list_of_state[i] != "" and self.list_of_state[i] != '' and self.list_of_state[i] is not None:
				self.new_combination_list.append(f'{self.list_of_country[i]}: {self.list_of_state[i]}')
			else:
				self.new_combination_list.append(str(self.list_of_country[i]))

		self.filled_df['geo_loc_name'] = self.new_combination_list

	def insert_additional_columns(self):
		""" Inserts additional columns into the metadata dataframe
		"""
		# todo: this fx does not include req'd cols for GISAID (see seqsender main config and submission_process.py script)
		self.filled_df.insert(self.filled_df.shape[1], "structuredcomment", ["Assembly-Data"] * len(self.filled_df.index))

	# todo: this is a temporary fx to convert the illumina paths as input to seqsender & tostadas.nf
	def change_illumina_paths(self):
		""" Create sra-file_name from illumina_sra_file_path_1 & illumina_sra_file_path_2 
			Rename illumina_sra_file_path_1 & illumina_sra_file_path_2 to fastq_path_1 & fastq_path_2
		"""
		# function to extract file name from path
		def extract_filename(path):
			if '/' in path:
				return path.split('/')[-1] # todo: assume Unix paths ok?
			else:
				return path
		# todo: this and fx above may be no longer needed (create new column 'sra-file_name')
		#self.filled_df['sra-file_name'] = self.filled_df.apply(lambda row: extract_filename(row['illumina_sra_file_path_1']) + ',' + extract_filename(row['illumina_sra_file_path_2']), axis=1)
		# rename original columns
		self.filled_df = self.filled_df.rename(columns={'illumina_sra_file_path_1': 'fastq_path_1', 'illumina_sra_file_path_2': 'fastq_path_2'})
	# todo: handle multiple tsvs for illumina vs. nanopore - another class?

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
