#!/usr/bin/env python3

# Adapted from Perl scripts by MH Seabolt and Python scripts by J Heuser
# Refactored and updated by AK Gupta and KA O'Connell

# necessary packages
import os
import pandas as pd
import warnings
import tempfile
import time
import re
import argparse
import sys
import math
import stat
import glob
import json
import shutil

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
	try:
		assert len([x for x in parameters.keys() if x in ['fasta_path', 'meta_path', 'output_dir', 'condaEnv', 'keep_personal_info',
														'date_format_flag', 'file_name', 'restricted_terms',
														'illumina_instrument_restrictions', 'nanopore_instrument_restrictions',
														'fasta_names', 'overwrite_output_files', 
														'custom_fields_file', 'validate_custom_fields']]) == len(parameters.keys())
	except AssertionError:
		raise AssertionError(f'Expected keys in parameters dictionary are absent:')
	for param in parameters.keys():
		try:
			assert parameters[param] != '' or parameters[param] != "" or parameters[param] is not None
		except AssertionError:
			raise AssertionError(f'One or more parameters are empty')

	# call the constructor class for converting meta to df
	meta_to_df = GetMetaAsDf(parameters)

	# call the load_meta function passing in the path to the metadata file
	meta_to_df.run_get_meta_df()
	filled_df = meta_to_df.final_df

	# now call the main function for validating the metadata
	validate_checks = ValidateChecks(filled_df, parameters)
	validate_checks.validate_main()

	# insert necessary columns in metadata dataframe
	insert = HandleDfInserts(parameters=parameters, filled_df=validate_checks.metadata_df)
	insert.handle_df_inserts()

	# change necessary columns to match what seqsender expects
	insert.handle_df_changes()

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
		parser.add_argument("-k", "--keep_personal_info", action="store_true", default=False,
							help="Flag to keep personal identifying info if provided otherwise it will return an " +
								 "error if personal information is provided.")
		parser.add_argument("-d", "--date_format_flag", type=str, default="s", choices=['s', 'o', 'v'],
							help="Flag to differ date output, s = default (YYYY-MM), " +
								 "o = original(this skips date validation), v = verbose(YYYY-MM-DD)")
		parser.add_argument("--custom_fields_file", type=str, help="File containing custom fields, datatypes, and which samples to check")
		parser.add_argument("--validate_custom_fields", type=bool, help="Flag for whether or not validate custom fields ")
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
		return df

	def populate_fields(self):
		""" Replacing the NaN values in certain columns with "Not Provided" or ""
		"""
		terms_2_replace = ["collected_by", "sample_type", "lat_lon", "purpose_of_sampling"]
		# remove any nans
		field_value_mapping = {term: "Not Provided" for term in terms_2_replace}
		replaced_df = self.df.fillna(value=field_value_mapping)
		final_df = replaced_df.fillna("")
		# remove any N/A or na or N/a or n/A
		for col in terms_2_replace:
			for unwanted_val in ['N/A', 'N/a', 'na', 'n/A']:
				for x in range(len(final_df[col].tolist())):
					if final_df[col].tolist()[x] == unwanted_val:
						final_df[col][x] = 'Not Provided'
		try:
			assert True not in [final_df[field].isnull().values.any() for field in terms_2_replace]
			for field in terms_2_replace:
				assert [value == "" or value == "Not Provided" for value in final_df[field].values]
		except AssertionError:
			raise AssertionError(f'Populating certain fields in the metadata df with "" or "Not Provided" was unsuccessful')
		return final_df


class ValidateChecks:
	""" Class constructor for performing a variety of checks on metadata
	"""
	def __init__(self, filled_df, parameters):
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
		self.case_data_detected = False
		self.valid_sample_num = 0
		self.list_of_sample_errors = []
		self.list_of_sample_dfs = {}
		self.final_cols = []

		# field requirements
		self.required_core = ["sample_name", "ncbi-spuid", "author", "isolate", "organism",
							  "collection_date", "country"]
		self.optional_core = ["collected_by", "sample_type", "lat_lon", "purpose_of_sampling"]
		self.case_fields = ["sex", "age", "race", "ethnicity"]
		
		# instantiate CustomFields class
		self.custom_fields_funcs = CustomFieldsFuncs(
			parameters=parameters
		)
		self.custom_fields_checks = CustomFieldsChecks(
			parameters=parameters,
			custom_fields_dict=self.custom_fields_funcs.custom_fields_dict, 
			error_file=self.custom_fields_error_file
		)

		# get the main utility class 
		self.main_util = main_util()
		
	def validate_main(self):
		""" Main validation function for the metadata
		"""

		# check if user would like to validate custom fields
		metadata_samp_names = self.metadata_df['sample_name'].tolist()
		if self.parameters['validate_custom_fields'] is True:

			# read the JSON file in 
			self.custom_fields_funcs.read_custom_fields_file()

			# check the JSON file passed in to make sure valid values were given
			self.custom_fields_checks.clean_lists(
				samp_names=metadata_samp_names
			)

		# if there are repeat samples then check them and replace the names
		if len(self.metadata_df['sample_name']) != len(set(self.metadata_df['sample_name'])):
			self.check_for_repeats_in_meta()

		# checks date
		if self.parameters['date_format_flag'].lower() != 'o':
			self.check_date()

		# lists through the entire set of samples and runs the different checks below
		for name in metadata_samp_names:
			self.sample_error_msg = f"\n\t{str(name)}:"
			sample_info = self.metadata_df.loc[self.metadata_df['sample_name'] == name]

			# first check the custom fields
			if self.parameters['validate_custom_fields'] is True and self.custom_fields_checks.proceed_with_custom_checks is True:
				sample_info, cols_renamed = self.custom_fields_funcs.validate_custom_fields(
					sample_info=sample_info.to_dict(),
					error_file=self.custom_fields_checks.error_file
				)
				# set new sample info to the metadata df 
				index = self.metadata_df[self.metadata_df['sample_name'] == sample_info['sample_name'].values[0]].index
				# get columns not in self.metadata_df to add
				columns_to_add = [col for col in sample_info.columns if col not in self.metadata_df.columns]
				# Add new columns to the DataFrame
				self.metadata_df = pd.concat([self.metadata_df, pd.DataFrame(columns=columns_to_add)], axis=1)
				# track the final list of columns by removing the renamed column 
				if len(cols_renamed.keys()) != 0:
					# get new column set
					self.final_cols = [x for x in self.metadata_df.columns if x not in cols_renamed.keys()]
				# add the sample information
				self.metadata_df.loc[index] = sample_info.values[0]

			# check the meta code for the sample line
			self.check_meta_core(sample_info)

			# if the author for the sample is not empty then check to make sure it is properly formatted
			try:
				assert self.author_valid is True
			except AssertionError:
				raise AssertionError(f'Author valid flag does not have the proper default value of True')
			if str(sample_info["author"]) != "" and str(sample_info["author"]) != '':
				try:
					fixed_authors = self.check_authors(sample_info["author"].to_list()[0].split(';'))
					self.metadata_df.loc[self.metadata_df['sample_name'] == name, 'author'] = fixed_authors
				except:
					self.author_valid = False
					self.sample_error_msg = "\n\t Invalid Author Name, please list as full names seperated by ;"

			# run the check on the PI meta information is the keep_personal_info flag is true
			try:
				assert self.case_data_detected is False
				assert self.meta_case_grade is True
			except AssertionError:
				raise AssertionError(f'Either case_data_detected is not False or meta_case_grade is not True default values')
			if self.parameters['keep_personal_info'] is True:
				self.check_meta_case(sample_info)
			if self.meta_case_grade is False:
				# just for tracking globally that there was an irregularity with empty personal information
				self.case_data_detected = True

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
					      'list_of_sample_errors': self.list_of_sample_errors,},
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
			date_error_msg = self.date_error_msg, case_data_detected = self.case_data_detected, valid_sample_num = self.valid_sample_num,
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
		Reformats the date ... expects YYYY or YYYY-MM-DD or YYYY-MM... if dates are empty then outputs error in txt file.
		Otherwise it throws and assertion error and stops the program to tell user to check date formats and input flag
		"""
		try:
			assert self.valid_date_flag is True
		except AssertionError:
			raise AssertionError(f'Valid date flag is not proper default value of True')

		dates_list = self.metadata_df["collection_date"].tolist()
		samples_list = self.metadata_df["sample_name"].tolist()
		dates_holder = {'missing_dates': [], 'invalid_dates': []}

		# based on input flag reformats the date
		for i in range(len(dates_list)):
			if dates_list[i] == "" or dates_list[i] == '' or dates_list[i] == None or dates_list[i] == []:
				dates_holder['missing_dates'].append(samples_list[i])
				self.valid_date_flag = False

			# checks if the date is in y-m format and converts to y-m-d format (puts 00 at end?)
			elif self.parameters['date_format_flag'].lower() == 'v' and str(dates_list[i]).count('-') == 1:
				try:
					dates_list[i] = f'{dates_list[i]}-00'
				except:
					dates_holder['invalid_dates'].append(samples_list[i])
					self.valid_date_flag = False

			# checks if the date is in y-m-d format and needs to be converted to y-m format (without day)
			elif self.parameters['date_format_flag'].lower() == 's' and str(dates_list[i]).count('-') == 2:
				try:
					dates_list[i] = '-'.join(dates_list[i].split('-')[:1])
				except:
					dates_holder['invalid_dates'].append(samples_list[i])
					self.valid_date_flag = False

			elif str(dates_list[i]).count('-') == 0:
				if self.parameters['date_format_flag'].lower() == 's':
					try:
						dates_list[i] = f'{dates_list[i]}-00'
					except:
						dates_holder['invalid_dates'].append(samples_list[i])
						self.valid_date_flag = False
				elif self.parameters['date_format_flag'].lower() == 'v':
					try:
						dates_list[i] = f'{dates_list[i]}-00-00'
					except:
						dates_holder['invalid_dates'].append(samples_list[i])
						self.valid_date_flag = False

		# output error messages collected
		if self.valid_date_flag is False:
			try:
				assert True in [len(dates_holder['missing_dates']) != 0, len(dates_holder['invalid_dates']) != 0]
			except AssertionError:
				raise AssertionError(f'Valid date flag was set as false, but recorded missing or invalid dates was empty')
			self.date_error_msg = f'\nDate Errors:\n'
			if dates_holder['missing_dates']:
				try:
					assert len(dates_holder['missing_dates']) != 0
				except AssertionError:
					raise AssertionError(f'Recorded missing dates as empty but still passed conditional')
				self.date_error_msg += f'Missing Dates: {", ".join(dates_holder["missing_dates"])}. '
			if dates_holder['invalid_dates']:
				raise ValueError(f'Unable to convert date format according to passed in {self.parameters["date_format_flag"]} '
								 f'value for date_format_flag. Please confirm date is in right format and this flag was intended')

		# place the modified date list into the dataframe
		self.metadata_df['collection_date'] = dates_list

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
			if str(sample_line[field].values[0]) == "" or str(sample_line[field].values[0]) == '':
				missing_fields.append(field)
				self.meta_core_grade = False

		# check the optional fields
		for field in self.optional_core:
			if str(sample_line[field].values[0]) == "" or str(sample_line[field].values[0]) == '':
				missing_optionals.append(field)

		if self.meta_core_grade is False:
			try:
				assert len(missing_fields) != 0
			except AssertionError:
				raise AssertionError(f'Meta core grade is false but did not record any missing fields')
			self.sample_error_msg += "\n\t\tMissing Required Metadata:  " + ", ".join(missing_fields)
			if len(missing_optionals) != 0:
				self.sample_error_msg += "\n\t\tMissing Optional Metadata:  " + ", ".join(missing_optionals)

	def check_meta_case(self, sample_info):
		""" Checks the case data for metadata (sex, age, race, and ethnicity) is not empty
		"""
		try:
			assert self.meta_case_grade is True
		except AssertionError:
			raise AssertionError(f'Meta case grade was not properly reset back to True after sample round')

		invalid_case_data = []
		for field in self.case_fields:
			if str(sample_info[field]) != "" and str(sample_info[field]) != '':
				invalid_case_data.append(field)
				self.meta_case_grade = False
		# develop the following error message if the field is empty
		if self.meta_case_grade is False:
			self.sample_error_msg += f'\n\t\tPresent Case Data found in: {", ".join(invalid_case_data)}' + \
					f"\n\t\tValidation will Fail. Please remove Case Data or add the Keep Data Flag -f to Conserve Case Data"

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
							valid_date_flag, date_error_msg, case_data_detected, valid_sample_num, metadata_df,
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

		# write the case data error message
		if case_data_detected is True:
			did_validation_work = False
			final_error += f'Keep Personal Info Flag is True But Case Data is Empty!'

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
		# adds any additional columns (seqsender required cols that are not in our metadata file)
		self.insert_additional_columns()
		try:
			assert 'bs-geo_location' in self.filled_df.columns.values
			assert True not in [math.isnan(x) for x in self.filled_df['bs-geo_location'].tolist() if isinstance(x, str) is False]
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

		self.filled_df['bs-geo_location'] = self.new_combination_list

	def insert_additional_columns(self):
		""" Inserts additional columns into the metadata dataframe
		"""
		# todo: this fx does not include req'd cols for GISAID (see seqsender main config and submission_process.py script)
		self.filled_df.insert(self.filled_df.shape[1], "structuredcomment", ["Assembly-Data"] * len(self.filled_df.index))
		self.filled_df.insert(self.filled_df.shape[1], "src-serotype", ["Not Provided"] * len(self.filled_df.index))
		self.filled_df.insert(self.filled_df.shape[1], "sra-library_name", ["Not Provided"] * len(self.filled_df.index))
		self.filled_df.insert(self.filled_df.shape[1], "bs-geo_loc_name", ["Not Provided"] * len(self.filled_df.index))
		# todo: default to Pathogen.cl.1.0 biosample package, might change this later
		self.filled_df.insert(self.filled_df.shape[1], "bs-package", ["Pathogen.cl.1.0"] * len(self.filled_df.index))
		# todo: these two cmt- fields have different values if organism== flu or cov
		self.filled_df.insert(self.filled_df.shape[1], "cmt-StructuredCommentPrefix", ["Assembly-Data"] * len(self.filled_df.index))
		self.filled_df.insert(self.filled_df.shape[1], "cmt-StructuredCommentSuffix", ["Assembly-Data"] * len(self.filled_df.index))

	def handle_df_changes(self):
		""" Main function to call change routines and return the final metadata dataframe
		"""
		self.change_col_names()
		self.change_illumina_paths()

		# list of column names to check
		columns_to_check = ['authors', 'bs-collected_by', 'src-country', 'bs-isolate', 'bs-host', 'bs-host_disease',
					  		'bs-lat_lon', 'bs-host_sex', 'bs-host_age', 'cmt-Assembly-Method', 'cmt-Coverage', 
							'src-isolate', 'src-host', 'cmt-HOST_AGE', 'cmt-HOST_GENDER']
		for column_name in columns_to_check:
			try:
				self.check_nan_for_column(column_name)
			except AssertionError:
				raise AssertionError(f'Columns in dataframe were not properly changed for input to seqsender')

	def change_col_names(self):
		""" Change identical column names to match the name seqsender expects
			Copy duplicate columns as seqsender expects
		"""
		# todo: only illumina is supported now (by changing colnames) - need to change illumina_ fields to properly support both nanopore and illumina
		self.filled_df.rename(columns={
									   'author': 'authors',
									   'collected_by': 'bs-collected_by',
									   'country': 'src-country',
									   'isolate': 'bs-isolate',
									   'host': 'bs-host',
									   'host_disease': 'bs-host_disease',
									   'lat_lon': 'bs-lat_lon',
									   'sex': 'bs-host_sex',
									   'age': 'bs-host_age',
									   'assembly_method': 'cmt-Assembly-Method',
									   'mean_coverage': 'cmt-Coverage',
									   'illumina_sequencing_instrument': 'sra-instrument_model',
									   'illumina_library_strategy': 'sra-library_strategy',
									   'illumina_library_source': 'sra-library_source',
									   'illumina_library_selection': 'sra-library_selection',
									   'illumina_library_layout': 'sra-library_layout',
									   'illumina_library_protocol': 'sra-library_construction_protocol',
									   'ncbi_sequence_name_sra':'gb-seq_id',
									   'description':'bs-description',
									   'file_location':'sra-file_location',
									   'submitting_lab':'gb-subm_lab',
									   'submitting_lab_division':'gb-subm_lab_division',
									   'submitting_lab_address':'gb-subm_lab_addr',
									   'publication_status':'gb-publication_status',
									   'publication_title':'gb-publication_title',
									   'isolation_source':'bs-isolation_source',
									   }, inplace = True)
		self.filled_df['src-isolate'] = self.filled_df['bs-isolate']
		self.filled_df['src-host'] = self.filled_df['bs-host']
		self.filled_df['cmt-HOST_AGE'] = self.filled_df['bs-host_age']
		self.filled_df['cmt-HOST_GENDER'] = self.filled_df['bs-host_sex']
		self.filled_df['src-isolation_source'] = self.filled_df['bs-isolation_source']

	# todo: this is a temporary fx to convert the illumina paths as input to seqsender
	def change_illumina_paths(self):
		""" Change illumina_sra_file_path_1 & illumina_sra_file_path_2 to sra-file_name
		"""

		# function to extract file name from path
		def extract_filename(path):
			if '/' in path:
				return path.split('/')[-1] # todo: assume Unix paths ok?
			else:
				return path

		# create new column 'sra-file_name'
		self.filled_df['sra-file_name'] = self.filled_df.apply(lambda row: extract_filename(row['illumina_sra_file_path_1']) + ',' + extract_filename(row['illumina_sra_file_path_2']), axis=1)

		# drop original columns
		self.filled_df = self.filled_df.drop(['illumina_sra_file_path_1', 'illumina_sra_file_path_2'], axis=1)
		

	# todo: apply this function to Ankush's insert checks as well
	def check_nan_for_column(self, column_name):
		""" Check for NaN values (if not a string) in a column of the dataframe """
		assert column_name in self.filled_df.columns.values
		assert True not in [math.isnan(x) for x in self.filled_df[column_name].tolist() if isinstance(x, str) is False]

# todo: handle multiple tsvs for illumina vs. nanopore - another class?

class CustomFieldsFuncs:
	""" Class constructor containing attributes/methods for handling custom fields processes
	"""
	def __init__(self, parameters):
		# parameters
		self.parameters = parameters
		# the dictionary containing the actual contents from JSON file
		self.custom_fields_dict = {}

	def read_custom_fields_file(self):
		""" Reads the JSON file to get the information from it
		"""
		# get the encoding of the JSON file 
		"""
		with open(self.parameters['custom_fields_file'], 'rb') as custom_file_encoding:
			result = chardet.detect(custom_file_encoding.read())
			encoding = result['encoding']
		"""

		# read the JSON file in
		with open(self.parameters['custom_fields_file'], 'r') as custom_file:
			data = json.load(custom_file)

		# save contents to dictionary
		for field_name, field_data in data.items():
			self.custom_fields_dict[field_name] = {
        		'type': field_data['type'],
        		'samples': field_data['samples'],
				'replace_empty_with': field_data['replace_empty_with'], 
				'new_field_name': field_data['new_field_name']
			}
	
	def validate_custom_fields(self, sample_info, error_file):
		""" Carries out the desired validation for custom field 
		"""
		# write the sample name to error file
		error_file.write(f"\n\n{list(sample_info['sample_name'].values())[0]}:")

		# loop through the custom fields to check for sample 
		error = ""
		cols_renamed = {}
		for field_name in self.custom_fields_dict.keys():

			# check that the sample name is in the samples listed within custom fields
			if list(sample_info['sample_name'].values())[0] in self.custom_fields_dict[field_name]['samples']:

				# check that the field name exists and if not then create it
				if field_name not in sample_info.keys():
					sample_info[field_name] = None

				# check that the field name is not empty for sample
				if sample_info[field_name]:
			
					# look at the type
					val_type = self.custom_fields_dict[field_name]['type']

					# check the different types if it is not just 'present'
					if val_type != 'present':

						# get the value from sample / custom field 
						samp_custom_field_val = list(sample_info[field_name].values())[0]

						# initialize type error 
						type_error = ""

						# check and try to convert to bool
						if val_type == 'bool':
							if not isinstance(samp_custom_field_val, bool):
								type_error += f"\n\t{field_name} value was not bool. Converting to bool"
								try:
									sample_info[field_name][0] = bool(samp_custom_field_val)
									type_error += f"\n\tSuccessfully converted {field_name} to a bool"
								except:
									type_error += f"\n\tUnable to convert {field_name} to a bool."
							else:
								type_error += f"\n\t{field_name} value was a bool. No need to convert"
						
						# check and try to convert to string
						elif val_type == 'string':
							if not isinstance(samp_custom_field_val, str):
								type_error += f"\n\t{field_name} value was not string. Converting to string"
								try:
									sample_info[field_name][0] = str(samp_custom_field_val)
									type_error += f"\n\tSuccessfully converted {field_name} to a string"
								except:
									type_error += f"\n\tUnable to convert {field_name} to a string."
							else:
								type_error += f"\n\t{field_name} value was a string. No need to convert"

						# check and try to convert to integer
						elif val_type == 'integer':
							if not isinstance(samp_custom_field_val, int):
								type_error += f"\n\t{field_name} value was not int. Converting to int"
								try:
									sample_info[field_name] = int(samp_custom_field_val)
									type_error += f"\n\tSuccessfully converted {field_name} to an int"
								except:
									type_error += f"\n\tUnable to convert {field_name} to an int."
							else:
								type_error += f"\n\t{field_name} value was an int. No need to convert"
						
						# check and try to convert to float
						elif val_type == 'float':
							if not isinstance(samp_custom_field_val, float):
								type_error += f"\n\t{field_name} value was not float. Converting to float"
								try:
									sample_info[field_name] = float(int(samp_custom_field_val))
									type_error += f"\n\tSuccessfully converted {field_name} to a float"
								except:
									type_error += f"\n\tUnable to convert {field_name} to a float."
							else:
								type_error += f"\n\t{field_name} value was a float. No need to convert"

						# write the final type error
						error_file.write(type_error)

				else:
					# means that the value is not present
					error = f"\n\t{field_name} not populated. "

					# check if you need to replace empty with anything
					if self.custom_fields_dict[field_name]['replace_empty_with']:
						# replace the value with specified default
						default_val = self.custom_fields_dict[field_name]['replace_empty_with']
						sample_info[field_name] = default_val
						error += f"\n\tReplaced empty with {default_val}"

				# check if you need to replace the field name 
				new_field_name = self.custom_fields_dict[field_name]['new_field_name']
				if new_field_name:
					# add to the cols that have been renamed 
					cols_renamed[field_name] = new_field_name
					# replace the field name to something new
					sample_info[new_field_name] = sample_info[field_name]
					# print this out to error message 
					error += f"\n\tReplaced field name ({field_name}) with {new_field_name}" 

		# write the error for the field name / sample
		if error:
			error_file.write(error)
		else:
			error_file.write(f"\n\tAll custom field checks passed")

		# convert back to pandas dataframe 
		sample_info = pd.DataFrame(sample_info)

		return sample_info, cols_renamed



class CustomFieldsChecks():
	""" Subclass containing checks for custom fields 
	"""
	def __init__(self, parameters, custom_fields_dict, error_file):
		self.parameters = parameters
		# get the custom fields dict
		self.custom_fields_dict = custom_fields_dict
		# fields that must be populated and not empty
		self.necessary_fields_for_checks = ['name']
		# flag for tracking whether or not can proceed with custom checks
		self.proceed_with_custom_checks = False
		# error file to append for checks
		self.error_file = error_file
		# possible dtype inputs passed in 
		self.possible_type_name_str = ['str', 'string', 'strin', 's', 'word']
		self.possible_type_name_int = ['int', 'integer', 'intege', 'i', 'number']
		self.possible_type_name_bool = ['bool', 'boolean', 'boolea', 'boo', 'b', 'true/false']
		self.possible_type_name_float = ['float', 'decimal', 'fraction']

	def clean_lists(self, samp_names):
		""" Goes through the custom field names specified 
		"""
		# go through the field names within the JSON
		custom_fields = self.custom_fields_dict.copy()
		for field_name in self.custom_fields_dict.keys():

			# check that the field name is not empty
			if not field_name:
				# delete key from final dictionary 
				custom_fields = custom_fields.pop(field_name)
				# write error message 
				self.error_file.write(f"\nEmpty Custom Field Name Provided! Cannot be empty.\n")
			else:
				# write the field name to error message
				self.error_file.write(f"\n\n{field_name}:\n")
				# make the flag true
				self.proceed_with_custom_checks = True 

				# go through the different subfields (type, and sample names)
				subfields = self.custom_fields_dict[field_name]

				# specifically check type and samples subfields for the custom field wanting to be checked
				for field in ['type', 'samples']:

					# check that field is present and not empty 
					if field in subfields.keys() and subfields[field]:

						# assert that the field is either a string or a list of strings for samples
						is_original_dtype_valid = True 
						no_samp_val_string = False
						try:
							assert isinstance(subfields[field], str) or isinstance(subfields[field], list)
							if isinstance(subfields[field], list):
								# make sure that only samples are a list of strings
								assert field == 'samples'
								assert all([isinstance(x, str) for x in subfields[field]])
						except:
							# write the error and handle cases for samples
							if field == 'samples':
								if isinstance(subfields[field], list):
									# there are some values that are properly formatted (in string form) (remove all that are not and continue)
									if [isinstance(x, str) for x in subfields[field]].count(True) != 0:
										self.error_file.write(f"\tFound value(s) in subfield {field} for the custom field named {field_name} " + \
															f"that are not all strings... will remove these")
										# only keep the ones that are string 
										self.custom_fields_dict[field_name]['samples'] = [x for x in subfields[field] if isinstance(x, str)]
									else:
										# there are no values in list that are string 
										no_samp_val_string = True 
								else:
									no_samp_val_string = True

								# check if no samp val string is true or not and provide error + change it 
								if no_samp_val_string is True:
									# either a single value that is invalid or no values in list are strings
									self.error_file.write(f"\tFound no valid value(s) in subfield {field} for the custom field named {field_name} " + \
														f"that is a string... will proceed with all")
									self.custom_fields_dict[field_name]['samples'] = ['all']
									# skip the cleaning
									is_original_dtype_valid = False

						# only proceed if the original dtype is valid
						if is_original_dtype_valid is True:

							# now perform specific check for sample names subfield
							if field == 'samples':
								skip_field_name = self.clean_sample_names(
									field_name=field_name,
									samp_names=samp_names
								)
								# remove the custom field due to no overlapping samples
								if skip_field_name is True:
									custom_fields.pop(field_name)
									self.error_file.write(f"\tUnable to validate this field name because no samples specified were in the metadata file")
							elif field == 'type':
								self.clean_custom_field_types(
									field_name=field_name
								)

					else:
						if field == 'samples':
							# proceed with all samples
							self.custom_fields_dict[field_name]['samples'] = 'all'
						
						elif field == 'type':
							# put the default value of present
							self.custom_fields_dict[field_name]['type'] = 'present'

		# if the flag to continue is still false, then do not proceed with custom and print error
		if self.proceed_with_custom_checks is False:
			# write the error
			self.error_file.write(f"\n\nDid not pass in any valid field name to check. Skipping custom checks.\n")
		elif self.proceed_with_custom_checks is True and not custom_fields:
			# if the dictionary is empty and a sample name was specified, it must be that no samples provided are within metadata sheet 
			# write the error 
			self.error_file.write(f"\n\nFor all custom fields, did not pass in any sample names within metadata file. Skipping custom checks.\n")
			# change the tracking param 
			self.proceed_with_custom_checks = False
		else:
			self.error_file.write(f"\n\nAfter preliminary checks, valid information for custom field names have been passed in. Will now check these accordingly\n")

	def clean_sample_names(self, field_name, samp_names):
		""" Method for actually cleaning the sample names
		"""
		# reset the flag for skipping field name or not
		skip_field_name = False

		samples = self.custom_fields_dict[field_name]['samples']

		# check whether all is present or not / handle differently if case or not for STRING
		if isinstance(samples, str):
			# general cleaning for sample names 
			samples = samples.strip()
			# check if string is equal to all 
			if samples.strip().lower() == 'all':
				# place as a list for consistency 
				samples = ['all']
			# if not then clean it and put into list 
			else:
				samples = [samples.strip().upper()]

		# check whether all is present or not / handle differently if case or not for LIST
		else:
			# general cleaning for sample names 
			samples = [str(x.strip()) for x in samples if len(str(x)) != 0]
			# check if all is present at all within the list
			if 'all' in [x.lower() for x in samples]:
				if len(samples) > 1:
					# proceed with all no matter what 
					self.error_file.write(f"\n\tFound 'all' specified within samples list, AND other values as well. Proceeded with checking all samples in this case.")
				# store the new sample list
				samples = ['all']
			else:
				# make each sample name uppercase and strips
				samples = [x.strip().upper() for x in samples]

		# check that sample name is within the list of sample names from metadata file
		if samples != ['all']:
			if set(samples) != set(samp_names):
				# sample names mentioned in list but not in metadata file
				in_list_not_meta = list(set(samples) - set(samp_names))
				if in_list_not_meta:
					# if all the samples mentioned in the cleaned list are not in metadata file, then skip checks
					if len(in_list_not_meta) == len(samples):
						self.error_file.write(f"\n\tNo sample names specified were present within metadata file. Skipping this field entirely.")
						skip_field_name = True
					else:
						# just get overlapping ones
						self.error_file.write(f"\n\tYou specified some sample names that are not present within metadata file: {in_list_not_meta}. Processed all others.")
						samples = [x for x in samples if x in samp_names]
		
		# set the custom field dict to the cleaned samples 
		self.custom_fields_dict[field_name]['samples'] = samples

		return skip_field_name

	def clean_custom_field_types(self, field_name):
		""" Checks if the subfield for type contains a valid value
		"""
		# extract out the type value
		type_val = self.custom_fields_dict[field_name]['type'].strip().lower()

		# modify the values based on user input
		if type_val in self.possible_type_name_bool:
			# then it is a bool value!
			self.custom_fields_dict[field_name]['type'] = 'bool'
		elif type_val in self.possible_type_name_str:
			# then it is a string value! 
			self.custom_fields_dict[field_name]['type'] = 'string'
		elif type_val in self.possible_type_name_int:
			# then it is an integer value!
			self.custom_fields_dict[field_name]['type'] = 'integer'
		elif type_val in self.possible_type_name_float:
			# then it is a float value!
			self.custom_fields_dict[field_name]['type'] = 'float'
		else:
			# the value provided is not in any of the lists, just check if present or not
			self.error_file.write(f"\n\tCould not determine desired type for field name. Will only check if populated or not")
			self.custom_fields_dict[field_name]['type'] = 'present'

if __name__ == "__main__":
	metadata_validation_main()

