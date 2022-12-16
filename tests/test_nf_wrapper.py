import os
import time
import numpy as np
import shutil
import argparse
from alive_progress import alive_bar
import sys


def get_args():
    """ All potential arguments passed in through command line
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--scicomp", type=str, default='false', help='whether running on scicomp or not')
    parser.add_argument("--alive_bar", type=str, default='false', help='whether to use interactive progress bar')
    parser.add_argument("--progress_bar", type=str, default='true', help='whether to use custom progress bar (faster)')
    parser.add_argument("--test_entry", type=str, default='true', help='whether to test out the entrypoints for annotation and validation')
    parser.add_argument("--test_workflows", type=str, default='true', help='whether to test out the main workflows (full and full without submission)')
    parser.add_argument("--test_submission", type=str, default='true', help='whether to test out the submission subworkflow')
    parser.add_argument("--only_cleanup", type=str, default='false', help='whether to cleanup files and exit')
    return parser


def test_main():
    start = time.time()

    # get param 
    args = get_args().parse_args()
    parameters = vars(args)

    # initialize class constructors
    get_info = Get_Info(parameters)
    utility = Utility()
    run_tests = Run_Tests(utility, get_info, parameters)

    # get the information
    get_info.get_commands()

    # check if only cleanup
    if parameters['only_cleanup'].lower() == 'true':
        os.system(f"nextflow run {get_info.main_nf} -profile test -entry only_cleanup_files >/dev/null 2>&1")
        utility.handle_deletions()
        sys.exit()

    # run the commands
    print(f"\nTESTING IN PROGRESS\n")

    if parameters['alive_bar'].lower() == 'true':
        parameters['progress_bar'] = 'false'
        with alive_bar(len(get_info.commands)+len(get_info.submission_commands), title='PROGRESS', bar='blocks', spinner='fishes') as run_tests.bar:
            run_tests.run_main()
    else:
        run_tests.run_main()

    end = time.time()
    print(f"\n\nPASSED {run_tests.tests_passed}/{len(get_info.commands)+len(get_info.submission_commands)} TESTS SUCCESSFULLY IN {np.round((end-start)/60,2)} MINUTES\n\n")

    # delete all residual files
    utility.handle_deletions()
    
class Run_Tests():
    def __init__(self, utility, get_info, parameters):
        self.parameters = parameters
        self.utility = utility
        self.get_info = get_info
        self.tests_passed = 0
        self.bar = None

    def run_main(self):
        # run the main commands (everything except for submission)
        if self.parameters['progress_bar'].lower() == 'true':
            self.utility.progress_bar(self.tests_passed, len(self.get_info.commands)+len(self.get_info.submission_commands), 
                bar_length=len(self.get_info.commands)+len(self.get_info.submission_commands))

        for command, check, meta_file_name in zip(self.get_info.commands, self.get_info.check_outputs['num'], self.get_info.check_outputs['meta']): 
            if check == 3 or check == 4:
                os.system(f"nextflow run {self.get_info.main_nf} -profile test -entry only_cleanup_files >/dev/null 2>&1")
            # submit the command and check output
            os.system(command + " >/dev/null 2>&1") 
            self.utility.check_outputs(check, meta_file_name, command)
            self.tests_passed+=1 
            # update the progress bar
            if self.parameters['alive_bar'].lower() == 'true': 
                self.bar()
            else:
                self.utility.progress_bar(self.tests_passed, len(self.get_info.commands)+len(self.get_info.submission_commands), 
                bar_length=len(self.get_info.commands)+len(self.get_info.submission_commands))
        # now run the submission commands
        self.run_submission()

    def run_submission(self):
        # run the submission command 
        for command, without_sub in zip(self.get_info.submission_commands, self.get_info.without_sub_commands):
            # delete all previous files
            os.system(f"nextflow run {self.get_info.main_nf} -profile test -entry only_cleanup_files >/dev/null 2>&1")
            # first generate the files without submission 
            os.system(without_sub + " >/dev/null 2>&1")
            # now run the submission command
            os.system(command + " >/dev/null 2>&1")
            # check the outputs 
            self.utility.check_outputs(check=5, meta_file_name='default', command=command)
            self.tests_passed+=1 
            # update progress bar
            if self.parameters['alive_bar'].lower() == 'true': 
                self.bar()
            else:
                self.utility.progress_bar(self.tests_passed, len(self.get_info.commands)+len(self.get_info.submission_commands), 
                bar_length=len(self.get_info.commands)+len(self.get_info.submission_commands))
    

class Get_Info():
    def __init__(self, parameters):
        # parameters
        self.parameters = parameters 

        # necessary paths for files 
        self.paths = {
            'meta_paths': [
                'input_files/MPOX_metadata_20221104_16_2022MPXV_new_template.xlsx', 
                'input_files/MPXV_metadata_Sample_Run_1.xlsx', 'input_files/MPXV_metadata_Sample_Run_5.xlsx', 
                'input_files/test.xlsx'
            ],
            'meta_file_name': [
                meta_file_name.split('/')[-1].split('.')[0] for meta_file_name in [
                    'input_files/MPOX_metadata_20221104_16_2022MPXV_new_template.xlsx', 
                    'input_files/MPXV_metadata_Sample_Run_1.xlsx', 
                    'input_files/MPXV_metadata_Sample_Run_5.xlsx', 
                    'input_files/test.xlsx'
                ]
            ],
            'fasta_paths': [
                'input_files/16mpxv.fasta', 
                'input_files/trialData.fasta', 
                'input_files/trialDatav5.fasta', 
                'input_files/test.fasta'
            ],
            'output_dir': os.path.join(os.getcwd(), 'nf_test_results')
        }

        # command information
        self.root = '/'.join(__file__.split('/')[:-2])
        self.main_nf = self.root + '/main.nf'
        self.commands = []
        self.submission_commands = []
        self.check_outputs = {'num': [], 'meta': []}
        self.without_sub_commands = []

    def get_commands(self):
        # determine methods to run
        if self.parameters['scicomp'].lower() == 'false':
            methods = ['singularity', 'docker', 'conda']
        elif self.parameters['scicomp'].lower() == 'true':
            methods = ['singularity', 'conda']
        else:
            raise ValueError(f"Valid value was not passed in for scicomp flag... must be either true or false")

        for x in range(len(self.paths['meta_paths'])):
            for y in methods:
                # get the without submission command on outside
                without_sub = f"nextflow run {self.main_nf} -profile test,{y} --run_submission false --meta_path {self.root}/{self.paths['meta_paths'][x]}" + \
                        f" --fasta_path {self.root}/{self.paths['fasta_paths'][x]} --val_meta_file_name {self.paths['meta_file_name'][x]} --scicomp {self.parameters['scicomp']}"
               
                # get the main workflwos
                if self.parameters['test_workflows'].lower() == 'true':
                    # get the commands with default
                    self.commands.append(f"nextflow run {self.main_nf} -profile test,{y} --submission_wait_time 1 --meta_path {self.root}/{self.paths['meta_paths'][x]}" + \
                        f" --fasta_path {self.root}/{self.paths['fasta_paths'][x]} --val_meta_file_name {self.paths['meta_file_name'][x]} --scicomp {self.parameters['scicomp']}")
                    self.check_outputs['num'].append(1)
                    self.check_outputs['meta'].append(self.paths['meta_file_name'][x])

                    # get the command without submission
                    self.commands.append(without_sub)
                    self.check_outputs['num'].append(2)
                    self.check_outputs['meta'].append(self.paths['meta_file_name'][x])

                # get the entry commands
                if self.parameters['test_entry'].lower() == 'true':
                    # get the command with only validation 
                    self.commands.append(f"nextflow run {self.main_nf} -profile test,{y} -entry only_validation --meta_path {self.root}/{self.paths['meta_paths'][x]}" + \
                        f" --fasta_path {self.root}/{self.paths['fasta_paths'][x]} --val_meta_file_name {self.paths['meta_file_name'][x]} --scicomp {self.parameters['scicomp']}")
                    self.check_outputs['num'].append(3)
                    self.check_outputs['meta'].append(self.paths['meta_file_name'][x])

                    # get the command with only annotation
                    self.commands.append(f"nextflow run {self.main_nf} -profile test,{y} -entry only_liftoff --meta_path {self.root}/{self.paths['meta_paths'][x]}" + \
                        f" --fasta_path {self.root}/{self.paths['fasta_paths'][x]} --val_meta_file_name {self.paths['meta_file_name'][x]} --scicomp {self.parameters['scicomp']}")
                    self.check_outputs['num'].append(4)
                    self.check_outputs['meta'].append(self.paths['meta_file_name'][x])

                if self.parameters['test_submission'].lower() == 'true':
                    # get the commands for submission
                    self.submission_commands.append(f"nextflow run {self.main_nf} -profile test,{y} -entry only_submission --submission_wait_time 1 --meta_path {self.root}/{self.paths['meta_paths'][x]}" + \
                        f" --fasta_path {self.root}/{self.paths['fasta_paths'][x]} --val_meta_file_name {self.paths['meta_file_name'][x]} --scicomp {self.parameters['scicomp']}")
                    self.without_sub_commands.append(without_sub)


class Utility():
    def __init__(self):
        # get some necessary information
        self.root = '/'.join(__file__.split('/')[:-2])

    @staticmethod
    def handle_deletions():
        # get the tests directory 
        tests_dir = '/'.join(__file__.split('/')[:-1])
        # delete all .nextflow files / directory 
        for file in os.listdir(tests_dir):
            if '.nextflow' in file:
                try:
                    os.remove(file)
                except:
                    shutil.rmtree(file, ignore_errors=True)

        # delete all non conda directories within work 
        for file in os.listdir(os.path.join(tests_dir, 'work')):
            if file != 'conda':
                shutil.rmtree(os.path.join(tests_dir, file), ignore_errors=True)
        
        # delete the nextflow results dir 
        if os.path.isdir(os.path.join(tests_dir, 'nf_test_results')):
            shutil.rmtree(os.path.join(tests_dir, 'nf_test_results'))

    @staticmethod
    def progress_bar(current, total, bar_length):
        fraction = current / total
        arrow = int(fraction * bar_length - 1) * '-' + '>'
        padding = int(bar_length - len(arrow)) * ' '
        ending = '\n' if current == total else '\r'
        print(f'PROGRESS: [{arrow}{padding}] {int(fraction*100)}% | {current}/{total}', end=ending)

    def check_outputs(self, check, meta_file_name, command):
        if check == 1:
            # should be nf test results with all subdirs 
            self.actually_check_outputs(which_dirs=['validation', 'liftoff', 'submission'], meta_file_name=meta_file_name, command=command)
        elif check == 2:
            # should be all test results except for submission
            self.actually_check_outputs(which_dirs=['validation', 'liftoff'], meta_file_name=meta_file_name, command=command)
        elif check == 3:
            # should be only validation
            self.actually_check_outputs(which_dirs=['validation'], meta_file_name=meta_file_name, command=command)
        elif check == 4:
            # should be only annotation
            self.actually_check_outputs(which_dirs=['liftoff'], meta_file_name=meta_file_name, command=command)
        elif check == 5:
            # should be only submission
            self.actually_check_outputs(which_dirs=['submission'], meta_file_name=meta_file_name, command=command)
    
    def actually_check_outputs(self, which_dirs, meta_file_name, command):
        expected_files = {
            'liftoff': [
                os.path.join(self.root, 'tests/nf_test_results/liftoff_outputs'),
                os.path.join(self.root, f"tests/nf_test_results/liftoff_outputs/{meta_file_name}/errors"),
                os.path.join(self.root, f"tests/nf_test_results/liftoff_outputs/{meta_file_name}/fasta"),
                os.path.join(self.root, f"tests/nf_test_results/liftoff_outputs/{meta_file_name}/liftoff"),
                os.path.join(self.root, f"tests/nf_test_results/liftoff_outputs/{meta_file_name}/tbl")
            ],
            'validation': [
                os.path.join(self.root, 'tests/nf_test_results/validation_outputs'),
                os.path.join(self.root, f"tests/nf_test_results/validation_outputs/{meta_file_name}/errors"),
                os.path.join(self.root, f"tests/nf_test_results/validation_outputs/{meta_file_name}/tsv_per_sample")
            ],
            'submission': [
                os.path.join(self.root, 'tests/nf_test_results/submission_outputs'),
                os.path.join(self.root, 'tests/nf_test_results/submission_outputs/terminal_outputs'),
                os.path.join(self.root, 'tests/nf_test_results/submission_outputs/commands_used')
            ]
        }

        for x in which_dirs:
            for y in expected_files[x]:
                try:
                    assert os.path.exists(y)
                    assert len(os.listdir(y)) != 0
                except AssertionError:
                    raise AssertionError(f"Could not find the following path: {y} or it is empty.\nFollowing command was used: {command}")


if __name__ == "__main__":
    test_main()