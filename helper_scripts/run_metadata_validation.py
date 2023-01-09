import os

class MetadataValidationTests:
    def __init__(self):
        self.meta_file_names = ['MPXV_metadata_Sample_Run_1', 'MPXV_metadata_Sample_Run_2_error',
                                'MPXV_metadata_Sample_Run_3_error', 'MPXV_metadata_Sample_Run_4',
                                'MPXV_metadata_Sample_Run_5']
        # handle directories
        self.root = '/'.join(os.getcwd().split('/')[:-1])
        self.path_to_metadata_val_dir = os.path.join(self.root, 'bin')
        os.chdir(self.path_to_metadata_val_dir)

    def run_metadata_validation(self):
        for meta, expected in zip(self.meta_file_names, ['good', 'error', 'error', 'good', 'good']):
            meta_path = f"{self.root}/input_files/{meta}.xlsx"
            fasta_path = f"{self.root}/input_files/trialData.fasta"
            try:
                os.system(f"python validate_metadata.py --fasta_path {fasta_path} --meta_path {meta_path} --output_dir test_validation_outputs")
            except AssertionError:
                raise AssertionError(f"Unable to run validate_metadata.py file on {meta}")

if __name__ == "__main__":
    metadata_validation_tests = MetadataValidationTests()
    metadata_validation_tests.run_metadata_validation()
