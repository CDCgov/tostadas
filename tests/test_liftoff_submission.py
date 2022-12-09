import os
import argparse
import pandas as pd


def test_main():
    liftoff_tests = LiftoffSubmissionTests()
    # check directories
    liftoff_tests.get_dirs()
    try:
        assert 'liftoff_submission.py' in os.listdir(os.getcwd())
    except AssertionError:
        raise AssertionError(f"Could not find liftoff_submission.py script in {os.getcwd()}")
    # run test for checking the codon and itr checks
    checks(liftoff_tests)

def handling_dirs(liftoff_tests):
    liftoff_tests.get_dirs()
    assert 'liftoff_submission.py' in os.listdir(os.getcwd())

def checks(liftoff_tests):
    # specify all the appropriate files to pass in
    for key in liftoff_tests.paths:
        for file_name in range(len(liftoff_tests.paths[key])):
            liftoff_tests.paths[key][file_name] = os.path.join(liftoff_tests.root, liftoff_tests.paths[key][file_name])
    # run the command for checks on files
    liftoff_tests.liftoff_cmd()
    # run the command for checks with different parameters
    liftoff_tests.liftoff_cmd2()


class LiftoffSubmissionTests:
    def __init__(self):
        self.paths = {
            'meta_paths': ['input_files/MPXV_metadata_Sample_Run_1.xlsx', 'input_files/MPXV_metadata_Sample_Run_5.xlsx', 'input_files/test.xlsx'],
            'fasta_paths': ['input_files/trialData.fasta', 'input_files/trialDatav5.fasta', 'input_files/test.fasta'],
            'ref_fasta_path': ['input_files/ref/ref.MPXV.NC063383.v7.fasta'],
            'ref_gff_path': ['input_files/ref/ref.MPXV.NC063383.v7.gff'],
        }

        self.root = None

        self.liftoff_params = {
            'print_version_exit': 'true',
            'print_help_exit': 'true',
            'unmapped_features_file_name': 'test.txt',
            'bundled_params': {
                'parallel_processes': 6,
                'delete_temp_files': 'false',
                'coverage_threshold': 0.4,
                'child_feature_align_threshold': 0.4,
                'distance_scaling_factor': 1.8,
                'mismatch': 1,
                'gap_open': 1,
                'gap_extend': 2,
            }
        }

    def get_dirs(self):
        # get the git root for repository
        self.root = '/'.join(os.getcwd().split('/')[:-1])
        path_to_liftoff_submission_dir = os.path.join(self.root, 'bin')
        os.chdir(path_to_liftoff_submission_dir)

    @staticmethod
    def get_samples(meta_path):
        idf = pd.read_excel(meta_path, header=[1], sheet_name=0)
        df = idf.set_index("sample_name", drop=False)
        sample_list = df.loc[:, "sample_name"]
        return sample_list

    def liftoff_cmd(self):
        for fasta, meta in zip(self.paths['fasta_paths'], self.paths['meta_paths']):
            meta_name = meta.split('/')[-1].split('.')[0]
            try:
                # run it with keeping the temporary directories
                os.system(f"python liftoff_submission.py --fasta_path {fasta} --meta_path {meta} --ref_fasta_path " + \
                          f"{self.paths['ref_fasta_path'][0]} --ref_gff_path {self.paths['ref_gff_path'][0]} --final_liftoff_output_dir test_liftoff_outputs --delete_temp_files False")
                self.check_outputs(final_output_dir=f"test_liftoff_outputs/final_{meta_name}", final_temp_dir=f"test_liftoff_outputs/temp_{meta_name}",
                                   meta_path=meta, temp_present=True, unmapped_features_name='output.unmapped_features')

                # run it with deleting the temporary directories
                os.system(f"python liftoff_submission.py --fasta_path {fasta} --meta_path {meta} --ref_fasta_path " + \
                          f"{self.paths['ref_fasta_path'][0]} --ref_gff_path {self.paths['ref_gff_path'][0]} --final_liftoff_output_dir test_liftoff_outputs --delete_temp_files True")
                self.check_outputs(final_output_dir=f"test_liftoff_outputs/final_{meta_name}",
                               final_temp_dir=f"test_liftoff_outputs/temp_{meta_name}",
                               meta_path=meta, temp_present=False, unmapped_features_name='output.unmapped_features')
            except AssertionError:
                raise AssertionError(f"Failed to run the liftoff_submission.py script")

    def liftoff_cmd2(self):
        for fasta, meta in zip(self.paths['fasta_paths'], self.paths['meta_paths']):
            meta_name = meta.split('/')[-1].split('.')[0]
            for param in self.liftoff_params.keys():
                if param == 'print_version_exit' or param == 'print_help_exit' or param == 'unmapped_features_file_name':
                    os.system(f"python liftoff_submission.py --fasta_path {fasta} --meta_path {meta} --ref_fasta_path " + \
                              f"{self.paths['ref_fasta_path'][0]} --ref_gff_path {self.paths['ref_gff_path'][0]} --final_liftoff_output_dir " + \
                              f"test_liftoff_outputs --{param} {self.liftoff_params[param]} --delete_temp_files True")
                    if param == 'unmapped_features_file_name':
                        self.check_outputs(final_output_dir=f"test_liftoff_outputs/final_{meta_name}",
                                           final_temp_dir=f"test_liftoff_outputs/temp_{meta_name}",
                                           meta_path=meta, temp_present='skip', unmapped_features_name='test')
                else:
                    command = f"python liftoff_submission.py --fasta_path {fasta} --meta_path {meta} --ref_fasta_path " + \
                              f"{self.paths['ref_fasta_path'][0]} --ref_gff_path {self.paths['ref_gff_path'][0]} --final_liftoff_output_dir " + \
                              f"test_liftoff_outputs --delete_temp_files True"
                    for param2 in self.liftoff_params[param].keys():
                        command += f" --{param2} {self.liftoff_params[param][param2]}"
                    os.system(command)
                    self.check_outputs(final_output_dir=f"test_liftoff_outputs/final_{meta_name}",
                                       final_temp_dir=f"test_liftoff_outputs/temp_{meta_name}",
                                       meta_path=meta, temp_present='skip',
                                       unmapped_features_name='output.unmapped_features')

    def check_outputs(self, final_output_dir, final_temp_dir, meta_path, temp_present, unmapped_features_name):
        try:
            assert os.path.isfile(f"{final_output_dir}/errors/annotation_error.txt")
            assert os.path.isfile(f"{final_output_dir}/errors/{unmapped_features_name}.txt")
        except AssertionError:
            raise AssertionError(f"Expected error files not found in {final_output_dir}/errors")

        samples = self.get_samples(meta_path)
        for sample in samples:
            for output_type, ext in zip(['fasta', 'liftoff', 'tbl'], ['.fasta', '_reformatted.gff', '.tbl']):
                if not os.path.isfile(f"{final_output_dir}/{output_type}/{sample}{ext}"):
                    raise AssertionError(f"Could not the following file: {sample}{ext} in {output_type}{final_output_dir}")

        if temp_present is True:
            try:
                assert os.path.isdir(final_temp_dir)
            except AssertionError:
                raise AssertionError(f"Could not find temporary directory despite passing in flag to keep it")
        elif temp_present is False:
            try:
                assert not os.path.isdir(final_temp_dir)
            except AssertionError:
                raise AssertionError(f"Found temporary directory despite passing in flag to delete it")

if __name__ == "__main__":
    test_main()