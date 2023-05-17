#!/usr/bin/env python3

import time 
import argparse
import os
import glob
import yaml
import shutil


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait", type=str, default='false', help='Flag to wait or not')
    parser.add_argument("--database", type=str, help='Certain database to submit to')
    parser.add_argument("--wait_time", type=str, help='Length of time to wait in seconds')
    parser.add_argument("--config", type=str, help='Name of submission config file')
    parser.add_argument("--prep_submission_entry", type=str, default='false', help='Whether or not to create directory for submission files')
    parser.add_argument("--meta_path", type=str, help='Path to the metadata files for submission entrypoint')
    parser.add_argument("--fasta_path", type=str, help='Path to the fasta files for submission entrypoint')
    parser.add_argument("--gff_path", type=str, help='Path to the gff files for submission entrypoint')
    parser.add_argument("--update_entry", type=str, help='Whether or not it is update submission entry')
    parser.add_argument("--processed_samples", type=str, help='Path to processed samples')
    return parser


def main():
    # get the parameters 
    args = get_args().parse_args()
    parameters = vars(args)

    # initialize the utility class 
    util = Utility()
    
    # =================================================================================================================
    #                              CHECK IF YOU NEED TO WAIT... IF SO, THEN WAIT
    # =================================================================================================================
    
    # check if you need to wait or not
    if parameters['wait'].lower().strip() == 'true':
        util.actually_wait (
            time_2_wait=int(parameters['wait_time'])
        )

    # =================================================================================================================
    #                        CHECK IF NEED TO CREATE SUBMISSION OUTPUT DIR FOR ENTRYPOINT
    # =================================================================================================================
    
    if parameters['prep_submission_entry'].lower().strip() == 'true' and parameters['update_entry'].lower().strip() == 'false':
        
        # check the database being submitted to and adjust file check/copy accordingly 
        util.check_database (
            database_name=parameters['database'], 
            config=parameters['config']
        )

        # cycle through the different input files for submission and copy into work directory
        for file_type, key in zip(['tsv', 'fasta', 'gff'], ['meta_path', 'fasta_path', 'gff_path']):
            # make the directory to copy over the files to 
            os.mkdir(f"{file_type}_submit_entry", mode=0o777)
            # copy over the files to this directory
            for file in glob.glob(f"{parameters[key]}/*.{file_type}"):
                file_name = file.split('/')[-1]
                shutil.copyfile(file, f"{file_type}_submit_entry/{file_name}")
    else:
        # make the new directory to copy over the files to
        os.mkdir(f"update_entry", mode=0o777)
        # copy over the processed files
        for folder in glob.glob(f"{parameters['processed_samples']}/*"):
            # get the dir name 
            dir_name = folder.split('/')[-1]
            # copy over the files 
            shutil.copytree(folder, f"update_entry/{dir_name}")
    

class Utility():
    def __init__(self):
        """
        """
    
    @staticmethod 
    def actually_wait(time_2_wait):
        time.sleep(time_2_wait)

    @staticmethod 
    def check_database(database_name, config):
        cleaned_name = database_name.lower().strip()
        if cleaned_name == 'sra':
            # for SRA specifically, easiest to just create dummy files
            os.mkdir(f"dummy_gffs", mode=0o777)
                
            """
            """



if __name__ == "__main__":
    main()