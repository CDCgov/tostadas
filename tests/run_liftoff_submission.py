import os
import argparse
import pandas as pd

class LiftoffSubmission:
    def __init__(self):
        self.parameters = None
        self.root = None
        self.meta_paths = ['input_files/MPXV_metadata_Sample_Run_1.xlsx',
                           'input_files/MPXV_metadata_Sample_Run_5.xlsx',
                           'input_files/test.xlsx']
        self.fasta_paths = ['input_files/trialData.fasta', 'input_files/trialDatav5.fasta', 'input_files/test.fasta']
        ref_fasta = 'input_files/ref/ref.MPXV.NC063383.v7.fasta'
        self.ref_fasta_paths = [ref_fasta, ref_fasta, ref_fasta]
        ref_gff = 'input_files/ref/ref.MPXV.NC063383.v7.gff'
        self.ref_gff_paths = [ref_gff, ref_gff, ref_gff]

    def run_main(self):
        # get general params
        args = self.get_args().parse_args()
        self.parameters = vars(args)
        # handle dirs stuff
        self.get_dirs()
        # check which files to run
        if self.parameters['codon_and_itr_check_run'] is True:
            print(f'\n********** DOING STOP CODON AND ITR CHECK **********\n')
            self.codon_and_itr_liftoff_submission_cmd()

    @staticmethod
    def get_args():
        parser = argparse.ArgumentParser(description="Parameters for Running Test For Liftoff Submission")
        parser.add_argument("--codon_and_itr_check_run", type=bool, default=True, help="Runs the files that will trigger codon and itr checks")
        return parser

    def get_dirs(self):
        # get the git root for repository
        self.root = '/'.join(os.getcwd().split('/')[:-1])
        path_to_liftoff_submission_dir = os.path.join(self.root, 'bin')
        os.chdir(path_to_liftoff_submission_dir)

    def codon_and_itr_liftoff_submission_cmd(self):
        for fasta, meta, ref_fasta, ref_gff in zip(self.fasta_paths, self.meta_paths, self.ref_fasta_paths, self.ref_gff_paths):
            meta_name = meta.split('/')[-1].split('.')[0]
            self.abstracted_cmd(
                f"{self.root}/{fasta}",
                f"{self.root}/{meta}",
                f"{self.root}/{ref_fasta}",
                f"{self.root}/{ref_gff}",
                check_type='checking stop codon fixing functionality')
            self.check_outputs(final_output_dir=f"test_liftoff_outputs/final_{meta_name}", meta_path=f"{self.root}/{meta}")

    @staticmethod
    def get_samples(meta_path):
        idf = pd.read_excel(meta_path, header=[1], sheet_name=0)
        df = idf.set_index("sample_name", drop=False)
        sample_list = df.loc[:, "sample_name"]
        return sample_list

    @staticmethod
    def abstracted_cmd(fasta, meta, ref_fasta, ref_gff, check_type):
        try:
            os.system(f"python liftoff_submission.py --fasta_path {fasta} --meta_path {meta} --ref_fasta_path " + \
                  f"{ref_fasta} --ref_gff_path {ref_gff} --final_liftoff_output_dir test_liftoff_outputs")
            print(f"\nProperly ran the different set of files through for: {check_type}!!!!\n")
        except AssertionError:
            raise AssertionError(f"Unable to properly run the different set of files through for: {check_type}")

    def check_outputs(self, final_output_dir, meta_path):
        try:
            assert os.path.isfile(f"{final_output_dir}/errors/annotation_error.txt")
            assert os.path.isfile(f"{final_output_dir}/errors/output.unmapped_features.txt")
        except AssertionError:
            raise AssertionError(f"Expected error files not found in {final_output_dir}/errors")
        samples = self.get_samples(meta_path)
        for sample in samples:
            for output_type, ext in zip(['fasta', 'liftoff', 'tbl'], ['.fasta', '_reformatted.gff', '.tbl']):
                if not os.path.isfile(f"{final_output_dir}/{output_type}/{sample}{ext}"):
                    raise AssertionError(f"Could not the following file: {sample}{ext} in {output_type}{final_output_dir}")

if __name__ == "__main__":
    liftoff_submission = LiftoffSubmission()
    liftoff_submission.run_main()
