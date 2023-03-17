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
    parser.add_argument("--validated_meta_path", type=str, help='Path to the metadata directory containing validated meta files ending with .tsv')
    parser.add_argument("--lifted_fasta_path", type=str, help='Path to the fasta directory containing split fasta files ending with .fasta')
    parser.add_argument("--lifted_gff_path", type=str, help='Path to the gff directory containing reformatted gff files ending with .gff')
    parser.add_argument("--config", type=str, help='Name of the config file')
    parser.add_argument("--unique_name", type=str, help='Name of batch')
    parser.add_argument("--prod_or_test", type=str, help='Whether it is a production or test submission')
    parser.add_argument("--submission_database", type=str, help='Which database to submit to')
    parser.add_argument("--req_col_config", type=str, help='Path to the required columns yamls')
    parser.add_argument("--update", type=str, help='Whether to update or not')
    parser.add_argument("--send_submission_email", type=str, help='Whether to send genbank/table2asn email or not')
    parser.add_argument("--sample_name", type=str, help='Name of the sample')
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
        unique_dir_name = f"{self.parameters['unique_name']}.{self.parameters['sample_name']}"
        os.makedirs(f"{unique_dir_name}/initial_submit_info")
 
        # get the command that will be used 
        command = f"submission.py --command {self.parameters['submission_database']} --unique_name {self.parameters['unique_name']} --fasta {self.parameters['lifted_fasta_path']} \
                  --metadata {self.parameters['validated_meta_path']} --gff {self.parameters['lifted_gff_path']} --config {self.parameters['config']} --test_or_prod {self.parameters['prod_or_test']} \
                  --req_col_config {self.parameters['req_col_config']} --send_email {self.parameters['send_submission_email']}"

        # open a txt file and write the command 
        with open(f"{unique_dir_name}/initial_submit_info/{self.parameters['sample_name']}_initial_submit_info", "w") as f:
            f.write(f"ACTUAL COMMAND USED: {command}\n")
        f.close()

        # submit the submission.py job as a subprocess + write the terminal output
        file_ = open(f"{unique_dir_name}/initial_submit_info/{self.parameters['sample_name']}_initial_terminal_output.txt", "w+")
        subprocess.run(command, shell=True, stdout=file_)
        file_.close()


    def update_submission(self):
        """ Calls update submission
        """
        unique_dir_name = f"{self.parameters['unique_name']}.{self.parameters['sample_name']}"
        os.makedirs("update_submit_info")

        # get the command
        command = f"submission.py --command update_submissions --config {self.parameters['config']} --unique_name {unique_dir_name}"
        
        # call the subprocess for update submission
        file_ = open(f"update_submit_info/{self.parameters['sample_name']}_update_terminal_output.txt", "w+")
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
