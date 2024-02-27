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
    
    # =================================================================================================================
    #                              CHECK IF YOU NEED TO WAIT... IF SO, THEN WAIT
    # =================================================================================================================
    
    # check if you need to wait or not
    if parameters['wait'].lower().strip() == 'true':
        util.actually_wait (
            time_2_wait=int(parameters['wait_time'])
        )
   

class Utility():
    def __init__(self):
        """
        """
    
    @staticmethod 
    def actually_wait(time_2_wait):
        time.sleep(time_2_wait)

if __name__ == "__main__":
    main()