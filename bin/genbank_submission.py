#!/usr/bin/env python3

import ftplib
from zipfile import ZipFile
import os
import yaml
import sys
import pandas as pd
import glob
import copy
import csv

config_dict = dict()

#Initialize config file
def initialize_global_variables(config):
    if os.path.isfile(config) == False:
        print("Error: Cannot find submission config at: " + config, file=sys.stderr)
    else:
        with open(config, 'r') as f:
            global config_dict
            config_dict = yaml.safe_load(f)
        if isinstance(config_dict, dict) == False:
            print("Config Error: Config file structure is incorrect.", file=sys.stderr)
            sys.exit()

#submit files to ncbi
def submit_ftp(unique_name, config, test, overwrite):
    initialize_global_variables(config)
    if not os.path.isfile("submit.ready"):
        open("submit.ready", 'w+').close()
    create_zip(unique_name)
    try:
        #Login to ftp
        ftp = ftplib.FTP(config_dict["ncbi"]["hostname"])
        ftp.login(user=config_dict["ncbi"]["username"], passwd = config_dict["ncbi"]["password"])
        if config_dict["ncbi"]["ncbi_ftp_path_to_submission_folders"] != "":
            ftp.cwd(config_dict["ncbi"]["ncbi_ftp_path_to_submission_folders"])
        if test == False:
            ftp.cwd("Production")
        else:
            ftp.cwd("Test")
        dir = unique_name + "_genbank"
        if dir not in ftp.nlst():
            ftp.mkd(dir)
        ftp.cwd(dir)
        #Check if report.xml exists
        if "report.xml" in ftp.nlst() and overwrite == False:
            print("Submission report exists pulling down.")
            report_file = open(os.path.join(config_dict["general"]["submission_directory"], unique_name, "genbank", unique_name + "_report.xml"), 'wb')
            ftp.retrbinary('RETR report.xml', report_file.write, 262144)
            report_file.close()
        else:
            print("Submitting to Genbank.")
            res = ftp.storlines("STOR " + "submission.xml", open(os.path.join(config_dict["general"]["submission_directory"],unique_name, "genbank", "submission.xml"), 'rb'))
            if not res.startswith('226 Transfer complete'):
                print('Submission.xml upload failed.', file=sys.stderr)
            res = ftp.storbinary("STOR " + unique_name + ".zip", open(os.path.join(config_dict["general"]["submission_directory"], unique_name, "genbank", unique_name + ".zip"), 'rb'))
            if not res.startswith('226 Transfer complete'):
                print(unique_name + ".zip upload failed.", file=sys.stderr)
            res = ftp.storlines("STOR " + "submit.ready", open("submit.ready", 'rb'))
            if not res.startswith('226 Transfer complete'):
                print('submit.ready upload failed.', file=sys.stderr)
    except ftplib.all_errors as e:
        print('FTP error:', e)
        sys.exit()

#zip files for cmdline submission
def create_zip(unique_name):
    print("Zipping submission files.")
    #Zip file
    with ZipFile(os.path.join(config_dict["general"]["submission_directory"], unique_name, "genbank", unique_name + ".zip"), 'w') as zip:
        zip.write(os.path.join(config_dict["general"]["submission_directory"],unique_name, "genbank", unique_name + "_authorset.sbt"), unique_name + "_authorset.sbt")
        zip.write(os.path.join(config_dict["general"]["submission_directory"],unique_name, "genbank", unique_name + "_ncbi.fsa"), unique_name + "_ncbi.fsa")
        zip.write(os.path.join(config_dict["general"]["submission_directory"],unique_name, "genbank", unique_name + "_source.src"), unique_name + "_source.src")
        if config_dict["genbank_cmt_metadata"]["create_cmt"] == True:
            zip.write(os.path.join(config_dict["general"]["submission_directory"],unique_name, "genbank", unique_name + "_comment.cmt"), unique_name + "_comment.cmt")
