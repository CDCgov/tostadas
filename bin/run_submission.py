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
        unique_dir_name, sample_name = self.get_unique_name(
            path=self.parameters['validated_meta_path'],
            unique_name=self.parameters['unique_name']
        )
        os.makedirs(unique_dir_name)

        # get the command that will be used 
        command = f"submission.py --command {self.parameters['submission_database']} --unique_name {self.parameters['unique_name']} --fasta {self.parameters['lifted_fasta_path']} \
                  --metadata {self.parameters['validated_meta_path']} --gff {self.parameters['lifted_gff_path']} --config {self.parameters['config']} --test_or_prod {self.parameters['prod_or_test']} \
                  --req_col_config {self.parameters['req_col_config']} --send_submission_email {self.parameters['send_submission_email']}"

        # open a txt file and write the command 
        with open(f"{unique_dir_name}/{sample_name}_initial_submit_info", "w") as f:
            f.write(f"ACTUAL COMMAND USED: {command}\n")
        f.close()

        # submit the submission.py job as a subprocess + write the terminal output
        file_ = open(f"{unique_dir_name}/{sample_name}_initial_terminal_output.txt", "w+")
        subprocess.run(command, shell=True, stdout=file_)
        file_.close()


    def update_submission(self):
        """ Calls update submission
        """
        # get the command that will be used 
        command = f"submission.py --command update_submissions --config {self.parameters['config']} --unique_name {self.parameters['unique_name']}"

        with open(f"update_submission_terminal_output.txt", "w+") as f:
            subprocess.run(f"{command}", shell=True, stdout=f)
        f.close()

     
    @staticmethod
    def get_unique_name(path, unique_name):
         # make the dir for storing the command + terminal output
        sample_name = path.split('/')[-1].split('.')[0]
        unique_dir_name = f"{unique_name}.{sample_name}"
        return unique_dir_name, sample_name


if __name__ == "__main__":
    submit_to_database = SubmitToDatabase()
    submit_to_database.main()
