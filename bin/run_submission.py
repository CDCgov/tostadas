#!/usr/bin/env python3

import argparse
import os
import glob
import subprocess
import yaml
 
def get_args():
    """ All potential arguments passed in through command line
    """ 
    parser = argparse.ArgumentParser()
    parser.add_argument("--sra", required=False, type=str, help='Submit to SRA database')
    parser.add_argument("--genbank", required=False, type=str, help='Submit to Genbank database')
    parser.add_argument("--gisaid", required=False, type=str, help='Submit to GISAID database')
    parser.add_argument("--biosample", required=False, type=str, help='Submit to EMBL-EBI BioSamples database')
    parser.add_argument("--organism", type=str, help='Type of organism data (options: FLU,COV, default: OTHER)')
    parser.add_argument("--submission_dir", type=str, help='Directory to where all required files (such as metadata, fasta, etc.) are stored')
    parser.add_argument("--submission_name", type=str, help='Name of the sample') # used to be sample_name
    parser.add_argument("--config", type=str, help='Name of the config file')
    parser.add_argument("--validated_meta_path", type=str, help='Path to the metadata directory containing validated meta files ending with .tsv')
    parser.add_argument("--fasta_path", required=False, type=str, help='Path to the fasta directory containing split fasta files ending with .fasta')
    parser.add_argument("--gff_path", required=False, type=str, help='')
    parser.add_argument("--table2asn", required=False, type=str, help='Whether to prepare a Table2asn submission')
    parser.add_argument("--prod_or_test", type=str, help='Whether it is a production or test submission')
    # Specific to previous version (--unique_name) or Tostadas
    #parser.add_argument("--submission_database", type=str, help='Which database to submit to')
    #parser.add_argument("--unique_name", type=str, help='Name of batch')
    parser.add_argument("--req_col_config", type=str, help='Path to the required columns yamls')
    parser.add_argument("--update", type=str, help='Whether to update or not')
    parser.add_argument("--send_submission_email", type=str, help='Whether to send genbank/table2asn email or not')

    return parser

class SubmitToDatabase:
    """ Class constructor containing methods and attributes associated with initial submission and update submission
    """
    def __init__(self):
        # get the arguments from argparse
        args = get_args().parse_args()
        self.parameters = vars(args)

    def main(self):
        """ Main function for calling the two different cases: (1) initial submission or (2) update submission
        """
        # either call initial submission or update submission
        if self.parameters['update'].lower() == 'false':
            self.initial_submission()
        elif self.parameters['update'].lower() == 'true':
            self.update_submission()
 
    def initial_submission(self):
        """ Function for initial submission
        """
        # make the dir for storing the command + terminal output
        unique_dir_name = f"{self.parameters['submission_name.']}"
        os.makedirs(f"{unique_dir_name}/initial_submit_info")
 
        # get the command that will be used 
        command = f"submission.py submit --sra {self.parameters['sra']} --genbank {self.parameters['genbank']} --gisaid {self.parameters['gisaid']} --biosample {self.parameters['biosample']} \
                  --organism {self.parameters['organism']} --submission_dir {self.parameters['submission_dir']}  --submission_name {self.parameters['submission_name']} --config {self.parameters['config']} \
                  --metadata {self.parameters['validated_meta_path']}  --fasta {self.parameters['fasta_path']} --gff {self.parameters['gff_path']} --table2asn {self.parameters['table2asn']} --test_or_prod {self.parameters['prod_or_test']} \
                  --req_col_config {self.parameters['req_col_config']} --send_email {self.parameters['send_submission_email']}"        
        #command = f"submission.py --command submit --unique_name {self.parameters['unique_name']} --fasta {self.parameters['fasta_path']} \
        #          --metadata {self.parameters['validated_meta_path']} --gff {self.parameters['gff_path']} --config {self.parameters['config']} --test_or_prod {self.parameters['prod_or_test']} \
        #          --req_col_config {self.parameters['req_col_config']} --send_email {self.parameters['send_submission_email']}"

        # open a txt file and write the command 
        with open(f"{unique_dir_name}/initial_submit_info/{self.parameters['submission_name.']}_initial_submit_info.txt", "w") as f:
            f.write(f"ACTUAL COMMAND USED: {command}\n")
        f.close()

        # submit the submission.py job as a subprocess + write the terminal output
        file_ = open(f"{unique_dir_name}/initial_submit_info/{self.parameters['submission_name.']}_initial_terminal_output.txt", "w+")
        subprocess.run(command, shell=True, stdout=file_)
        file_.close()


    def update_submission(self):
        """ Calls update submission
        """
        unique_dir_name = f"{self.parameters['submission_name.']}"
        os.makedirs(f"{unique_dir_name}/update_submit_info", exist_ok=True)

        # get the command
        #command = f"submission.py --command update_submissions --config {self.parameters['config']} --unique_name {unique_dir_name}"
        command = f"submission.py submit --sra {self.parameters['sra']} --genbank {self.parameters['genbank']} --gisaid {self.parameters['gisaid']} --biosample {self.parameters['biosample']} \
                  --organism {self.parameters['organism']} --submission_dir {self.parameters['submission_dir']}  --submission_name {self.parameters['submission_name']} --config {self.parameters['config']} \
                  --metadata {self.parameters['validated_meta_path']}  --fasta {self.parameters['fasta_path']} --gff {self.parameters['gff_path']} --table2asn {self.parameters['table2asn']} --test_or_prod {self.parameters['prod_or_test']} \
                  --req_col_config {self.parameters['req_col_config']} --send_email {self.parameters['send_submission_email']}"  

        # open a txt file and write the command 
        with open(f"{unique_dir_name}/update_submit_info/{self.parameters['submission_name.']}_update_submit_info.txt", "w") as f:
            f.write(f"ACTUAL COMMAND USED: {command}\n")
        f.close()

        # call the subprocess for update submission
        file_ = open(f"{unique_dir_name}/update_submit_info/{self.parameters['submission_name.']}_update_terminal_output.txt", "w+")
        subprocess.run(command, shell=True, stdout=file_)
        file_.close()
        
        # run the command
        os.system(command)

        # get the upload_log csv out 
        if os.path.isfile(f"{unique_dir_name}/upload_log.csv"):
            os.system(f"cp {unique_dir_name}/upload_log.csv .")


if __name__ == "__main__":
    submit_to_database = SubmitToDatabase()
    submit_to_database.main()
