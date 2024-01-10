#!/usr/bin/env python3

import argparse
import pandas as pd
import os 
import shutil

from annotation_utility import MainUtility as main_util


def get_args():
    parser = argparse.ArgumentParser(description="Parameters for General Utility Functions")
    parser.add_argument("--check_fasta_paths", type=bool, default=False, help="Flag whether to check FASTA paths or not")
    parser.add_argument("--check_fasta_names", type=bool, default=False, help="Flag whether to check FASTA names or not")
    parser.add_argument("--meta_path", type=str, help="Path to the input metadata file")
    parser.add_argument("--fasta_path", type=str, help="Path to the fasta file(s)")
    parser.add_argument("--output_fasta_path", type=str, help="Path to the output directory for fasta file(s)")
    return parser

def main(): 

    # get the parameters
    args = get_args().parse_args()
    parameters = vars(args)

    # instantiate the class 
    general_util = GeneralUtil()

    # convert the metadata file to pandas dataframe 
    meta_df = pd.read_excel(parameters['meta_path'], header=[1])

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


class GeneralUtil():
    def __init__(self):
        self.main_util = main_util()

    @staticmethod
    def check_fasta_path(meta_df, fasta_path):
        """ This checks the fasta_path passed in and the fasta paths within the metadata sheet, to make sure they are aligned
        """
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
        """ 
        Checks the name of the FASTA files to make sure it is aligned with the sample name from metadata
        Places these modified FASTA files into new created directory
        """
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

    def check_if_unzip(fasta_path):
        """ This checks if the fasta_path points to a zipped .tz file containing individual fasta files
        """
        # check if the fasta file needs to be unzipped first
        if fasta_path.split('/')[-1].split('.')[-1] == 'gz':
            fasta_path = self.main_util.unzip_fasta(fasta_path=fasta_path)
        fasta_names = self.main_util.get_fasta_sample_names(fasta_path=fasta_path)
        return fasta_names
        # TODO: NEED TO CHECK THIS UNZIPPED SITUATION

if __name__ == "__main__":
    main()