#!/usr/bin/env python3

import argparse
import pandas as pd
import os 
import shutil
import glob
from pathlib import Path
import sys

from annotation_utility import MainUtility as main_util


def get_args():
    parser = argparse.ArgumentParser(description="Parameters for General Utility Functions")
    # different files to check
    parser.add_argument("--meta_path", type=str, help="Path to the input metadata file(s)")
    parser.add_argument("--fasta_path", type=str, help="Path to the fasta file(s)")
    parser.add_argument("--gff_path", type=str, help="Path to the gff file(s)")
    parser.add_argument("--ref_gff_path", type=str, help="Path to the ref gff file")
    parser.add_argument("--ref_fasta_path", type=str, help="Path to the ref fasta file")
    parser.add_argument("--submission_config", type=str, help="Path to the submission config")
    # different flags to orient checks 
    # parser.add_argument("--individual_meta_files_flag", type=str, help="Is it individual files or no")
    parser.add_argument("--annotation_entry", type=str, help="Is it the entrypoint or not")
    parser.add_argument("--run_submission", type=str, help="Whether to run submission or not")
    parser.add_argument("--run_annotation", type=str, help="Whether to run annotation or not")
    parser.add_argument("--run_liftoff", type=str, help="Whether to run liftoff or not")
    parser.add_argument("--run_repeatmasker_liftoff", type=str, help="Whether to run repeatmasker liftoff or not")
    parser.add_argument("--run_vadr", type=str, help="Whether to run vadr or not")
    parser.add_argument("--run_bakta", type=str, help="Whether to run bakta or not")
    # which datbases are being submitted to 
    parser.add_argument("--submission_database", type=str, help="Which databases are being submitted to")
    """
    parser.add_argument("--check_fasta_paths", type=bool, default=False, help="Flag whether to check FASTA paths or not")
    parser.add_argument("--check_fasta_names", type=bool, default=False, help="Flag whether to check FASTA names or not")
    parser.add_argument("--output_fasta_path", type=str, help="Path to the output directory for fasta file(s)")
    parser.add_argument("--output_fasta_path", type=str, help="Path to the output directory for fasta file(s)")
    """
    return parser

def main(): 

    # get the parameters
    args = get_args().parse_args()
    parameters = vars(args)

    # instantiate the class 
    general_util = GeneralUtil()

    # create the dictionary for tracking which files exist 
    files_exist_dict = {
        'fasta_path': [False, ['.fasta', '.fastq'], True],
        'meta_path': [False, ['.tsv', '.csv'], True],
        'ref_fasta_path': [False, ['.fasta'], False],
        'ref_gff_path': [False, ['.gff'], False], 
        'gff_path': [False, ['.gff'], True],
        'submission_config': [False, ['.yaml', '.yml'], False]
    }

    """
    # check if the individual meta files flag is true or false + change accordingly 
    if parameters['individual_meta_files_flag'].lower().strip() == 'true':
        files_exist_dict['meta_path'] = [False, ['.tsv', '.csv'], True]
    else:
        files_exist_dict['meta_path'] = [False, ['.xlsx', ], False]
    """

    # go through each list file and check if it exists + update it 
    for key in files_exist_dict.keys():
        # call the check function
        files_exist_dict[key][0] = general_util.check_files_exist (
            parameters[key], 
            files_exist_dict[key][2], 
            extensions=files_exist_dict[key][1]
        )


    # TODO: need to add check for whether or not a .GZ file was passed in for fastas, if so unzip, then proceed with 

    # check if annotation entry is being called, if so, then only need to check fasta files
    # TODO: need to add checks for the fasta to this part, where names are checked / renamed, etc.
    if parameters['annotation_entry'].lower().strip() == 'false':
        try:
            assert files_exist_dict['fasta_path'][0] is True
        except:
            raise AssertionError(f"\nValid FASTA files were not found at {parameters[fasta_path]} with either .fastq or .fasta ext... needed for annotation\n")


    # check annotation, there must be ref fasta/gff, fasta, and meta (liftoff) + just fasta and meta (vadr and bakta)
    if parameters['run_annotation'].lower().strip() == 'true' and parameters['annotation_entry'].lower().strip() == 'false':

        # do general checks 
        if any([parameters['run_liftoff'].lower().strip(), parameters['run_repeatmasker_liftoff'].lower().strip(),  
            parameters['run_vadr'].lower().strip(), parameters['run_bakta'].lower().strip()]):
            
            # need to have meta and fasta 
            for file_param in ['fasta_path', 'meta_path']:
                try:
                    assert files_exist_dict[file_param][0] is True
                except:
                    raise AssertionError(f"\nValid file(s) were not found at {parameters[file_param]} with {' or '.join(files_exist_dict[file_param][1])} extensions (using {file_param} param), needed for annotation.\n" + \
                                         f"Program was terminated.\n")
                    sys.exit(1)

            if parameters['run_liftoff'].lower().strip() == 'true' or parameters['run_repeatmasker_liftoff'].lower().strip() == 'true':
                # do specific checks for liftoff + repeatmasker liftoff (ref fasta and ref gff)
                for file_param in ['ref_fasta_path', 'ref_gff_path']:
                    try:
                        assert files_exist_dict[file_param][0] is True
                    except:
                        raise AssertionError(f"\nValid file(s) were not found at {parameters[file_param]} with {' or '.join(files_exist_dict[file_param][1])} extensions (using {file_param} param), needed for liftoff.\n" + \
                                             f"Program was terminated.\n")

    # check if submission is being ran 
    if parameters['run_submission'].lower().strip() == 'true' and parameters['annotation_entry'].lower().strip() == 'false':

        # check that a valid submission config is passed in 
        try:
            assert files_exist_dict['submission_config'][0] is True
        except:
            raise AssertionError(f"\nA valid submission config file path was not passed in. You provided the following path: {parameters['submission_config']}\n")

        # fill out the database dictionary with ones that the user wants to submit 
        databases2check = general_util.get_database_dict(parameters)

        # using the databases the user wants to submit to + files the exist = check if ready for submission + dummy file creation
        general_util.check_files_for_submission(databases2check, files_exist_dict, parameters)

    """
    # check if need to perform checks for fasta path 
    if parameters['check_fasta_paths']:
        # call the check_fasta_path function
        fasta_column = general_util.check_fasta_path (
            meta_df=meta_df,
            fasta_path=parameters['fasta_path']
        )

    # check if need to perform checks for fasta file names 
    if parameters['check_fasta_names']:
        general_util.check_fasta_names (
            meta_df=meta_df, 
            input_fasta_path=parameters['fasta_path'], 
            output_fasta_path=parameters['output_fasta_path'], 
            fasta_column=fasta_column
        )
    """


class GeneralUtil():
    def __init__(self):
        self.main_util = main_util()

    @staticmethod
    def create_dummy_files(databases4dummy, files_exist_dict, parameters):
        """ Goes through the list containing which dummy files to create and makes 
        """
        # create dictionary for iteration 
        dict_for_iter = {
            'fasta_path': '.fasta', 
            'gff_path': '.gff', 
            'meta_path': '.tsv'
        }

        # check if metadata files exists, if so, then read it in and get list of samples 
        if files_exist_dict['meta_path'][0]:
            # get the metadata files (.csv and .tsv)
            csv_meta_paths = glob.glob(os.path.join(parameters['meta_path'], '*.tsv'))
            tsv_meta_paths = glob.glob(os.path.join(parameters['meta_path'], '*.csv'))
            list_of_paths = csv_meta_paths + tsv_meta_paths

        # otherwise, need to use fasta/fastq files, get names of them and append
        else:
            # get the list of .fasta and .fastq file paths
            fasta_files = glob.glob(os.path.join(parameters['fasta_path'], '*.fasta'))
            fastq_files = glob.glob(os.path.join(parameters['fasta_path'], '*.fastq'))
            list_of_paths = fasta_files + fastq_files
        
        # use the names of new files to get the sample 
        names_of_new_files = [x.split('/')[-1].split('.')[0] for x in list_of_paths]

        # loop through the parameter names and create files accordingly 
        for file_name, ext in dict_for_iter.items():

            # create the new folder to copy over 
            folder_name = f"new_{file_name.split('_')[0]}"
            os.mkdir(f"{folder_name}", mode=0o777)

            # check if file name is in the create dummy list 
            if file_name in databases4dummy:
                # iterate through list and create files
                for new_file_name in names_of_new_files:
                    with open(f"{folder_name}/{new_file_name}{ext}", 'w') as f:
                        pass
                    f.close()
            else:
                # initialize list that you will be using to copy files over
                list_of_files = []
                if os.path.isdir(parameters[file_name]):
                    # get a list of these files
                    for extension in files_exist_dict[file_name][1]:
                        list_of_files.extend(glob.glob(os.path.join(parameters[file_name], f"*{extension}")))
                elif os.path.isfile(parameters[file_name]):
                    # place the file into a list 
                    list_of_files.append(parameters[file_name])
                # copy over each of the files
                for file2move in list_of_files:
                    final_file_name = file2move.split('/')[-1]
                    shutil.copyfile(file2move, f"{folder_name}/{final_file_name}")



    def check_files_for_submission(self, database_dict, files_exist_dict, parameters):
        """ Goes through the selected databases in the dictionary + checks that appropriate files exist + creates dummy ones
        """
        # figure out which files need to be checked based on database submissions (database dict)
        files2check = []
        for key in database_dict.keys():
            if database_dict[key][0] is True:
                files2check.extend(database_dict[key][1])
        files2check = list(set(files2check))

        # now make sure that these files are present 
        for file_name in files2check:
            try:
                assert files_exist_dict[file_name][0] is True 
            except:
                raise AssertionError(f"\nMissing files that end with {' or '.join(files_exist_dict[file_name][1])} extensions at {parameters[file_name]} needed for submission")

        # go through the updated files exist dict and for fasta, gff, or meta create dummy files if they do not exist 
        create_dummies_for = [key for key in ['fasta_path', 'gff_path', 'meta_path'] if files_exist_dict[key][0] is False]

        # call create dummy files method 
        self.create_dummy_files(create_dummies_for, files_exist_dict, parameters)

    @staticmethod
    def check_files_exist(path2check, is_dir, extensions=[]):
        """ Checks whether or not files exist within a directory with certain extensions or a single file
        """
        # Check if the path points to a directory that exists + proper files are inside
        if is_dir:
            # check the directory in general
            if not any([os.path.exists(path2check), os.path.isdir(path2check)]):
                return False
            # now check the files inside
            matching_files = []
            for extension in extensions:
                matching_files.extend(glob.glob(os.path.join(path2check, f"*{extension}")))
            if len(matching_files) == 0:
                return False

        # check that the single file exists at the path 
        else:
            # check that the file exists 
            if not os.path.exists(path2check):
                return False
            # check that file has proper extension 
            _, extension = os.path.splitext(path2check)
            if extension.lower().strip() not in extensions:
                return False 

        return True

    @staticmethod 
    def get_database_dict(parameters):
        """ Updates the dictionary containing which databases the user wants to submit to for checks 
        """
        # create the database dictionary 
        databases2check = {
            "sra": [False, ['fasta_path', 'meta_path']],
            "biosample": [False, ['meta_path']], 
            "joint_sra_biosample": [False, ['fasta_path', 'meta_path']], 
            "genbank": [False, ['fasta_path', 'gff_path']], 
            "gisaid": [False, []]
        }

        # if the submission database is 'submit', then you need to check the submission config
        if parameters['submission_database'].lower().strip() == 'submit':

            # read in the config 
            with open(parameters['config'], "r") as f:
                config_dict = yaml.safe_load(f)
            f.close()

            # go through config and populate the dictionary 
            for field in ['submit_Genbank', 'submit_GISAID', 'submit_BioSample', 'joint_SRA_BioSample_submission', 'submit_SRA']:
                
                # if it is true then update the dictionary accordingly
                if config_dict['general'][field].strip().lower() == 'true':
                    if field == 'submit_Genbank':
                        databases2check['genbank'][0] = True 
                    elif field == 'submit_GISAID':
                        databases2check['gisaid'][0] = True
                    elif field == 'submit_BioSample':
                        databases2check['biosample'][0] = True
                    elif field == 'joint_SRA_BioSample_submission':
                        databases2check['joint_sra_biosample'][0] = True
                    elif field == 'submit_SRA':
                        databases2check['sra'][0] = True
        else:
            # use the passed in submission database to update the dictionary
            if parameters['submission_database'].strip().lower() != 'all':
                # then use as the same key 
                databases2check[parameters['submission_database'].strip().lower()][0] = True
            else:
                # make all the keys equal to true 
                for database in databases2check.keys():
                    databases2check[database][0] = True

        return databases2check

    """
    @staticmethod
    def check_fasta_path(meta_df, fasta_path):
        # This checks the fasta_path passed in and the fasta paths within the metadata sheet, to make sure they are aligned

        # try finding a fasta_path field
        if 'fasta_file' in [x.strip().lower() for x in meta_df.columns]:
            fasta_column = 'fasta_file'
        elif 'fasta_file_name' in [x.strip().lower() for x in meta_df.columns]:
            fasta_column = 'fasta_file_name'
        elif 'fasta_name' in [x.strip().lower() for x in meta_df.columns]:
            fasta_column = 'fasta_name'
        elif 'fasta' in  [x.strip().lower() for x in meta_df.columns]:
            fasta_column = 'fasta'
        else:
            # try some other variant as last resort 
            # get all fields with fasta in it
            fasta_fields = [x for x in meta_df.columns if 'fasta' in x.strip().lower()]
            if fasta_fields:
                # just use the first field to get values
                fasta_column = fasta_fields[0]
            else:
                raise Exception(f"Could not find the column named fasta_file_name within metadata sheet. Please make sure it exists")

        # get these values 
        fasta_file_names = meta_df[fasta_column].to_list()
        
        # now cycle through these values and make sure they are no repeats for different sample names
        if len(set(fasta_file_names)) != len(fasta_file_names):
            raise Exception("Cannot have multiple samples in metadata sheet pointing to same FASTA file")
        
        # check all of them are located at fasta_path location
        try:
            list_of_fastas = [file for file in os.listdir(fasta_path) if file.endswith((".fasta", ".fastq"))]
        except:
            list_of_fastas = [fasta_path.split('/')[-1]]
        for name in fasta_file_names:
            try:
                assert name.strip() in list_of_fastas 
            except:
                raise AssertionError(f"Missing {name} from the directory named {fasta_path}. Only files in dir are: {list_of_fastas}")
        
        return fasta_column

    @staticmethod
    def check_fasta_names(meta_df, input_fasta_path, output_fasta_path, fasta_column):

        # Checks the name of the FASTA files to make sure it is aligned with the sample name from metadata
        # Places these modified FASTA files into new created directory

        # create the output directory
        os.system(f'mkdir -p -m777 {output_fasta_path}')

        # first check to make sure whether the input fasta path is a dir or to a single fasta / fastq
        if input_fasta_path.split('/')[-1].endswith((".fasta", ".fastq")):
            # it is a single file, need to change input_fasta_path accordingly 
            input_fasta_path = '/'.join(input_fasta_path.split('/')[:-1])

        for index, row in meta_df.iterrows():
            # get the sample name 
            sample_name = row['sample_name']
            # get the fasta file name
            fasta_file_name = row[fasta_column]

            # copy the file with the new name
            shutil.copy(f"{input_fasta_path}/{fasta_file_name}", f"{output_fasta_path}/{sample_name}.fasta")

    @staticmethod
    def create_dummy_fastas(parameters, meta_df):
        # Creates dummy fasta files in the work directory

        # create the directory for the dummy files
        os.system(f'mkdir -p -m777 {parameters['output_fasta_path']}')

        # cycle through list of meta paths and create dummy fastas based on sample in new location 
        for index, row in meta_df.iterrows():
            with open(f"{parameters['output_fasta_path']}/{row['sample_name']}.fasta", 'w') as f:
                pass
            f.close()


    def check_if_unzip(fasta_path):
        # This checks if the fasta_path points to a zipped .tz file containing individual fasta files

        # check if the fasta file needs to be unzipped first
        if fasta_path.split('/')[-1].split('.')[-1] == 'gz':
            fasta_path = self.main_util.unzip_fasta(fasta_path=fasta_path)
        fasta_names = self.main_util.get_fasta_sample_names(fasta_path=fasta_path)
        return fasta_names
        # TODO: NEED TO CHECK THIS UNZIPPED SITUATION
    """

if __name__ == "__main__":
    main()