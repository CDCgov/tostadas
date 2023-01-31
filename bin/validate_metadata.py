#!/usr/bin/env python3

# Adapted from Perl scripts by MH Seabolt and Python scripts by J Heuser
# Refactored and updated by AK Gupta and KA O'Connell

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
														'fasta_names', 'overwrite_output_files']]) == len(parameters.keys())
	except AssertionError:
		raise AssertionError(f'Expected keys in parameters dictionary are absent')
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

	# now split the modified and checked dataframe into individual samples
	sample_dfs = {}
	final_df = insert.filled_df
	for row in range(len(final_df)):
		sample_df = final_df.iloc[row].to_frame().transpose()
		sample_df = sample_df.set_index('sample_name')
		sample_dfs[final_df.iloc[row]['sample_name']] = sample_df

	# now export the .xlsx file as a .tsv
	if validate_checks.did_validation_work:
		for sample in sample_dfs.keys():
			tsv_file = f'{parameters["output_dir"]}/{parameters["file_name"]}/tsv_per_sample/{sample}.tsv'
			sample_dfs[sample].to_csv(tsv_file, sep="\t")
			print(f'\nMetadata Validation was Successful!!!\n')
	else:
		print(f'\nMetadata Validation Failed Please Consult : {parameters["output_dir"]}/{parameters["file_name"]}/errors/full_error.txt for a Detailed List\n')
		sys.exit(1)

class GetParams:
	""" Class constructor for getting all necessary parameters (input args from argparse and hard-coded ones)
	"""
	def __init__(self):
		self.parameters = self.get_inputs()
		self.fasta_path = self.parameters['fasta_path']
		# get the file name and put it in parameters dict
		self.parameters['file_name'] = self.parameters['meta_path'].split("/")[-1].split(".")[0]

	def get_parameters(self):
		""" Main function for calling others in getting parameters
		"""
		self.get_restrictions()
		self.parameters['fasta_names'] = self.get_fasta_names()

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
		parser.add_argument("--fasta_path", type=str, help="Path to input Multi Fasta file")
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

	def get_fasta_names(self):
		""" opens up the multiFasta file based on inputted path and gets the names inside of the file
		"""
		fasta_file = open(self.fasta_path, "r")
		fasta_names = []
		while True:
			line = fasta_file.readline()
			if not line:
				break
			if line[0] == ">" and line.strip()[1:].split('_')[0] != 'no' and line.strip()[1:].split('_')[0] != 'not':
				name = line.strip()[1:]
				fasta_names.append(name)
		try:
			assert bool(fasta_names) is True
		except AssertionError:
			raise AssertionError(f'The names in the fasta file could not be properly parsed')
		return fasta_names


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
		df = pd.read_excel(self.parameters['meta_path'], header=[1])
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
		self.final_error_file = open(f'{self.parameters["output_dir"]}/{self.parameters["file_name"]}/errors/full_error.txt', "w")

		# for checking overlap between fasta and metadata file samples
		self.in_f_not_meta, self.in_meta_not_f = [], []

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

		# field requirements
		self.required_core = ["sample_name", "ncbi_sequence_name_biosample_genbank", "author", "isolate", "organism",
							  "collection_date", "country"]
		self.optional_core = ["collected_by", "sample_type", "lat_lon", "purpose_of_sampling"]
		self.case_fields = ["sex", "age", "race", "ethnicity"]

	def validate_main(self):
		""" Main validation function for the metadata
		"""
		# checks whether samples are shared between meta and fasta
		self.check_samples_in_meta_fasta()

		# if there are repeat samples then check them and replace the names
		if len(self.metadata_df['sample_name']) != len(set(self.metadata_df['sample_name'])):
			self.check_for_repeats_in_meta()

		# checks date
		if self.parameters['date_format_flag'].lower() != 'o':
			self.check_date()

		# lists through the entire set of samples and runs the different checks below
		for name in self.metadata_df['sample_name'].tolist():
			self.sample_error_msg = f"\n\t{str(name)}:"
			sample_info = self.metadata_df.loc[self.metadata_df['sample_name'] == name]

			# check the meta code for the sample line
			self.check_meta_core(sample_info)

			# if the author for the sample is not empty then check to make sure if it is properly formatted
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

		# get the final error message
		self.did_validation_work = errors_class.capture_final_error (
			final_error_file = self.final_error_file, repeat_error = self.repeat_error, in_f_not_meta = self.in_f_not_meta,
			in_meta_not_f = self.in_meta_not_f, matchup_error = self.matchup_error, valid_date_flag = self.valid_date_flag,
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

	def check_samples_in_meta_fasta(self):
		""" Check that Meta samples are in the fasta file and fasta files are in the Metadata
		"""
		samp_list = self.metadata_df['sample_name'].tolist()
		fasta_list = self.parameters['fasta_names']
		# get the samples that are not in meta but not in fasta
		[self.in_meta_not_f.append(sample) for sample in samp_list if sample not in fasta_list]
		if self.in_meta_not_f:
			# just double check that it is actually not empty
			try:
				assert len(self.in_meta_not_f) != 0
				assert False not in [sample not in fasta_list and sample in samp_list for sample in self.in_meta_not_f]
			except AssertionError:
				raise AssertionError(f'Issue with detecting samples in meta but not in fasta... double check')
			self.matchup_error += f'Following Metadata Samples are not Found in Provided Fasta File: {", ".join(self.in_meta_not_f)}'
		# get the samples that are in fasta but not in meta
		[self.in_f_not_meta.append(fasta) for fasta in fasta_list if fasta not in samp_list]
		if self.in_f_not_meta:
			try:
				assert len(self.in_f_not_meta) != 0
				assert False not in [sample not in samp_list and sample in fasta_list for sample in self.in_f_not_meta]
			except AssertionError:
				raise AssertionError(f'Issue with detecting samples in fasta but not in meta... double check')
			self.matchup_error += f'Following Fasta Samples are not Found in Provided Metadata File: {self.in_f_not_meta}'

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
			raise AssertionError(f'Meta core grade was not properly reseted to True after sample round')

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
			raise AssertionError(f'Meta case grade was not properly resetted back to True after sample round')

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

	def capture_final_error(self, final_error_file, repeat_error, in_f_not_meta, in_meta_not_f, matchup_error,
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

		# write final error for matchups between fasta and .xlsx files
		if in_f_not_meta is False or in_meta_not_f is False:
			did_validation_work = False
			final_error += matchup_error 

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
		# adds any additional columsn, for now just the Assembly-Data column
		self.insert_additional_columns()
		try:
			assert 'geo_location' in self.filled_df.columns.values
			assert True not in [math.isnan(x) for x in self.filled_df['geo_location'].tolist() if isinstance(x, str) is False]
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
				self.new_combination_list.append(f'{self.list_of_country[i]}:{self.list_of_state[i]}')
			else:
				self.new_combination_list.append(str(self.list_of_country[i]))

		self.filled_df['geo_location'] = self.new_combination_list

	def insert_additional_columns(self):
		""" Inserts additional columns into the metadata dataframe
		"""
		self.filled_df.insert(self.filled_df.shape[1], "structuredcomment", ["Assembly-Data"] * len(self.filled_df.index))

if __name__ == "__main__":
	metadata_validation_main()

