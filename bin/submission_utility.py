#!/usr/bin/env python3

import time 
import argparse
import os
import glob
import yaml
import shutil
import pandas as pd
import sys
import traceback


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
    parser.add_argument("--merge_upload_log", type=str, default='false', help='Whether to create an upload_log file for submission or not')
    parser.add_argument("--batch_name", type=str, help='Name for batch')
    return parser


def main():
    # get the parameters 
    args = get_args().parse_args()
    parameters = vars(args)

    # initialize the necessary classes
    util = Utility()
    checks = AssertChecks()
    
    # =================================================================================================================
    #                              CHECK IF YOU NEED TO WAIT... IF SO, THEN WAIT
    # =================================================================================================================
    
    # check if you need to wait or not
    if parameters['wait'].lower().strip() == 'true':
        util.actually_wait (
            time_2_wait=int(parameters['wait_time'])
        )

    # =================================================================================================================
    #                    CHECK IF YOU NEED TO CREATE AN UPLOAD LOG FILE FOR SUBMISSION
    # =================================================================================================================

    if parameters['merge_upload_log'].lower().strip() == 'true':

        expected_cols = ["name", "update_date", "SRA_submission_id", "SRA_submission_date", "SRA_status", "BioSample_submission_id",
                     "BioSample_submission_date", "BioSample_status", "Genbank_submission_id", "Genbank_submission_date", "Genbank_status",
                     "GISAID_submission_date", "GISAID_submitted_total", "GISAID_failed_total", "directory", "config", "type"]

        # get all paths to directories within working directory containing batch name
        current_dir = os.getcwd()
        upload_log_dirs = [x for x in os.listdir(current_dir) if f"{parameters['batch_name']}." in x]

        # cycle through the directories and add contents from upload log files to a merged dataframe
        merged_df = pd.DataFrame(columns=expected_cols)
        for log_dir in upload_log_dirs:
            # get sample information and log file information
            sample_name = log_dir.split('.')[-1]
            log_file_name = f"{sample_name}_upload_log.csv"
            if log_file_name in os.listdir(log_dir):
                # open the upload log file and save csv contents
                log_data = pd.read_csv(f"{log_dir}/{log_file_name}")
                # check some upload log stuff 
                checks.check_upload_log(log_data=log_data, expected_cols=expected_cols)
                # merge the concatenated df with this upload log file
                merged_df = pd.concat([merged_df, log_data], ignore_index=True)
            else:
                pass
        
        # write the final upload log file
        merged_df.to_csv('upload_log.csv', index=False)

    # =================================================================================================================
    #                        CHECK IF NEED TO CREATE SUBMISSION OUTPUT DIR FOR ENTRYPOINT
    # =================================================================================================================
    
    if parameters['prep_submission_entry'].lower().strip() == 'true' and parameters['update_entry'].lower().strip() == 'false':
        
        # check the database being submitted to and adjust file check/copy accordingly 
        if len(glob.glob(f"{parameters['gff_path']}/*.gff")) == 0:
            parameters = util.check_database (
                parameters=parameters
            )

        # cycle through the different input files for submission and copy into work directory
        for file_type, key in zip(['tsv', 'fasta', 'gff'], ['meta_path', 'fasta_path', 'gff_path']):
            # make the directory to copy over the files to 
            os.mkdir(f"{file_type}_submit_entry", mode=0o777)
            # copy over the files to this directory
            for file in glob.glob(f"{parameters[key]}/*.{file_type}"):
                file_name = file.split('/')[-1]
                shutil.copyfile(file, f"{file_type}_submit_entry/{file_name}")

    elif parameters['prep_submission_entry'].lower().strip() == 'true' and parameters['update_entry'].lower().strip() == 'true':
        # make the new directory to copy over the files to
        os.mkdir(f"update_entry", mode=0o777)
        # copy over the processed files
        for folder in glob.glob(f"{parameters['processed_samples']}/*"):
            # get the dir name 
            dir_name = folder.split('/')[-1]
            # copy over the files 
            if dir_name != 'upload_log.csv':
                shutil.copytree(folder, f"update_entry/{dir_name}")
    

class Utility():
    def __init__(self):
        """
        """
    
    @staticmethod 
    def actually_wait(time_2_wait):
        time.sleep(time_2_wait)

    @staticmethod 
    def check_database(parameters):
        cleaned_name = parameters['database'].lower().strip()

        # read the submission config file in if submit was used for database
        if cleaned_name == 'submit':
            with open(parameters['config'], "r") as f:
                config_dict = yaml.safe_load(f)
            f.close()
            # cycle through the databases to check if only 'sra' was selected
            create_dummy_files = True
            for field in ['submit_Genbank', 'submit_GISAID', 'submit_BioSample', 'joint_SRA_BioSample_submission']:
                if config_dict['general'][field] == True:
                    create_dummy_files = False
                    break

        # check whether to create dummy files or not, if so, then do it 
        if cleaned_name == 'sra' or create_dummy_files == True:
            # for SRA specifically, easiest to just create dummy files
            os.mkdir(f"dummy_gffs", mode=0o777)
            for x in range(len(glob.glob(f"{parameters['meta_path']}/*.tsv"))):
                with open(f"dummy_gffs/gff_{x}.gff", 'w') as f:
                    pass
            # set the gff path to the dummy files created
            parameters['gff_path'] = 'dummy_gffs'
        else:
            raise ValueError(f"Missing required GFF files at the provided path encoded by submission_only_gff in params: {parameters['gff_path']}")
    
        return parameters 


class AssertChecks():
    def __init__(self):
        """
        """
    
    def check_upload_log(self, log_data, expected_cols):
        try:
            assert len(log_data.columns) != 0
            assert sorted(set(log_data.columns)) == sorted(set(expected_cols))
            assert len(log_data.index) != 0
        except AssertionError:
            handle_stacktrace()

    @staticmethod
    def handle_stacktrace():
        """ Generates, makes verbose, and cleans up the stack trace generated from assertion error
        """
        _, _, tb = sys.exc_info()
        traceback.print_tb(tb) # Fixed format
        tb_info = traceback.extract_tb(tb)
        filename, line, func, text = tb_info[-1]
        print('An error occurred on line {} in the following statement: {}'.format(line, text))
        sys.exit(1)


if __name__ == "__main__":
    main()