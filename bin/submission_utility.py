#!/usr/bin/env python3

import time 
import argparse
import os
import glob
import yaml


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--wait", type=str, default='false', help='Flag to wait or not')
    parser.add_argument("--check_submission_config", type=str, default='false', help='Flag for checking whether or not the submission output paths are aligned')
    parser.add_argument("--specific_submission", type=str, help='Certain database to submit to')
    parser.add_argument("--wait_time", type=str, help='Length of time to wait in seconds')
    parser.add_argument("--config", type=str, help='Name of submission config file')
    parser.add_argument("--submission_outputs", type=str, help='Path to the submission outputs')
    return parser


def main():
    # get the parameters 
    args = get_args().parse_args()
    parameters = vars(args)
    
    # check if you need to wait or not
    if parameters['wait'].lower().strip() == 'true':
        time_2_wait = int(parameters['wait_time'])
        time.sleep(time_2_wait)
    
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

                # now write the new .yaml file with this updated value
                with open('submitdir_modified.yaml', 'w') as new_config:
                    yaml.dump(loaded_conf, new_config)


if __name__ == "__main__":
    main()