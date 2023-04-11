#!/usr/bin/env python3

# Adapted from Perl scripts by MH Seabolt and Python scripts by J Heuser
# Refactored and updated by AK Gupta and KA O'Connell
 
import pandas as pd
import warnings
import os
import tempfile
import time
import re
import argparse
import sys
import shutil

# import utility functions 
from annotation_utility import MainUtility as main_util
from annotation_utility import GFFChecksUtility as gff_checks_util


def annotation_main():
	""" Main function for calling the annotation transfer pipeline
	"""
	warnings.filterwarnings('ignore')
	
	# get all parameters needed for running the steps
	parameters_class = GetParams()
	parameters_class.get_params_main()
	parameters = parameters_class.parameters

	# get the utility functions needed
	utility_functions = UtilityFunctions(parameters=parameters)

	# run the preparation steps
	annotation_prep = AnnotationPrep(parameters)
	annotation_prep.prep_main()
	# place the seq length for each sample inside of parameters
	parameters['sample_seq_lengths'] = annotation_prep.sample_seq_lengths

	# get the transfer class constructor
	annotation_transfer = AnnotationTransfer(parameters, utility_functions)

	for sample in annotation_prep.sample_list:
		for i in [1,2]:
			annotation_transfer.transfer_annotation(input_fasta=f"{parameters['fasta_temp']}{sample}.fasta", round=i)
		annotation_transfer.round_repeat_info = {}
		
	# delete the temporary files (dependent on flag passed in)
	if str(parameters['delete_temp_files']).lower() == 'true':
		utility_functions.remove_temp()


class GetParams:
	""" Class constructor to get the user-defined parameters for the annotation pipeline
	"""
	def __init__(self):
		self.required_parameters = ['meta_path', 'ref_fasta_path', 'fasta_path', 'ref_gff_path']
		# specify the names of temporary directories + create the temporary directories
		self.temp_dirs = ["", "fastaFiles", "liftoff", "tbl", 'errors']
		self.temp_dirs_purposes = ['root_temp', 'fasta_temp', 'liftoff_temp', 'tbl_temp', 'errors_temp']
		self.final_dirs = ['fasta', 'liftoff', 'tbl', 'errors']
		self.final_dirs_purposes = ['fasta_final', 'liftoff_final', 'tbl_final', 'errors_final']
		self.parameters = None

	def get_params_main(self):
		""" Main function to get the parameters
		"""
		self.get_inputs()
		# check that necessary parameters are present
		for req in self.required_parameters:
			if self.parameters[req] is None or self.parameters[req] == '' or self.parameters[req] == "":
				raise ValueError(f'Please input a valid {req} value...')

		# get the name of the meta file from path and attach the current time to it
		meta_name = self.parameters['meta_path'].split('/')[-1].split('.')[0]
		self.parameters['meta_name'] = meta_name

		# populate parameters with the temporary dir paths and create them
		self.check_dirs(dirs_list=self.temp_dirs, purpose_list=self.temp_dirs_purposes, final_or_temp='temp')

		# check if the final liftoff output directories exist, if not create it with proper permissions
		self.check_dirs(dirs_list=self.final_dirs, purpose_list=self.final_dirs_purposes, final_or_temp='final')

		# unmapped features output file path
		self.parameters['unmapped_features_path'] = f"{self.parameters['errors_temp']}{self.parameters['unmapped_features_file_name']}"

		# get the tag name from the reference fasta file and save in parameters dict
		self.get_tag_name()

	def get_inputs(self):
		""" For getting the user inputs
		"""
		args = self.get_args().parse_args()
		self.parameters = vars(args)

	def check_dirs(self, dirs_list, purpose_list, final_or_temp):
		""" Abstracted function for checking dirs and overwriting
		"""
		for dir, purpose in zip(dirs_list, purpose_list):
			if final_or_temp == 'final':
				dir_path = f"{self.parameters['final_liftoff_output_dir']}/{self.parameters['meta_name']}/{dir}"
			elif final_or_temp == 'temp':
				dir_path = f"{self.parameters['final_liftoff_output_dir']}/temp_{self.parameters['meta_name']}/{dir}"
			if os.path.isdir(dir_path):
				shutil.rmtree(dir_path)
			os.system(f"mkdir -m777 -p {dir_path}")
			self.parameters[purpose] = f"{dir_path}/"

	@staticmethod
	def get_args():
		""" Defines the possible parameters that can be passed in by user (both required and optional)
		"""
		parser = argparse.ArgumentParser(description="Parameters for Running Liftoff Submission")
		# Required Arguments
		parser.add_argument("--fasta_path", type=str, help="Non reference path to input Multi Fasta file \n")
		parser.add_argument("--ref_fasta_path", type=str, help="Reference path to fasta file \n")
		parser.add_argument("--meta_path", type=str, help="Path to excel spreadsheet for MetaData \n")
		parser.add_argument("--ref_gff_path", type=str, help="Path to the input gff file.... expects gff3 format")
		# for the main annotation transfer steps
		parser.add_argument("-o", "--final_liftoff_output_dir", type=str, default='final_liftoff_outputs', help="Output Directory for final Files")
		# for the gff_reformat function specifically
		parser.add_argument("--print_version_and_exit", type=str, help="Print version and exit the program")
		parser.add_argument("--print_help_and_exit", type=str, help="Print help and exit the program")
		parser.add_argument("-d", "--delete_temp_files", type=str, default='True',
							help="Deletes the temporary files after finishing transfer")
		# for liftoff specifically
		parser.add_argument("--parallel_processes", type=int, default=8, help="# of parallel processes to use for liftoff")
		parser.add_argument("--minimap_path", type=str, help="Path to minimap if you did not use conda or pip")
		parser.add_argument("--feature_database_name", type=str, default='',
							help="name of the feature database, if none, then will use ref gff path to construct one")
		parser.add_argument("--unmapped_features_file_name", type=str, default='output.unmapped_features.txt',
							help="Name of unmapped features file name")
		parser.add_argument("--coverage_threshold", type=float,
							help="designate a feature mapped only if it aligns with coverage ≥A")
		parser.add_argument("--child_feature_align_threshold", type=float,
							help="designate a feature mapped only if its child features usually exons/CDS align with sequence identity ≥S")
		parser.add_argument("--exclude_partial", type=str, help="write partial mappings")
		parser.add_argument("--distance_scaling_factor", type=float,
							help='distance scaling factor; alignment nodes separated by ' + \
								 'more than a factor of D in the target genome will not be ' + \
								 'connected in the graph; by default D=2.0')
		parser.add_argument("--flank", type=float,
							help='amount of flanking sequence to align as a fraction [0.0-1.0] of gene length. This can' + \
								 ' improve gene alignment where gene structure differs between target and reference; by default F=0.0')
		parser.add_argument("--infer_genes", type=str, help='use if annotation file only includes transcripts,exon/CDS features')
		parser.add_argument("--infer_transcripts", type=str,
							help='use if annotation file only includes exon/CDS features and does not include transcripts/mRNA')
		parser.add_argument("--path_to_chroms_file", type=str,
							help='comma seperated file with corresponding chromosomes in the reference,target sequences')
		parser.add_argument("--path_to_unplaced_file", type=str,
							help='text file with name(s) of unplaced sequences to map genes from after genes from ' + \
								 'chromosomes in chroms.txt are mapped; default is "unplaced_seq_names.txt"')
		parser.add_argument("--copies", type=str, help='look for extra gene copies in the target genome')
		parser.add_argument("--copy_threshold", type=float, default=1.0,
							help='with -copies, minimum sequence identity in exons/CDS for which a gene is considered a ' + \
								 'copy; must be greater than -s; default is 1.0')
		parser.add_argument("--overlap", type=float,
							help='maximum fraction [0.0-1.0] of overlap allowed by 2 features; by default O=0.1')
		parser.add_argument("--mismatch", type=int,
							help='mismatch penalty in exons when finding best mapping; by default M=2')
		parser.add_argument("--gap_open", type=int,
							help='gap open penalty in exons when finding best mapping; by default GO=2')
		parser.add_argument("--gap_extend", type=int,
							help=' gap extend penalty in exons when finding best mapping; by default GE=1')
		return parser

	def get_tag_name(self):
		""" Retrieves the tag name from fasta file and the length of the sequence for the itr check
		"""
		with open(self.parameters['ref_fasta_path']) as f:
			ref_fasta_lines = [line for line in f.readlines() if line.strip()]
			f.close()
		for line in ref_fasta_lines:
			if '>' in line:
				self.parameters['ref_fasta_tag'] = line.split('>')[-1].strip()


class AnnotationPrep:
	""" Class constructor for performing the preparation steps for the annotation pipeline
	"""
	def __init__(self, parameters):
		self.parameters = parameters
		self.sample_seq_lengths = {}
		self.sample_list = []

	def prep_main(self):
		""" Main prep function for calling split_fasta, split gff for itr mapping, and load_meta
		"""
		# split the fasta file
		main_util.split_fasta (
			fasta_path=f"{self.parameters['fasta_path']}",
			fasta_output=f"{self.parameters['fasta_temp']}"
		)
		# split the ref gff file
		self.split_gff()
		# load the meta data file
		self.load_meta()
		# get the length of sequences for each sample
		self.get_seq_lens()
	
	def split_gff(self):
		"""
		Parses reference GFF file and 
		"""
		# define itr gff file
		gff_itr=str(self.parameters['ref_gff_path']).split('.gff')[0]+'_v2.gff'
		# check if the file already exists from a previous run
		if not os.path.exists(gff_itr):
			# get the gff lines that non empty
			with open(f"{self.parameters['ref_gff_path']}", "r") as ref_gff:
				gff_lines = [line.strip() for line in ref_gff.readlines() if line.strip()]
				ref_gff.close()
				gff_itr_out=open(gff_itr,'w')
			# loop through list and write the lines
			for line in gff_lines:
				if '#' in line:
					gff_itr_out.write(line + "\n")
				elif 'repeat_region' in line:
					gff_itr_out.write(line+"\n")
				else:
					pass

	def load_meta(self):
		""" Imports the Excel file and puts it into a dataframe
		"""
		idf = pd.read_excel(self.parameters['meta_path'], header=[1], sheet_name=0)
		df = idf.set_index("sample_name", drop=False)
		self.sample_list = df.loc[:, "sample_name"]

	def get_seq_lens(self):
		""" Get the sequence lengths from each sample fasta file
		"""
		for sample in self.sample_list:
			seq_len_count = 0
			with open(f"{self.parameters['fasta_temp']}{sample}.fasta", "r") as f:
				fasta_lines = [line for line in f.readlines() if line.strip()]
				f.close()
			for line in fasta_lines:
				if '>' not in line:
					seq_len_count += len(line.strip())
			self.sample_seq_lengths[sample] = seq_len_count
	

class AnnotationTransfer:
	""" Class constructor for the transfer portion of the annotation pipeline
	"""
	def __init__(self, parameters, utility_functions):
		self.parameters = parameters
		# for the different rounds (getting itr first time and then misc_feature second time)
		self.round = None
		self.round_repeat_info = {}
		self.insert_next_line = False
		# for generally cleaning up the lines
		self.fields_to_drop = ['coverage', 'sequence_ID', 'matches_ref_protein', 'valid_ORF', 'valid_ORFs', 'extra_copy_number',
							   'copy_num_ID', 'pseudogene', 'partial_mapping', 'low_identity']
		self.empty_vals = [None, 'None', 'N/A', 'n/a', 'N/a', 'n/A', '', ""]
		self.tab_sep_fields = ['tag', 'source', 'type', 'coordinates', 'orientation']
		self.new_gff = None
		self.new_lines = None
		self.starting = 0
		# for IRT check
		self.repeat_regions = {}
		self.repeat_region_counter = 0
		self.repeat_index_counter = 0
		# for stop codon check
		self.get_next_one = False
		self.dict_for_codon_lines = None
		self.bad_codon_fields = ['missing_start_codon', 'missing_stop_codon', 'inframe_stop_codon']

		# get the utility functions
		self.utility_functions = utility_functions

		# get the check function
		self.check_functions = GFFChecks(parameters=self.parameters, tab_sep_fields=self.tab_sep_fields)

		# set up the text files for the stop codon errors and itr checks
		self.utility_functions.abstracted_error_file_check(f"{self.parameters['errors_temp']}annotation_error.txt")

	def transfer_annotation(self, input_fasta, round):
		""" Main function for calling liftoff and passing in needed args
		"""
		# get the sample name
		samp_name = str(input_fasta.split('/')[-1].split(".")[0])

		# get features for round + other information
		self.round = round
		if round == 1:
			ftype_features = ['repeat_region']
			gff_ref = str(self.parameters['ref_gff_path']).split('.gff')[0]+'_v2.gff'
		else:
			ftype_features = ['misc_feature']
			gff_ref=self.parameters['ref_gff_path']
			
		# write the liftoff features file
		with open(f"{self.parameters['liftoff_temp']}ftypes.liftoff.tmp", 'w') as out:
			for feature in ftype_features:
				out.write(f"{feature}\n")
			out.close()

		liftoff_command = f"liftoff -p {self.parameters['parallel_processes']} -f {self.parameters['liftoff_temp']}ftypes.liftoff.tmp " + \
			f"-u {self.parameters['unmapped_features_path']} -g "
		liftoff_command += gff_ref
		liftoff_command += f" -o {self.parameters['liftoff_temp']}{samp_name}.liftoff-orig.gff -dir {self.parameters['liftoff_temp']} "

		# if it is the second round then can use the custom params for liftoff
		if round == 2:
			# handle coverage threshold
			if self.parameters['coverage_threshold'] not in self.empty_vals:
				liftoff_command += f"-a {self.parameters['coverage_threshold']} "

			# handle child feature align threshold
			if self.parameters['child_feature_align_threshold'] not in self.empty_vals:
				liftoff_command += f"-s {self.parameters['child_feature_align_threshold']} "

			# handle exclude partial
			if self.parameters['exclude_partial'] not in self.empty_vals:
				liftoff_command += f"-exclude_partial {self.parameters['exclude_partial']} "

			# handle feature database name
			if self.parameters['feature_database_name'] not in self.empty_vals:
				liftoff_command += f"-db {self.parameters['feature_database_name']} "

			# handle minimap path
			if self.parameters['minimap_path'] not in self.empty_vals:
				liftoff_command += f"-m {self.parameters['minimap_path']} "

			# handle copies
			if self.parameters['copies'] is True:
				liftoff_command += f"-copies {self.parameters['copies']} -sc {self.parameters['copy_threshold']} "

			# handle a few other misc settings
			if self.parameters['flank'] not in self.empty_vals:
				liftoff_command += f"-flank {self.parameters['flank']} "

			if self.parameters['infer_genes'] not in self.empty_vals:
				liftoff_command += f"-infer_genes {self.parameters['infer_genes']} "

			if self.parameters['infer_transcripts'] not in self.empty_vals:
				liftoff_command += f"-infer_transcripts {self.parameters['infer_transcripts']} "

			if self.parameters['path_to_chroms_file'] not in self.empty_vals:
				liftoff_command += f"-chroms {self.parameters['path_to_chroms_file']} "

			if self.parameters['path_to_unplaced_file'] not in self.empty_vals:
				liftoff_command += f"-unplaced {self.parameters['path_to_unplaced_file']} "

			if self.parameters['overlap'] not in self.empty_vals:
				liftoff_command += f"-overlap {self.parameters['overlap']} "

			if self.parameters['mismatch'] not in self.empty_vals:
				liftoff_command += f"-mismatch {self.parameters['mismatch']} "

			if self.parameters['gap_open'] not in self.empty_vals:
				liftoff_command += f"-gap_open {self.parameters['gap_open']} "

			if self.parameters['gap_extend'] not in self.empty_vals:
				liftoff_command += f"-gap_extend {self.parameters['gap_extend']} "

		# add final part of liftoff command
		liftoff_command += f"-cds {input_fasta} {self.parameters['ref_fasta_path']} >liftoffCommand.txt"
		# call the command
		os.system(liftoff_command)

		self.new_gff = f"{self.parameters['liftoff_temp']}{samp_name}.liftoff-orig.gff"
		gff_lines, self.starting = self.utility_functions.read_gff_in(self.new_gff)

		# if it is the first round then we need to store the repeat_region information
		if round == 1:
			repeat_counter = 1
			for line in gff_lines[self.starting:]:
				split_string = re.split('[;\t\n]', line)
				if split_string[2] == 'repeat_region':
					self.round_repeat_info[str(repeat_counter)] = line
					repeat_counter += 1
		else:
			# pass the new gff to the reformatting
			self.reformat_gff(samp_name, gff_lines)
			# pass the gff from reformatting function for gff --> tbl
			main_util.gff2tbl(
				samp_name=samp_name,
				gff_loc=f"{self.parameters['liftoff_temp']}{samp_name}_reformatted.gff",
				tbl_output=self.parameters['tbl_temp']
			)
			# move the generated files from temp dir to final dir
			self.utility_functions.move_data(samp_name)

	def reformat_gff(self, samp_name, gff_lines):
		""" Reformats and cleans the gff outputted from liftoff
		"""
		# initialize necessary vars/structures
		self.repeat_regions = {}
		self.repeat_region_counter = 0
		self.new_lines = []
		self.dict_for_codon_lines = {'mapping_for_line': [], 'index_in_new_lines': [], 'flag': [], 'coordinates': []}
		self.insert_next_line = False
		self.repeat_index_counter = 0

		# write the sample name to error text
		with open(f"{self.parameters['errors_temp']}annotation_error.txt", 'a') as out:
			out.write(f"\n\n{samp_name}:")

		# print out the version and exit the program if selected
		if self.parameters['print_version_and_exit'] is True:
			print(f'\nreformatGFF v1.0\n')
			sys.exit(1)
		# print out the help message and exit the program if selected
		if self.parameters['print_help_and_exit'] is True:
			print(f'USAGE:	reformatGFF -i <original.gff> -o <modified.gff>')
			sys.exit(1)

		# check if it is the first line or not, if it is replace it with the line you got from previous round
		gff_lines = self.add_repeat_region_lines(gff_lines)

		for line in gff_lines[self.starting:]:
			# first check if it is not the trailing ### that comes up on a separate line sometimes
			if list(set(line.strip())) == ['#']:
				self.new_lines.append(line.strip())
				break

			# pass string into the general line cleaup function
			split_string = re.split('[;\t\n]', line)
			field_value_mapping = self.utility_functions.line_cleanup(
				split_string=split_string,
				samp_name=samp_name,
				fields_to_drop=self.fields_to_drop,
				repeat_regions=self.repeat_regions,
				repeat_index_counter=self.repeat_index_counter,
				repeat_region_counter=self.repeat_region_counter,
			)

			# rewrite the new line with the drops and cleaned up
			new_line = self.utility_functions.abstracted_gff_line_writer(field_value_mapping, tab_sep_fields=self.tab_sep_fields)
			if new_line.endswith(';'):
				raise ValueError(f"Added a ; at the end of the line when reformatting GFF: {new_line}")
			self.new_lines.append(new_line)

			# check whether you need to store line and following line for the codon changes
			# reads the line, if flag in it then gets next line during loop and stores in dict
			if self.get_next_one is False:
				key_match_bad_codon = [key for key in field_value_mapping.keys() if key in self.bad_codon_fields]
				if key_match_bad_codon:
					self.dict_for_codon_lines['flag'].append(key_match_bad_codon[0])
					self.get_next_one = True
			elif self.get_next_one is True:
					self.dict_for_codon_lines['mapping_for_line'].append(field_value_mapping)
					self.dict_for_codon_lines['index_in_new_lines'].append(len(self.new_lines)-1)
					self.dict_for_codon_lines['coordinates'].append(field_value_mapping['coordinates'])
					self.get_next_one = False

			# check if you need to store mapping for itr check
			if field_value_mapping['type'] == 'repeat_region':
				self.repeat_regions[f'repeat_region{self.repeat_region_counter}']['line_map_dict'] = field_value_mapping
				self.repeat_region_counter += 1

			# iterate the index counter for itr check
			self.repeat_index_counter += 1

		# check if the repeat regions are correct
		if len(self.repeat_regions.keys()) == 2:
			itr_errors, self.new_lines = self.check_functions.check_itr(
				samp_name=samp_name,
				repeat_regions=self.repeat_regions,
				new_lines=self.new_lines,
			)
		else:
			error = f"Could not find both repeat regions, only {len(self.repeat_regions.keys())}/2 repeat regions found in {samp_name}.liftoff-orig.gff file"
			print(f"{error}")
			itr_errors = [error]

		# check if the stop codons are correct
		if self.dict_for_codon_lines['mapping_for_line']:
			codon_errors, self.new_lines = self.check_functions.check_stop_codons(
				samp_name=samp_name,
				dict_for_codon_lines=self.dict_for_codon_lines,
				new_lines=self.new_lines,
				starting=self.starting,
			)
		else:
			codon_errors = [f"No stop codon field found in {samp_name}.liftoff-orig.gff"]

		# write all lines to new gff after reformatting, drops, and checks
		with open(f"{self.parameters['liftoff_temp']}{samp_name}_reformatted.gff", 'w') as g:
			for x in range(self.starting):
				g.write(f'{gff_lines[x]}')
			for new_line in self.new_lines:
				g.write(f'{new_line}\n')

		# write all the errors to the annotation.txt
		with open(f"{self.parameters['errors_temp']}annotation_error.txt", 'a') as out:
			# write the stop codon check
			out.write(f"\n\tSTOP CODON CHECK:\n")
			for codon_error in codon_errors:
				out.write(f"\t{codon_error}\n")
			# write the ITR check
			out.write(f"\n\tITR CHECK:\n")
			for itr_error in itr_errors:
				out.write(f"\t{itr_error}\n")

	def add_repeat_region_lines(self, gff_lines):
		""" Adds the lines for the repeat regions to the read in gff file
		"""
		# change the gff lines to add the first line to the beginning
		if '1' in self.round_repeat_info.keys():
			gff_lines.insert(self.starting, self.round_repeat_info['1'])
		# now find where to insert the second line
		if '2' in self.round_repeat_info.keys():
			for y in range(len(gff_lines)):
				# check if the gene feature is where we want to insert the second repeat region
				split_string = re.split('[;\t\n]', gff_lines[y])
				for x in range(len(split_string)):
					if '=' in split_string[x] and split_string[x].split('=')[0] == 'gene' and split_string[x].split('=')[1] == 'OPG016':
						# insert two after
						gff_lines.insert(y+2, self.round_repeat_info['2'])
						return gff_lines
		else: 
			return gff_lines


class GFFChecks:
	def __init__(self, parameters, tab_sep_fields):
		""" Checks after general reformatting
		"""
		self.parameters = parameters
		self.tab_sep_fields = tab_sep_fields
		self.utility_functions = UtilityFunctions

	def check_stop_codons(self, samp_name, dict_for_codon_lines, new_lines, starting):
		"""
		Reads the self.dict_for_codon_lines and performs following operations:
		Changes the type and ID in CDS line (with dup coordinates) (below the gene line) to misc_feature.
		Deletes the product in CDS line.
		"""
		# get the necessary values
		codon_errors = []
		for i in range(len(dict_for_codon_lines['mapping_for_line'])):
			line_map_dict = dict_for_codon_lines['mapping_for_line'][i]
			line_index = dict_for_codon_lines['index_in_new_lines'][i]
			line_flag = dict_for_codon_lines['flag'][i]
			coordinates = ', '.join(((dict_for_codon_lines['coordinates'][i]).split('\t')))

			# make changes to the key value mapping dict
			line_map_dict['ID'] = line_map_dict['ID'].replace(line_map_dict['type'].lower(), 'misc_feature')
			line_map_dict['ID'] = line_map_dict['ID'].replace(line_map_dict['type'], 'misc_feature')
			try:
				assert 'misc_feature' in line_map_dict['ID']
			except AssertionError:
				raise AssertionError(f"CDS in ID could not be replaced with misc_feature")
			line_map_dict['type'] = 'misc_feature'
			line_map_dict.pop('product')

			# write the new line with changes
			new_line = self.utility_functions.abstracted_gff_line_writer(line_map_dict,
																		 tab_sep_fields=self.tab_sep_fields)

			# replace the line in new_lines with this modified one
			try:
				assert 'product=' not in new_line
				assert new_line.endswith(';') is False
			except AssertionError:
				raise AssertionError(f"Stop Codon was detected but proper changes could not be carried out to gff file")
			new_lines[line_index] = new_line

			# store the error
			print(f"Found {line_flag} in gff line")
			codon_errors.append(f"Field for stop codon found in {samp_name}.liftoff-orig.gff: {line_flag} in line " + \
								f"{line_index + starting} at coordinates {coordinates}")

		return codon_errors, new_lines

	def check_itr(self, samp_name, repeat_regions, new_lines):
		""" For checking all codon information is present and correct... raises flags and writes errors
		"""
		# get necessary values
		first_region_coord1 = int(repeat_regions['repeat_region0']['coordinates'].split('\t')[0])
		first_region_coord2 = int(repeat_regions['repeat_region0']['coordinates'].split('\t')[1])
		second_region_coord1 = int(repeat_regions['repeat_region1']['coordinates'].split('\t')[0])
		second_region_coord2 = int(repeat_regions['repeat_region1']['coordinates'].split('\t')[1])
		errors = []

		# make sure that the first repeat_region has coordinates that start at 1
		if int(first_region_coord1) != 1:
			error = f"First repeat region coordinates does not start at 1: ({first_region_coord1}, {first_region_coord2}) in {samp_name}.liftoff-orig.gff.file"
			errors.append(error)
			# change the repeat region to start at 1
			repeat_regions['repeat_region0']['line_map_dict']['coordinates'] = f"1\t{first_region_coord2}"

		# make sure that the final coordinate in the second repeat_region extends to the end
		if second_region_coord2 < self.parameters['sample_seq_lengths'][samp_name]:
			error = f"Second repeat region does not extend to end in {samp_name}.liftoff-orig.gff file: {second_region_coord1, second_region_coord2} coordinates " \
					f"with overall seq length of {self.parameters['sample_seq_lengths'][samp_name]}"
			errors.append(error)
			# change the last coordinate to extend to end
			repeat_regions['repeat_region1']['line_map_dict'][
				'coordinates'] = f"{second_region_coord1}\t{self.parameters['sample_seq_lengths'][samp_name]}"

		# make sure that both repeat_regions are the same length
		length_region0 = first_region_coord2 - 1
		length_region1 = self.parameters['sample_seq_lengths'][samp_name] - second_region_coord1
		if length_region0 != length_region1:
			error = f"First repeat region length of {length_region0} at {1, first_region_coord2} does not " \
					f"equal second repeat region length of {length_region1} at {second_region_coord1, self.parameters['sample_seq_lengths'][samp_name]} " \
					f"in {samp_name}.liftoff-orig.gff file"
			errors.append(error)

		# write the line map dict to line and then replace new lines with this line
		new_line1 = self.utility_functions.abstracted_gff_line_writer(
			line_map_dict=repeat_regions['repeat_region0']['line_map_dict'], tab_sep_fields=self.tab_sep_fields)
		new_line2 = self.utility_functions.abstracted_gff_line_writer(
			line_map_dict=repeat_regions['repeat_region1']['line_map_dict'], tab_sep_fields=self.tab_sep_fields)
		new_lines[repeat_regions['repeat_region0']['index']] = new_line1
		new_lines[repeat_regions['repeat_region1']['index']] = new_line2
		return errors, new_lines


class UtilityFunctions:
	def __init__(self, parameters):
		self.parameters = parameters

	@staticmethod
	def abstracted_error_file_check(path_to_file):
		""" General function for checking whether a file is present
		"""
		if os.path.isfile(path_to_file):
			os.remove(path_to_file)
			with open(path_to_file, 'w') as _:
				pass

	@staticmethod
	def read_gff_in(gff_file):
		""" Reads the gff file in
		"""
		# read the gff file in
		with open(gff_file) as f:
			gff_lines = [line for line in f.readlines() if line.strip()]
			f.close()

		# get necessary stuff before looping through
		starting = 0
		while True:
			if '#' in gff_lines[starting]:
				starting += 1
			else:
				break
		return gff_lines, starting

	@staticmethod
	def abstracted_gff_line_writer(line_map_dict, tab_sep_fields):
		""" Writes the lines to appropriate gff formatting
		"""
		new_line = f"{line_map_dict['tag']}\t{line_map_dict['source']}\t{line_map_dict['type']}\t{line_map_dict['coordinates']}\t" + \
				   f"{line_map_dict['orientation']}"
		for y in range(len(line_map_dict.keys())):
			# determine if it is the first five columns, if so, it must be tab separated otherwise ; separated
			key = list(line_map_dict.keys())[y]
			if key not in tab_sep_fields:
				if y != len(list(line_map_dict.keys())) - 1:
					new_line += f'{key}={line_map_dict[key]};'
				else:
					new_line += f'{key}={line_map_dict[key]}'
		return new_line

	def line_cleanup(self, split_string, samp_name, fields_to_drop, repeat_regions, repeat_index_counter, repeat_region_counter):
		""" Utility function for cleaning up the lines in gff
		"""
		# get the field and value mapping from each line (just for checks and easily look things up)
		field_value_mapping = {
			'tag': split_string[0],
			'source': split_string[1],
			'type': split_string[2],
			'coordinates': f'{split_string[3]}\t{split_string[4]}',
		}

		# check if repeat region
		if field_value_mapping['type'] == 'repeat_region':
			repeat_regions[f'repeat_region{repeat_region_counter}'] = {
				'coordinates': field_value_mapping['coordinates'],
				'index': repeat_index_counter,
			}

		# check if = separated or if it is the orientation
		for x in range(len(split_string)):
			if '=' in split_string[x]:
				field_value_mapping[split_string[x].split('=')[0]] = split_string[x].split('=')[1]
			else:
				y = 5
				while True:
					if '=' in split_string[y]:
						raise ValueError(f'Unable to properly locate the gene coordinates... ')
					elif split_string[y] == '+' or split_string[y] == '-':
						field_value_mapping['orientation'] = f'.\t{split_string[y]}\t.\t'
						break
					y += 1

		# now check if any of the keys in the dict or field is within the drop list passed in
		matching_fields = list(set(fields_to_drop) & set(list(field_value_mapping.keys())))
		if matching_fields:
			for drop_match in matching_fields:
				field_value_mapping.pop(drop_match)
		if [x for x in field_value_mapping.keys() if x in fields_to_drop]:
			raise ValueError(
				f"Fields were properly not dropped from gff: {[x for x in field_value_mapping.keys() if x in fields_to_drop]}")

		# now check if any of the acquired fields have the ref fasta tag as value, if so, then replace with sample name
		has_ref_fasta_tag = [key for key in field_value_mapping.keys() if
							 self.parameters['ref_fasta_tag'] in field_value_mapping[key]]
		for key in has_ref_fasta_tag:
			field_value_mapping[key] = field_value_mapping[key].replace(self.parameters['ref_fasta_tag'], samp_name)
		try:
			assert not [key for key in field_value_mapping.keys() if
						self.parameters['ref_fasta_tag'] in field_value_mapping[key]]
		except AssertionError:
			raise AssertionError(
				f"Tags in keys in field_value_mapping were not properly were not properly replace with sample name")

		# now check whether a # sign is in the note section
		return gff_checks_util.check_note(field_value_mapping=field_value_mapping)

	def move_data(self, sample):
		""" Moving the data to the output directory
		"""
		# copying the temporary directories to the specified directory for the final files from liftoff
		liftoff_cp_command = f"cp {self.parameters['liftoff_temp']}{sample}_reformatted.gff {self.parameters['liftoff_final']}"
		fasta_cp_command = f"cp {self.parameters['fasta_temp']}{sample}.fasta {self.parameters['fasta_final']}"
		tbl_cp_command = f"cp {self.parameters['tbl_temp']}{sample}.tbl {self.parameters['tbl_final']}"
		errors_cp_command = f"cp -r {self.parameters['errors_temp']}* {self.parameters['errors_final']}"

		# os.system(tsvCpCommand)
		os.system(liftoff_cp_command)
		os.system(fasta_cp_command)
		os.system(tbl_cp_command)
		os.system(errors_cp_command)

		# remove the command text file for liftoff and unmapped features text
		# get_current_dir = '/'.join(repr(__file__).replace("'", '').split('/')[:-1])
		os.system(f"rm -f {os.path.join(os.getcwd(), 'liftoffCommand.txt')}")

	def remove_temp(self):
		""" Removing temporary directories
		"""
		os.system(f"rm -r {self.parameters['final_liftoff_output_dir']}/temp_{self.parameters['meta_name']}")


if __name__ == "__main__":
	annotation_main()
