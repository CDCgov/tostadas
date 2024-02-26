#!/usr/bin/env python3
 
import argparse
import os
import pandas as pd
import sys

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--submission_dir", type=str, default='false', help='Directory to submission log files')
    return parser

def main():
    # get the parameters 
    args = get_args().parse_args()
    parameters = vars(args)

    print(f"current dir is {parameters['submission_dir']}")

    # Get all files with 'submission_log.csv' in the current working directory
    log_files = [file for file in os.listdir(parameters['submission_dir']) if file.endswith('_submission_log.csv')]

    # Initialize an empty list to store dataframes
    log_dfs = []

    # Read each log file into a pandas dataframe and append it to the list
    for submission_log_file in log_files:
        if os.path.isfile(submission_log_file):
            df = pd.read_csv(submission_log_file, header = 0, dtype = str, engine = "python", encoding="utf-8", index_col=False)
            log_dfs.append(df)
        else:
            print("Cannot find a submission log at " + submission_log_file, file=sys.stderr)
            sys.exit(1)

    # Concatenate all dataframes in the list into one large dataframe
    merged_df = pd.concat(log_dfs)
    print("Individual sample log files merged")

    # Write the combined dataframe to the current working directory
    merged_df.to_csv('submission_log.csv', index=False)
    print("Final submission log file created successfully!")

if __name__ == "__main__":
    main()