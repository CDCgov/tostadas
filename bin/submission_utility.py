#!/usr/bin/env python3

import time 
import argparse
import os
import glob
import yaml
import shutil


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
    else:
        # make the new directory to copy over the files to
        os.mkdir(f"update_entry", mode=0o777)
        # copy over the processed files
        for folder in glob.glob(f"{parameters['processed_samples']}/*"):
            # get the dir name 
            dir_name = folder.split('/')[-1]
            # copy over the files 
            shutil.copytree(folder, f"update_entry/{dir_name}")


    """
    # modify the submission by checking the output paths are aligned + modifying for certain type of submission
    if parameters['check_submission_config'].lower().strip() == 'true':

        # get the path to the config 
        root = '/'.join(__file__.split('/')[:-1])
        path_to_config = f"{root}/config_files/{parameters['config']}"

        # open the config and make some modifications 
        with open(path_to_config) as sub_config:
            loaded_conf = yaml.safe_load(sub_config)
            if loaded_conf['general']['submission_directory'] != parameters['submission_outputs']:
                loaded_conf['general']['submission_directory'] = parameters['submission_outputs']

            # go through and change the config to match the passed in database submission
            database_mappings = {
                'genbank': 'submit_Genbank', 
                'sra': 'submit_SRA', 
                'gisaid': 'submit_GISAID', 
                'biosample': 'submit_BioSample',
                'joint_sra_biosample': 'joint_SRA_BioSample_submission'
            }

            if parameters['database'] != 'submit':
                for key, value in database_mappings.items():
                    if parameters['database'] == key:
                        loaded_conf['general'][value] = True
                    else:
                        loaded_conf['general'][value] = False

            # now write the new .yaml file with this updated value
            os.mkdir('config_files')
            with open('config_files/nextflow_modified.yaml', 'w') as new_config:
                yaml.dump(loaded_conf, new_config)
    """


if __name__ == "__main__":
    main()