#!/usr/bin/env python3

import ftplib
import argparse
from argparse import RawTextHelpFormatter
import submission_preparation
import gisaid_submission
import genbank_submission
import biosample_sra_submission
import sys
from datetime import datetime
import requests
import os
import pandas as pd
import yaml
from Bio import SeqIO
import xml.etree.ElementTree as ET
import subprocess as subprocess
import numpy as np

# email related imports (genbank submission + table2asn for genbank_submission_type)
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

config_dict = dict()

#Initialize config file
def initialize_global_variables(config):
    if os.path.isfile(config) == False:
        print("Error: Cannot find submission config at: " + config, file=sys.stderr)
        sys.exit(1)
    else:
        with open(config, "r") as f:
            global config_dict
            config_dict = yaml.safe_load(f)
        if isinstance(config_dict, dict) == False:
            print("Config Error: Config file structure is incorrect.", file=sys.stderr)
            sys.exit(1)

# Process Biosample Report
def biosample_sra_process_report(unique_name, ncbi_sub_type):
    submission_status = ""
    submission_id = "pending"
    df = pd.read_csv(os.path.join(unique_name, "accessions.csv"), header = 0, dtype = str, sep = ",")
    if "BioSample_accession" not in df and "biosample" in ncbi_sub_type:
        df["BioSample_accession"] = ""
    if "SRA_accession" not in df and "sra" in ncbi_sub_type:
        df["SRA_accession"] = ""
    with open(os.path.join(unique_name, "biosample_sra", unique_name + "_" + ncbi_sub_type + "_report.xml"), 'r') as file:
        line = file.readline()
        while line:
            if "<SubmissionStatus status=" in line:
                submission_status = line.split("<SubmissionStatus status=\"")[-1].split("\" submission_id=")[0].split("\">")[0]
                if submission_id == "pending" and "submission_id=" in line:
                    submission_id = line.split("\" submission_id=\"")[-1].split("\" last_update=")[0]
            if "<Object target_db=\"BioSample\"" in line and "accession=" in line:
                df.loc[df.BioSample_sequence == (line.split("spuid=\"")[-1].split("\" spuid_namespace=")[0]), "BioSample_accession"] = line.split("accession=\"")[-1].split("\" spuid=")[0]
            if "<Object target_db=\"SRA\"" in line and "accession=" in line:
                df.loc[df.SRA_sequence == (line.split("spuid=\"")[-1].split("\" spuid_namespace=")[0]), "SRA_accession"] = line.split("accession=\"")[-1].split("\" spuid=")[0]
            line = file.readline()
    df.to_csv(os.path.join(unique_name, "accessions.csv"), header = True, index = False, sep = ",")
    return submission_id, submission_status

#Update log csv
def update_csv(unique_name,config,type,Genbank_submission_id=None,Genbank_submission_date=None,Genbank_status=None,SRA_submission_id=None,SRA_status=None,SRA_submission_date=None,Biosample_submission_id=None,Biosample_status=None,Biosample_submission_date=None,GISAID_submission_date=None,GISAID_submitted_total=None,GISAID_failed_total=None):
    curr_time = datetime.now()
    # get the sample name 
    sample_name = unique_name.split('.')[-1]
    if os.path.isfile(f"{unique_name}/{sample_name}_upload_log.csv"):
        df = pd.read_csv(f"{unique_name}/{sample_name}_upload_log.csv", header = 0, dtype = str, sep = ",")
    else:
        df = pd.DataFrame(columns = ["name","update_date","SRA_submission_id","SRA_submission_date","SRA_status","BioSample_submission_id","BioSample_submission_date","BioSample_status","Genbank_submission_id","Genbank_submission_date","Genbank_status","GISAID_submission_date","GISAID_submitted_total","GISAID_failed_total","directory","config","type"])
    #Check if row exists in log to update instead of write new
    if df['name'].str.contains(unique_name).any():
        df_partial = df.loc[df['name'] == unique_name]
        df.loc[df_partial.index.values, 'update_date'] = curr_time.strftime("%-m/%-d/%Y")
        df.loc[df_partial.index.values, 'directory'] = os.path.join(unique_name)
        df.loc[df_partial.index.values, 'config'] = config
        df.loc[df_partial.index.values, 'type'] = type
        if Genbank_submission_id is not None:
            df.loc[df_partial.index.values, 'Genbank_submission_id'] = Genbank_submission_id
        if Genbank_submission_date is not None:
            df.loc[df_partial.index.values, 'Genbank_submission_date'] = Genbank_submission_date
        if Genbank_status is not None:
            df.loc[df_partial.index.values, 'Genbank_status'] = Genbank_status
        if SRA_submission_id is not None:
            df.loc[df_partial.index.values, 'SRA_submission_id'] = SRA_submission_id
        if SRA_submission_date is not None:
            df.loc[df_partial.index.values, 'SRA_submission_date'] = SRA_submission_date
        if SRA_status is not None:
            df.loc[df_partial.index.values, 'SRA_status'] = SRA_status
        if Biosample_submission_id is not None:
            df.loc[df_partial.index.values, 'BioSample_submission_id'] = Biosample_submission_id
        if Biosample_submission_date is not None:
            df.loc[df_partial.index.values, 'BioSample_submission_date'] = Biosample_submission_date
        if Biosample_status is not None:
            df.loc[df_partial.index.values, 'BioSample_status'] = Biosample_status
        if GISAID_submission_date is not None:
            df.loc[df_partial.index.values, 'GISAID_submission_date'] = GISAID_submission_date
        if GISAID_submitted_total is not None:
            df.loc[df_partial.index.values, 'GISAID_submitted_total'] = GISAID_submitted_total
        if GISAID_failed_total is not None:
            df.loc[df_partial.index.values, 'GISAID_failed_total'] = GISAID_failed_total
    else:
        new_entry = {'name':unique_name,
                    'update_date':curr_time.strftime("%-m/%-d/%Y"),
                    'Genbank_submission_id':Genbank_submission_id,
                    'Genbank_submission_date':Genbank_submission_date,
                    'Genbank_status':Genbank_status,
                    'directory':os.path.join(unique_name),
                    'config':config,
                    'type':type,
                    "SRA_submission_id":SRA_submission_id,
                    "SRA_submission_date":SRA_submission_date,
                    "SRA_status":SRA_status,
                    "BioSample_submission_id":Biosample_submission_id,
                    "BioSample_submission_date":Biosample_submission_date,
                    "BioSample_status":Biosample_status,
                    "GISAID_submission_date":GISAID_submission_date,
                    "GISAID_submitted_total":GISAID_submitted_total,
                    "GISAID_failed_total":GISAID_failed_total
                    }
        # df = df.append(new_entry, ignore_index = True)
        new_df = pd.DataFrame([new_entry])
        df = pd.concat([df, new_df], axis=0, ignore_index=True)
    df.to_csv(f"{unique_name}/{sample_name}_upload_log.csv", header = True, index = False, sep = ",")


def check_if_update(df, database_name):
    not_good_vals = [None, np.nan, '', 0, '0']
    if database_name == 'GISAID':
        if (df[f"{database_name}_submitted_total"].tolist()[0] not in not_good_vals) & (df[f"{database_name}_failed_total"].tolist()[0] not in not_good_vals) & (df['type'].tolist()[0].lower().strip() != 'test'):
            update_status = True
        else:
            update_status = False
    else:
        if (df[f"{database_name}_status"].tolist()[0] not in not_good_vals) & (df[f"{database_name}_status"].tolist()[0] != 'processed-ok'):
            update_status = True
        else:
            update_status = False
    return update_status

# Update log status
def update_log(unique_name):

    # get the sample name 
    sample_name = unique_name.split('.')[-1]

    # find the upload_log file
    if os.path.isfile(f"{unique_name}/{sample_name}_upload_log.csv"):
        main_df = pd.read_csv(f"{unique_name}/{sample_name}_upload_log.csv", header = 0, dtype = str, sep = ",")
    else:
        print("Error: Either a submission has not been made or upload_log.csv has been moved from " + f"{unique_name}/{sample_name}_upload_log.csv", file=sys.stderr)
        return
        
    # get the update status for biosample, sra, and genbank
    update_status_biosample = check_if_update(df=main_df, database_name='BioSample')
    update_status_sra = check_if_update(df=main_df, database_name='SRA')
    update_status_genbank = check_if_update(df=main_df, database_name='Genbank')
    update_status_gisaid = check_if_update(df=main_df, database_name='GISAID')

    if all([update_status_biosample, update_status_sra]):
        for index, row in main_df.iterrows():
            report_generated = False
            try:
                initialize_global_variables(row["config"])
                print("\nUpdating: " + row["name"] + " BioSample/SRA")
                #Login to ftp
                ftp = ftplib.FTP(config_dict["ncbi"]["hostname"])
                ftp.login(user=config_dict["ncbi"]["username"], passwd = config_dict["ncbi"]["password"])
                if config_dict["ncbi"]["ncbi_ftp_path_to_submission_folders"] != "":
                    ftp.cwd(config_dict["ncbi"]["ncbi_ftp_path_to_submission_folders"])
                ftp.cwd(row["type"])
                submission_folder = row['name'] + "_biosample_sra"
                #Check if submission folder already exists
                if submission_folder not in ftp.nlst():
                    print("submission doesn't exist")
                    continue
                ftp.cwd(submission_folder)
                #Check if report.xml exists
                if "report.xml" in ftp.nlst():
                    print("Report exists pulling down")
                    report_file = open(os.path.join(row["name"], "biosample_sra", row["name"] + "_biosample_sra_report.xml"), 'wb')
                    ftp.retrbinary('RETR report.xml', report_file.write, 262144)
                    report_file.close()
                    report_generated = True
            except ftplib.all_errors as e:
                print('FTP error:', e)
        if report_generated == True:
            submission_id, submission_status = biosample_sra_process_report(row["name"], "biosample_sra")
            update_csv(unique_name=row['name'],config=row["config"],type=row["type"],Biosample_submission_id=submission_id,Biosample_status=submission_status,SRA_submission_id=submission_id,SRA_status=submission_status)
            print("Status: " + submission_status)
            
    #Check BioSample
    if update_status_biosample is True:
        for index, row in main_df.iterrows():
            report_generated = False
            try:
                initialize_global_variables(row["config"])
                print("\nUpdating: " + row["name"] + " BioSample")
                #Login to ftp
                ftp = ftplib.FTP(config_dict["ncbi"]["hostname"])
                ftp.login(user=config_dict["ncbi"]["username"], passwd = config_dict["ncbi"]["password"])
                if config_dict["ncbi"]["ncbi_ftp_path_to_submission_folders"] != "":
                    ftp.cwd(config_dict["ncbi"]["ncbi_ftp_path_to_submission_folders"])
                ftp.cwd(row["type"])
                submission_folder = row['name'] + "_biosample"
                #Check if submission folder already exists
                if submission_folder not in ftp.nlst():
                    print("submission doesn't exist")
                    continue
                ftp.cwd(submission_folder)
                #Check if report.xml exists
                if "report.xml" in ftp.nlst():
                    print("Report exists pulling down")
                    report_file = open(os.path.join(row["name"], "biosample_sra", row["name"] + "_biosample_report.xml"), 'wb')
                    ftp.retrbinary('RETR report.xml', report_file.write, 262144)
                    report_file.close()
                    report_generated = True
            except ftplib.all_errors as e:
                print('FTP error:', e)
        if report_generated == True:
            submission_id, submission_status = biosample_sra_process_report(row["name"], "biosample")
            update_csv(unique_name=row['name'],config=row["config"],type=row["type"],Biosample_submission_id=submission_id,Biosample_status=submission_status)
            print("Status: " + submission_status)

    #Check SRA
    if update_status_sra is True:
        for index, row in main_df.iterrows():
            report_generated = False
            try:
                initialize_global_variables(row["config"])
                print("\nUpdating: " + row["name"] + " SRA")
                #Login to ftp
                ftp = ftplib.FTP(config_dict["ncbi"]["hostname"])
                ftp.login(user=config_dict["ncbi"]["username"], passwd = config_dict["ncbi"]["password"])
                if config_dict["ncbi"]["ncbi_ftp_path_to_submission_folders"] != "":
                    ftp.cwd(config_dict["ncbi"]["ncbi_ftp_path_to_submission_folders"])
                ftp.cwd(row["type"])
                submission_folder = row['name'] + "_sra"
                #Check if submission folder already exists
                if submission_folder not in ftp.nlst():
                    print("submission doesn't exist")
                    continue
                ftp.cwd(submission_folder)
                #Check if report.xml exists
                if "report.xml" in ftp.nlst():
                    print("Report exists pulling down")
                    report_file = open(os.path.join(row["name"], "biosample_sra", row["name"] + "_sra_report.xml"), 'wb')
                    ftp.retrbinary('RETR report.xml', report_file.write, 262144)
                    report_file.close()
                    report_generated = True
            except ftplib.all_errors as e:
                print('FTP error:', e)
        if report_generated == True:
            submission_id, submission_status = biosample_sra_process_report(row["name"], "sra")
            update_csv(unique_name=row['name'],config=row["config"],type=row["type"],SRA_submission_id=submission_id,SRA_status=submission_status)
            print("Status: " + submission_status)

    #Check Genbank
    if update_status_genbank is True:
        for index, row in main_df.iterrows():
            report_generated = False
            try:
                initialize_global_variables(row["config"])
                if config_dict["general"]["genbank_submission_type"].lower() == "ftp":
                    print("\nUpdating: " + row["name"] + " Genbank")
                    #Login to ftp
                    ftp = ftplib.FTP(config_dict["ncbi"]["hostname"])
                    ftp.login(user=config_dict["ncbi"]["username"], passwd = config_dict["ncbi"]["password"])
                    if config_dict["ncbi"]["ncbi_ftp_path_to_submission_folders"] != "":
                        ftp.cwd(config_dict["ncbi"]["ncbi_ftp_path_to_submission_folders"])
                    ftp.cwd(row["type"])
                    submission_folder = row['name'] + "_genbank"
                    #Check if submission folder already exists
                    if submission_folder not in ftp.nlst():
                        print("submission doesn't exist")
                        continue
                    ftp.cwd(submission_folder)
                    #Check if report.xml exists
                    if "report.xml" in ftp.nlst():
                        print("Report exists pulling down")
                        report_file = open(os.path.join(row["name"], "genbank", row["name"] + "_report.xml"), 'wb')
                        ftp.retrbinary('RETR report.xml', report_file.write, 262144)
                        report_file.close()
                        report_generated = True
            except ftplib.all_errors as e:
                print('FTP error:', e)
            if report_generated == True:
                submission_id, submission_status = genbank_process_report(row["name"])
                update_csv(unique_name=row['name'],config=row["config"],type=row["type"],Genbank_submission_id=submission_id,Genbank_status=submission_status)
                print("Status: " + submission_status)

    #Check GISAID
    if update_status_gisaid is True:
        for index, row in main_df.iterrows():
            initialize_global_variables(row["config"])
            if config_dict["general"]["submit_GISAID"] == True:
                print("\nSubmitting to GISAID: " + row["name"])
                submit_gisaid(unique_name=row["name"], config=row["config"], test=row["type"])

#Read output log from gisaid submission script
def read_log(unique_name, file):
    if os.path.exists(file):
        with open(file) as f:
            data = json.load(f)
        number_submitted = 0
        number_failed = 0
        already_submitted = []
        for i in data:
            #Sequence successfully uploaded
            if i["code"] == "upload_count":
                number_submitted = int(i["msg"].strip().split("uploaded: ")[1])
            #Sequence failed upload
            elif i["code"] == "failed_count":
                number_failed = int(i["msg"].strip().split("failed: ")[1])
            #Correct number of successfully uploaded for if a sequence fails for already existing
            elif (i["code"] == "validation_error") and ("\"covv_virus_name\": \"already exists\"" in i["msg"]):
                already_submitted.append(i["msg"].split("; validation_error;")[0])
            elif i["code"] == "epi_isl_id":
                continue
        clean_failed_log(unique_name, number_failed, already_submitted)
        number_failed = number_failed - len(already_submitted)
        number_submitted = number_submitted + len(already_submitted)
        return str(number_submitted), str(number_failed)
    else:
        return "error", "error"

#Cleans failed meta log if some of the submissions are just already submitted or
#Removes file if it is empty
def clean_failed_log(unique_name, number_failed, already_submitted):
    if number_failed == 0 or number_failed == len(already_submitted):
        if os.path.exists(os.path.join(unique_name, "gisaid", unique_name + "_failed_meta.csv")):
            print("No failed sequences.\nCleaning up files.")
            os.remove(os.path.join(unique_name, "gisaid", unique_name + "_failed_meta.csv"))
    else:
        df = pd.read_csv(os.path.join(unique_name, "gisaid", unique_name + "_failed_meta.csv"), header = 0, dtype = str)
        clean_df = df[~df.covv_virus_name.isin(already_submitted)]
        clean_df.to_csv(os.path.join(unique_name, "gisaid", unique_name + "_failed_meta.csv"), header = True, index = False)
        print("Error: Sequences failed please check: " + os.path.join(unique_name, "gisaid", unique_name + ".log"))

#Pull down report files
def pull_report_files(unique_name, files):
    api_url = config_dict["ncbi"]["api_url"]
    for item in files.keys():
        r = requests.get(api_url.replace("FILE_ID", files[item]), allow_redirects=True)
        open(os.path.join(unique_name, "genbank", unique_name + "_" + item), 'wb').write(r.content)

def submit_genbank(unique_name, config, test, overwrite, send_email):
    prepare_genbank(unique_name)
    if config_dict["general"]["genbank_submission_type"].lower() == "ftp":
        if test.lower() == "production" or test.lower() == 'prod':
            test_type = False
        else:
            test_type = True
        genbank_submission.submit_ftp(unique_name=unique_name, config=config, test=test_type, overwrite=overwrite)
        curr_time = datetime.now()
        update_csv(unique_name=unique_name, config=config, type=test, Genbank_submission_id="submitted", Genbank_submission_date=curr_time.strftime("%-m/%-d/%Y"), Genbank_status="submitted")
    elif config_dict["general"]["genbank_submission_type"].lower() == "table2asn":
        if config_dict["genbank_cmt_metadata"]["create_cmt"] == True:
            command = (os.path.join(os.path.dirname(os.path.abspath(__file__)), "table2asn") + " " + config_dict["ncbi"]["tbl2asn_flags"] +
                " -t " + os.path.join(unique_name, "genbank", unique_name + "_authorset.sbt") +
                " -w " + os.path.join(unique_name, "genbank", unique_name + "_comment.cmt") +
                " -i " + os.path.join(unique_name, "genbank", unique_name + "_ncbi.fsa") +
                " -src-file " + os.path.join(unique_name, "genbank", unique_name + "_source.src") +
                " -f " + os.path.join(unique_name, "genbank", unique_name + ".gff"))
            cmt = pd.read_csv(os.path.join(unique_name, "genbank", unique_name + "_comment.cmt"), header = 0, sep = "\t")
            cmt.to_csv(os.path.join(unique_name, "genbank", unique_name + "_comment.cmt"), header = True, index = False, sep = "\t")
        else:
            command = (os.path.join(os.path.dirname(os.path.abspath(__file__)), "table2asn") + " " + config_dict["ncbi"]["tbl2asn_flags"] +
                " -t " + os.path.join(unique_name, "genbank", unique_name + "_authorset.sbt") +
                " -i " + os.path.join(unique_name, "genbank", unique_name + "_ncbi.fsa") +
                " -f " + os.path.join(unique_name, "genbank", unique_name + ".gff"))
        proc = subprocess.run(command, env = os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, shell=True)
        print(proc.args)
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr)
            # sys.exit(1)
        
        # check if the send_submission_email param is true or false (if true, send email based on config)
        if send_email.lower().strip() == 'true':

            # acquire / place necessary information into dict for message
            msg = MIMEMultipart('multipart')
            msg['Subject'] = unique_name + " table2asn"
            msg['From'] = "submission_prep@cdc.gov"
            recipients = [config_dict['general'][field] for field in config_dict['general'].keys() if 'notif_email_recipient' in field]

            # check that the recipients is not empty, if it is then do not send email
            if recipients:
                # join the recipients together via comma 
                if len(recipients) > 1:
                    msg['To'] = ", ".join(recipients)
                else:
                    msg['To'] = recipients[0]

                # attach some information to the email
                with open(os.path.join(unique_name, "genbank", unique_name + "_ncbi.sqn"), 'rb') as file_input:
                    part = MIMEApplication(file_input.read(), Name=unique_name + "_ncbi.sqn")
                    part['Content-Disposition'] = "attachment; filename=" + unique_name + "_ncbi.sqn"
                    msg.attach(part)
                file_input.close()

                # send out the email
                s = smtplib.SMTP('localhost')
                s.sendmail(msg['From'], msg['To'], msg.as_string())

        curr_time = datetime.now()
        update_csv(unique_name=unique_name, config=config, type=test, Genbank_submission_id="table2asn", Genbank_submission_date=curr_time.strftime("%-m/%-d/%Y"), Genbank_status="table2asn")
    else:
        print("Error: Unknown value for (general: genbank_submission_type) in config file. Must be FTP for automatic FTP upload or table2asn for email upload.")
        sys.exit(1)

def submit_gisaid(unique_name, config, test):
    if config_dict["gisaid"]["Update_sequences_on_Genbank_auto_removal"] == True and config_dict["ncbi"]["Genbank_auto_remove_sequences_that_fail_qc"] == True:
        prepare_gisaid(unique_name)
    if test.lower() == "production" or test.lower() == 'prod':
        test_type = False
    else:
        test_type = True
    gisaid_submission.run_uploader(unique_name=unique_name, config=config, test=test_type)
    submitted, failed = read_log(unique_name, os.path.join(unique_name, "gisaid", unique_name + ".log"))
    curr_time = datetime.now()
    update_csv(unique_name=unique_name, config=config, type=test, GISAID_submission_date=curr_time.strftime("%-m/%-d/%Y"),GISAID_submitted_total=submitted,GISAID_failed_total=failed)

#Read xml report and check status of report
def genbank_process_report(unique_name):
    tree = ET.parse(os.path.join(unique_name, "genbank", unique_name + "_report.xml"))
    root = tree.getroot()
    if root.get('submission_id') == None:
        return "error", "error"
    files = dict()
    submission_id = ""
    status = ""
    for elem in tree.iter():
        if "submission_id" in elem.attrib.keys() and submission_id == "":
            submission_id = elem.attrib["submission_id"]
        if "status" in elem.attrib.keys() and status == "":
            if elem.attrib["status"] == "submitted":
                status = "submitted"
            elif elem.attrib["status"] == "queued":
                status = "queued"
            elif elem.attrib["status"] == "processing":
                status = "processing"
            elif elem.attrib["status"] == "processed-ok":
                status = "processed-ok"
            else:
                print("Possible Error check " + os.path.join(unique_name, "genbank", unique_name + "_report.xml"))
                status = "error"
        if "file_id" in elem.attrib.keys():
            files[elem.attrib['file_path']] = elem.attrib['file_id']
    if len(files) != 0:
        pull_report_files(unique_name, files)
    return submission_id, status

#Add biosample/SRA data to genbank submissions
def prepare_genbank(unique_name):
    accessions = pd.read_csv(os.path.join(unique_name, "accessions.csv"), header = 0, dtype=str, sep=',')
    df = pd.read_csv(os.path.join(unique_name, "genbank", unique_name + "_source.src"), header = 0, dtype=str, sep='\t')
    if config_dict["ncbi"]['BioProject'] != "":
        df['BioProject'] = config_dict["ncbi"]['BioProject']
    df = df.merge(accessions, how='left', left_on='sequence_ID', right_on='Genbank_sequence')
    potential_columns = ["SRA_sequence", "BioSample_sequence", "Genbank_sequence", "Genbank_accession", "GISAID_sequence"]
    drop_columns = []
    for col in potential_columns:
        if col in df:
            drop_columns.append(col)
    df = df.drop(columns=drop_columns)
    if "BioSample_accession" not in df and "SRA_accession" not in df:
        return
    df = df.rename(columns={"BioSample_accession": "BioSample", "SRA_accession": "SRA"})
    if "BioSample" in df:
        df["BioSample"] = df["BioSample"].fillna("")
    if "SRA" in df:
        df["SRA"] = df["SRA"].fillna("")
    col_names = df.columns.values.tolist()
    col_names.remove("sequence_ID")
    col_names.insert(0, "sequence_ID")
    df = df[col_names]
    df.to_csv(os.path.join(unique_name, "genbank", unique_name + "_source.src"), header = True, index = False, sep = '\t')

# If removing GISAID sequences based on Genbank Auto-remove
def prepare_gisaid(unique_name):
    if config_dict["gisaid"]["Update_sequences_on_Genbank_auto_removal"] != True:
        return
    accessions = pd.read_csv(os.path.join(unique_name, "accessions.csv"), header = 0, dtype=str, sep=',')
    if "Genbank_accession" not in accessions:
        return
    df = pd.read_csv(os.path.join(unique_name, "gisaid", unique_name + "_gisaid.csv"), header = 0, dtype=str, sep=',')
    df = df.merge(accessions, how='left', left_on='GISAID_sequence', right_on='covv_virus_name')
    potential_columns = ["SRA_sequence", "BioSample_sequence", "Genbank_sequence", "BioSample_accession", "SRA_accession", "GISAID_sequence", "Genbank_accession"]
    drop_columns = []
    for col in potential_columns:
        if col in df:
            drop_columns.append(col)
    df = df.dropna(subset=["Genbank_accession"])
    df = df[df.Genbank_accession != ""]
    df = df.drop(columns=[drop_columns])
    shutil.copy2(os.path.join(unique_name, "gisaid", unique_name + "_gisaid.csv"), os.path.join(unique_name, "gisaid", "old_" + unique_name + "_gisaid.csv"))
    df.to_csv(os.path.join(unique_name,"gisaid",unique_name + "_gisaid.csv"), na_rep="Unknown", index = False, header = True, quoting=csv.QUOTE_ALL)
    keep_records = []
    with open(os.path.join(unique_name, "gisaid", unique_name + "_gisaid.fsa"), "r") as fsa:
        records = SeqIO.parse(fsa, "fasta")
        for record in records:
            if record.id in df["covv_virus_name"]:
                keep_records.append(record)
    shutil.copy2(os.path.join(unique_name,"gisaid",unique_name + "_gisaid.fsa"), os.path.join(unique_name,"gisaid", "old_" + unique_name + "_gisaid.fsa"))
    with open(os.path.join(unique_name,"gisaid",unique_name + "_gisaid.fsa"), "w+") as fasta_file:
        SeqIO.write(keep_records, fasta_file, "fasta")

# For submitting when SRA/Biosample have to be split due to errors
def submit_biosample_sra(unique_name, config, test, ncbi_sub_type, overwrite):

    if test.lower() == "production" or test.lower() == 'prod':
        test_type = False
    else:
        test_type = True

    biosample_sra_submission.submit_ftp(unique_name=unique_name, ncbi_sub_type=ncbi_sub_type, config=config, test=test_type, overwrite=overwrite)
    
    curr_time = datetime.now()
    if ncbi_sub_type == "biosample_sra":
        update_csv(unique_name=unique_name,config=config,type=test,Biosample_submission_id="submitted",Biosample_status="submitted",Biosample_submission_date=curr_time.strftime("%-m/%-d/%Y"),SRA_submission_id="submitted",SRA_status="submitted",SRA_submission_date=curr_time.strftime("%-m/%-d/%Y"))
    elif ncbi_sub_type == "biosample":
        update_csv(unique_name=unique_name,config=config,type=test,Biosample_submission_id="submitted",Biosample_status="submitted",Biosample_submission_date=curr_time.strftime("%-m/%-d/%Y"))
    elif ncbi_sub_type == "sra":
        update_csv(unique_name=unique_name,config=config,type=test,SRA_submission_id="submitted",SRA_status="submitted",SRA_submission_date=curr_time.strftime("%-m/%-d/%Y"))

# Start submission into automated pipeline
def start_submission(unique_name, config, test, overwrite, send_email):
    if config_dict["general"]["submit_BioSample"] == True and config_dict["general"]["submit_SRA"] == True and config_dict["general"]["joint_SRA_BioSample_submission"] == True:
        submit_biosample_sra(unique_name, config, test, "biosample_sra", overwrite)
    elif config_dict["general"]["submit_BioSample"] == True and config_dict["general"]["submit_SRA"] == True and config_dict["general"]["joint_SRA_BioSample_submission"] == False:
        submit_biosample_sra(unique_name, config, test, "biosample", overwrite)
        submit_biosample_sra(unique_name, config, test, "sra", overwrite)
    elif config_dict["general"]["submit_BioSample"] == True:
        submit_biosample_sra(unique_name, config, test, "biosample", overwrite)
    elif config_dict["general"]["submit_SRA"] == True:
        submit_biosample_sra(unique_name, config, test, "sra", overwrite)
    elif config_dict["general"]["submit_Genbank"] == True:
        submit_genbank(unique_name=unique_name, config=config, test=test, overwrite=overwrite, send_email=send_email)
    elif config_dict["general"]["submit_GISAID"] == True:
        submit_gisaid(unique_name=unique_name, config=config, test=test)
    """
    # go through the different database submissions and call the appropriate functions
    if config_dict["general"]["submit_BioSample"] == True and config_dict["general"]["submit_SRA"] == True and config_dict["general"]["joint_SRA_BioSample_submission"] == True:
        submit_biosample_sra(unique_name, config, test, "biosample_sra", overwrite)

    elif config_dict["general"]["submit_BioSample"] == True:
        submit_biosample_sra(unique_name, config, test, "biosample", overwrite)

    elif config_dict["general"]["submit_SRA"] == True:
        submit_biosample_sra(unique_name, config, test, "sra", overwrite)

    elif config_dict["general"]["submit_Genbank"] == True:
        submit_genbank(unique_name=unique_name, config=config, test=test, overwrite=overwrite)

    elif config_dict["general"]["submit_GISAID"] == True:
        submit_gisaid(unique_name=unique_name, config=config, test=test)
    """

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unique_name", help='unique identifier')
    parser.add_argument("--config", help='config file for submission')
    parser.add_argument("--send_email", help='whether or not to send email')
    parser.add_argument("--req_col_config", help='config file for required columns in yaml')
    parser.add_argument("--test_or_prod", help='Perform test submission or prod')
    parser.add_argument("--overwrite", default=False, help='Overwrite existing submission on NCBI')
    parser.add_argument("--metadata", help="Metadata file")
    parser.add_argument("--gff", help="GFF file for annotation")
    parser.add_argument("--fasta", help="Fasta file")
    parser.add_argument("--command", default='submit', help="whether to submit or not" \
                        "[submit, genbank, biosample, biosample_sra, sra, gisaid, update_submissions, or all]")
    return parser


def main():

    # get the parameters 
    args = get_args().parse_args()

    # get the sample name to append the unique name 
    if args.command != 'update_submissions':
        args.unique_name = args.unique_name + '.' + str(args.metadata.split('/')[-1].split('.')[0])
        try:
            assert all([args.unique_name, args.config, args.req_col_config, args.test_or_prod, args.metadata, args.gff, args.fasta, args.command, args.send_email])
        except AssertionError:
            raise AssertionError(f"Missing one of the following required arguments:  \
                                [unique_Name, config, req_col_config, test_or_prod, metadata, gff, fasta, command]")

    # initialize the global variables from the config (gets the config dict)
    initialize_global_variables(args.config)

    # go through and change the config to match the passed in database submission
    database_mappings = {
        'genbank': 'submit_Genbank', 
        'sra': 'submit_SRA', 
        'gisaid': 'submit_GISAID', 
        'biosample': 'submit_BioSample',
        'joint_sra_biosample': 'joint_SRA_BioSample_submission'
    }

    if args.command != 'submit':
        for key, value in database_mappings.items():
            if args.command == key or args.command == 'all':
                config_dict['general'][value] = True
            else:
                config_dict['general'][value] = False
    
    if args.command == 'joint_sra_biosample':
        config_dict['general']['submit_SRA'] = True
        config_dict['general']['submit_BioSample'] = True

    if args.command != 'update_submissions':
        submission_preparation.process_submission(args.unique_name, args.fasta, args.metadata, args.gff, args.config, args.req_col_config, config_dict)
        start_submission(args.unique_name, args.config, args.test_or_prod, args.overwrite, args.send_email)
    
    elif args.command == 'update_submissions':
        update_log(args.unique_name)

    else:
        print ("Invalid option")
        parser.print_help()


if __name__ == "__main__":
    main()
