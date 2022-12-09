import os
import argparse
import pandas as pd


def test_main():
    metadata_validation_tests = MetadataValidationTests()
    # check directories
    metadata_validation_tests.get_dirs()
    try:
        assert 'validate_metadata.py' in os.listdir(os.getcwd())
    except AssertionError:
        raise AssertionError(f"Could not find validate_metadata.py in {os.getcwd()}")
    # test the metadata validation script
    metadata_validation_tests.run_metadata_validation()

class MetadataValidationTests:
    def __init__(self):
        self.meta_file_names = ['MPXV_metadata_Sample_Run_1', 'MPXV_metadata_Sample_Run_2_error',
                                'MPXV_metadata_Sample_Run_3_error', 'MPXV_metadata_Sample_Run_4',
                                'MPXV_metadata_Sample_Run_5']
        self.root = None
        self.path_to_metadata_val_dir = None
        self.sample_names = []

    def get_dirs(self):
        # handle directories
        self.root = '/'.join(os.getcwd().split('/')[:-1])
        self.path_to_metadata_val_dir = os.path.join(self.root, 'bin')
        os.chdir(self.path_to_metadata_val_dir)

    def get_sample_names(self, meta_path):
        df = pd.read_excel(meta_path, header=[1])
        self.sample_names = df['sample_name'].tolist()

    def run_metadata_validation(self):
        # define the fasta path
        fasta_path = f"{self.root}/input_files/trialData.fasta"
        for meta, expected in zip(self.meta_file_names, ['good', 'error', 'error', 'good', 'good']):
            meta_path = f"{self.root}/input_files/{meta}.xlsx"
            # get the sample names from metadata file
            self.get_sample_names(meta_path=meta_path)
            try:
                os.system(f"python validate_metadata.py --fasta_path {fasta_path} --meta_path {meta_path} --output_dir test_validation_outputs")
            except AssertionError:
                raise AssertionError(f"Unable to run validate_metadata.py file on {meta}")
            self.check_outputs(output_tsv_path=f"{self.root}/bin/test_validation_outputs/{meta}/tsv_per_sample",
                               output_error_path=f"{self.root}/bin/test_validation_outputs/{meta}/errors/full_error.txt",
                               expected=expected)

    def check_outputs(self, output_tsv_path, output_error_path, expected):
        try:
            assert os.path.isfile(output_error_path)
        except AssertionError:
            raise AssertionError(f"Could not find the error file in {output_error_path}")
        if expected == 'error':
            if len(os.listdir(output_tsv_path)) != 0:
                raise ValueError(f"Found an output metadata file in {output_tsv_path} but expected error")
        else:
            for expected_file in [f"{x}.tsv" for x in self.sample_names]:
                try:
                    assert expected_file in os.listdir(output_tsv_path)
                except AssertionError:
                    raise AssertionError(f"Could not find {expected_file} file in {os.listdir(output_tsv_path)}")
            self.check_metadata_contents()

    def check_metadata_contents(self):
        pass

