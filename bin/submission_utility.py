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
    parser.add_argument("--check_submission_config", type=str, default='false', help='Flag for checking whether or not the submission output paths are aligned')
    parser.add_argument("--database", type=str, help='Certain database to submit to')
    parser.add_argument("--wait_time", type=str, help='Length of time to wait in seconds')
    parser.add_argument("--config", type=str, help='Name of submission config file')
    parser.add_argument("--submission_outputs", type=str, help='Path to the submission outputs')
    parser.add_argument("--prep_submission_entry", type=str, default='false', help='Whether or not to create directory for submission files')
    parser.add_argument("--meta_path", type=str, help='Path to the metadata files for submission entrypoint')
    parser.add_argument("--fasta_path", type=str, help='Path to the fasta files for submission entrypoint')
    parser.add_argument("--gff_path", type=str, help='Path to the gff files for submission entrypoint')
    parser.add_argument("--update_entry", type=str, help='Whether or not it is update submission entry')
    parser.add_argument("--batch_name", type=str, help='Name of the batch prefix')
    parser.add_argument("--processed_samples", type=str, help='Path to processed samples')
    parser.add_argument("--merge_upload_log", type=str, default='false', help='Whether to create an upload_log file for submission or not')
    return parser


def main():
    # get the parameters 
    args = get_args().parse_args()
    parameters = vars(args)
    
    # =================================================================================================================
    #                              CHECK IF YOU NEED TO WAIT... IF SO, THEN WAIT
    # =================================================================================================================
    # check if you need to wait or not
    if parameters['wait'].lower().strip() == 'true':
        time_2_wait = int(parameters['wait_time'])
        time.sleep(time_2_wait)

    # =================================================================================================================
    #                    CHECK IF YOU NEED TO CREATE AN UPLOAD LOG FILE FOR SUBMISSION
    # =================================================================================================================
    if parameters['merge_upload_log'].lower().strip() == 'true':
        # get all paths to directories within working directory containing batch name
        current_dir = os.getcwd()
        upload_log_dirs = [x for x in os.listdir(current_dir) if f"{parameters['batch_name']}." in x]
        # cycle through the directories and add contents from upload log files to new log file
        with open('upload_log.csv', 'w') as f:
            for log_dir in upload_log_dirs:
                sample_name = log_dir.split('.')[-1]
                log_file_name = f"{sample_name}_upload_log.csv"
                #if log_file_name in os.listdir():
                # open the upload log file and save csv contents
                log_data = pd.read_csv(f"{log_dir}/{log_file_name}")
                # check some upload log stuff 
                try:
                    assert len(log_data.columns) != 0
                    assert sorted(set(log_data.columns)) == sorted(set(["name", "update_date", "SRA_submission_id", "SRA_submission_date", 
                                                        "SRA_status", "BioSample_submission_id", "BioSample_submission_date",
                                                        "BioSample_status", "Genbank_submission_id", "Genbank_submission_date",
                                                        "Genbank_status", "GISAID_submission_date", "GISAID_submitted_total", 
                                                        "GISAID_failed_total", "directory", "config", "type"]))
                    assert len(log_data.index) != 0
                except AssertionError:
                    handle_stacktrace()
                # 
                #else:
                    #pass

    # =================================================================================================================
    #                        CHECK IF NEED TO CREATE SUBMISSION OUTPUT DIR FOR ENTRYPOINT
    # =================================================================================================================
    if parameters['prep_submission_entry'].lower().strip() == 'true' and parameters['update_entry'].lower().strip() == 'false':
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
            shutil.copytree(folder, f"update_entry/{dir_name}")


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