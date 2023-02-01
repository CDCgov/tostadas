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
    parser.add_argument("--meta_path", type=str, help='Path to the original metadata file')
    parser.add_argument("--validated_meta_path", type=str, help='Path to the metadata directory containing validated meta files ending with .tsv')
    parser.add_argument("--lifted_fasta_path", type=str, help='Path to the fasta directory containing split fasta files ending with .fasta')
    parser.add_argument("--lifted_gff_path", type=str, help='Path to the gff directory containing reformatted gff files ending with .gff')
    parser.add_argument("--entry_flag", type=str, help='Flag passed in for informing whether entrypoint was used or not')
    parser.add_argument("--submission_script", type=str, help='Path to submission.py script')
    parser.add_argument("--config", type=str, help='Name of the config file')
    parser.add_argument("--update", type=str, help='Whether to run update or not')
    parser.add_argument("--nf_output_dir", type=str, help='Name of output directory in nextflow')
    parser.add_argument("--submission_output_dir", type=str, help='Name of submission directory in nextflow')
    parser.add_argument("--launch_dir", type=str, help='Path to directory where it is being launched ')
    parser.add_argument("--project_dir", type=str, help='Path to directory where main.nf is located')
    parser.add_argument("--batch_name", type=str, help='Name of batch')
    parser.add_argument("--prod_or_test", type=str, help='Whether it is a production or test submission')
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
       # check if relative path or absolute path
        if not os.path.isabs(self.parameters['nf_output_dir']):
            #work_dir= os.mkdir("/data/nf" )
            self.parameters['nf_output_dir'] = f"{self.parameters['nf_output_dir']}"
            if self.parameters['entry_flag'].lower() != 'true':
                self.parameters['validated_meta_path'] = f"{meta_filename}"
                self.parameters['lifted_fasta_path'] = f"{meta_filename}"
                self.parameters['lifted_gff_path'] = f"{meta_filename}"
                
        # get the meta file name from meta path if entry point was not used
        if self.parameters['entry_flag'].lower() == 'false':
            meta_filename = (self.parameters['meta_path'].split('/')[-1]).split('.')[0]
            meta_files = glob.glob(f"{self.parameters['validated_meta_path']}/{meta_filename}/tsv_per_sample/*.tsv")
            fasta_files = glob.glob(f"{self.parameters['lifted_fasta_path']}/{meta_filename}/fasta/*.fasta")
            gff_files = glob.glob(f"{self.parameters['lifted_gff_path']}/{meta_filename}/liftoff/*.gff")

        # if the entrypoint was used, assumes that the path to dir contaiing the files is already specified
        elif self.parameters['entry_flag'].lower() == 'true':
            meta_files = glob.glob(f"{self.parameters['validated_meta_path']}/*.tsv")
            fasta_files = glob.glob(f"{self.parameters['lifted_fasta_path']}/*.fasta")
            gff_files = glob.glob(f"{self.parameters['lifted_gff_path']}/*.gff")
        else:
            raise ValueError("Entry flag, for whether or not submission was called via entrypoint, must be a str and either true or false " + \
                             f"... passed input = {self.parameters['entry_flag']}")

        # check to make sure that the number of meta, fasta, and gff files are equal to each other
        try:
            assert len(meta_files) == len(fasta_files) == len(gff_files)
        except AssertionError:
            raise AssertionError(f"Length of meta files {len(meta_files)} does not match length of fasta files {len(fasta_files)}" + \
                                     f" does not match the length of the gff files {len(gff_files)}")
        # check that the files actually exist
        try:
            assert 0 not in [len(meta_files), len(fasta_files), len(gff_files)] != 0 
        except AssertionError:
            raise AssertionError(f"Length of meta files {len(meta_files)} or fasta files {len(fasta_files)} or gff files {len(gff_files)} is equal to zero" + \
                                 f"{self.parameters['validated_meta_path']}")
        
        # create the main submission outputs directory 
        commands = {}
        if not os.path.isabs(self.parameters['submission_output_dir']):
            dirs_to_check = {
                'root': f"{self.parameters['nf_output_dir']}/{self.parameters['submission_output_dir']}",
                'terminal': f"{self.parameters['nf_output_dir']}/{self.parameters['submission_output_dir']}/terminal_outputs",
                'commands': f"{self.parameters['nf_output_dir']}/{self.parameters['submission_output_dir']}/commands_used"
            }
        else:
            dirs_to_check = {
                'root': f"{self.parameters['submission_output_dir']}",
                'terminal': f"{self.parameters['submission_output_dir']}/terminal_outputs",
                'commands': f"{self.parameters['submission_output_dir']}/commands_used"
            }
        for path in dirs_to_check: 
            if not os.path.isdir(dirs_to_check[path]):
                os.makedirs(dirs_to_check[path], exist_ok=True)
        
        # check the config path (if absolute leave it else assume that it is in conf folder within submission scripts)
        if not os.path.isabs(self.parameters['config']):
            self.parameters['config'] = f"{self.parameters['project_dir']}/submission_scripts/config_files/{self.parameters['config']}"
        
        # check that the submission config file value matches the one inside of the params config 
        with open(self.parameters['config']) as sub_config:
            loaded_conf = yaml.safe_load(sub_config)
            if loaded_conf['general']['submission_directory'] != dirs_to_check['root']:
                loaded_conf['general']['submission_directory'] = dirs_to_check['root']
                # now write the new .yaml file with this updated value
                path_to_new_conf = '/'.join(self.parameters['config'].split('/')[:-1]) + '/' + self.parameters['config'].split('/')[-1].split('.')[0] + '_submitdir_modified.yaml'
                if os.path.exists(path_to_new_conf):
                    os.remove(path_to_new_conf)
                with open(path_to_new_conf, 'w') as new_config:
                    yaml.dump(loaded_conf, new_config)
                    self.parameters['config'] = path_to_new_conf

        # sort file lists to ensure they are in the same order, assumes you have alpha prefix
        meta_files = sorted(meta_files)
        fasta_files = sorted(fasta_files)
        gff_files = sorted(gff_files)

        for meta, fasta, gff in zip(meta_files, fasta_files, gff_files):
            # get the sample names and specify command
            sample_name = (meta.split('/')[-1]).split('.')[0]
            if self.parameters['prod_or_test'].lower().strip() == 'test':
                command = f"python {self.parameters['submission_script']} submit --unique_name {self.parameters['batch_name']}.{sample_name} --fasta {fasta}" + \
                        f" --metadata {meta} --gff {gff} --config {self.parameters['config']} --{self.parameters['prod_or_test']}"
            elif self.parameters['prod_or_test'].lower().strip() == 'prod':
                command = f"python {self.parameters['submission_script']} submit --unique_name {self.parameters['batch_name']}.{sample_name} --fasta {fasta}" + \
                        f" --metadata {meta} --gff {gff} --config {self.parameters['config']}"
            else: 
                raise ValueError(f"ERROR: Must specify either test/prod for the submission_prod_or_test flag... passed in value is {self.parameters['prod_or_test']}")

            # write the text file with information
            with open(f"{dirs_to_check['commands']}/{sample_name}_initial_submit_info.txt", 'w') as f:
                f.write(f"PATH TO META FILE: {meta}\n")
                f.write(f"PATH TO FASTA FILE: {fasta}\n")
                f.write(f"PATH TO GFF FILE: {gff}\n")
                f.write(f"ACTUAL COMMAND USED: {command}\n")
            f.close()
            # store the final command within dictionary
            commands[sample_name] = command

        # cycle through the commands stored and initiate subprocesses for these + write terminal output to file
        for key in commands.keys():
            file_ = open(f"{dirs_to_check['terminal']}/{key}_initial_terminal_output.txt", "w+")
            subprocess.run(commands[key], shell=True, stdout=file_)
            file_.close()

    def update_submission(self):
        """ Calls update submission
        """
        if not os.path.isabs(self.parameters['nf_output_dir']):
            self.parameters['nf_output_dir'] = f"{self.parameters['launch_dir']}/{self.parameters['nf_output_dir']}"

        if not os.path.isabs(self.parameters['submission_output_dir']):
            terminal_dir = f"{self.parameters['nf_output_dir']}/{self.parameters['submission_output_dir']}/terminal_outputs",
            command_dir = f"{self.parameters['nf_output_dir']}/{self.parameters['submission_output_dir']}/commands_used"
        else:
            terminal_dir = f"{self.parameters['submission_output_dir']}/terminal_outputs", 
            command_dir = f"{self.parameters['submission_output_dir']}/commands_used"

        with open(f"{command_dir}/submit_info_for_update.txt", 'w') as f:
            f.write(f"ACTUAL COMMAND USED: python {self.parameters['submission_script']} update_submissions\n")
            f.close()

        os.system(f"python {self.parameters['submission_script']} update_submissions")
        """
        with open(f"{terminal_dir}/test.txt", "w+") as f:
            subprocess.run(f"python {self.parameters['submission_script']} update_submissions", shell=true, stdout=f)
        f.close()
        """

if __name__ == "__main__":
    submit_to_database = SubmitToDatabase()
    submit_to_database.main()
