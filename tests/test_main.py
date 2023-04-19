import os 
import pytest
import pandas as pd
import glob

# import the module for splitting fasta
from ..bin.annotation_utility import MainUtility as main_util


def test_main():

    # initialize the checks class/methods + for utility
    output_checks = OutputChecks()
    util = UtilityFunctions()

    # initialize a few parameters to test
    dir_name = 'main_workflow_test'
    meta_dir_name = 'meta_outputs_test'
    lift_dir_name = 'liftoff_outputs_test'
    sub_dir_name = 'sub_outputs_test'
    batch_name = 'batch_test'

    # run the main workflow command + output directory = main workflow
    os.system (
        f"nextflow run main.nf -profile test,docker --submission_wait_time 2 --submission_database all --output_dir {dir_name} " + \
        f"--val_output_dir {meta_dir_name} --final_liftoff_output_dir {lift_dir_name} --submission_output_dir {sub_dir_name} " + \
        f"--batch_name {batch_name}"
    )

    # check that the proper outputs are generated in the custom output directory
    assert os.path.exists(f"{dir_name}")

    for key,value in {'meta': meta_dir_name, 'lift': lift_dir_name, 'sub': sub_dir_name}.items():
        assert os.path.exists(f"{dir_name}/{value}")
        if key == 'meta':
            output_checks.check_meta_output(
                path_to_meta_dir=f"{dir_name}/{value}"
            )

    # call the submission entrypoint
    util.call_submission (
        output_dir=dir_name,
        meta_dir_name=meta_dir_name,
        lift_dir_name=lift_dir_name,
        sub_dir_name=sub_dir_name
    )


@pytest.mark.run(order=1)
def test_meta_val():

    # initialize the checks class/methods
    output_checks = OutputChecks()

    # initialize some other variables
    output_dir = "meta_val_test"
    meta_dir = "metadata_outputs_test"

    # run metadata validation entrypoint
    os.system (
        f"nextflow run main.nf -profile test,docker -entry only_validation --output_dir {output_dir} " + \
        f"--val_output_dir {meta_dir}"
    )

    # run the metadata checks 
    output_checks.check_meta_output (
        path_to_meta_dir=f"{output_dir}/{meta_dir}"
    )


@pytest.mark.run(order=2)
def test_liftoff():
    # initialize the checks class/methods
    output_checks = OutputChecks()

    # initialize some other variables
    output_dir = "liftoff_test"
    lift_dir = "liftoff_outputs_test"

    # run liftoff entrypoint
    os.system (
        f"nextflow run main.nf -profile test,docker -entry only_liftoff --output_dir {output_dir} " + \
        f"--final_liftoff_output_dir {lift_dir}"
    )
    assert os.path.exists(f"{output_dir}/{lift_dir}")


@pytest.mark.run(order=3)
def test_initial_sub():
    # initialize the checks class/methods
    output_checks = OutputChecks()

    # initialize some other variables
    output_dir = "submission_test"
    sub_dir = "submission_outputs_test"

    # run the initial submission entrypoint
    os.system (
        f"nextflow run main.nf -profile test,docker -entry only_liftoff --output_dir {output_dir} " + \
        f"--final_liftoff_output_dir {sub_dir}"
    )


@pytest.mark.run(order=4)
def test_update_sub():
    # initialize the checks class/methods
    output_checks = OutputChecks()

    # would have to check that it just ran + the general outputs


class UtilityFunctions():
    def __init__(self):
        self.root_dir = '/'.join(__file__.split('/')[:-2])

    def call_submission(self, output_dir, meta_dir_name, lift_dir_name, sub_dir_name):
        # initialize the checks class/methods
        output_checks = OutputChecks()

        # remove the previous submission files
        os.system (
            f"rm -rf {output_dir}/{sub_dir_name}"
        )
        assert not os.path.exists(f"{output_dir}/{sub_dir_name}")

        # call the submission entrypoint
        os.system (
            f"nextflow run main.nf -profile test,docker -entry only_submission --submission_wait_time 2 --output_dir {output_dir} " + \
            f"--submission_only_meta {self.root_dir}/{output_dir}/{meta_dir_name}/*/tsv_per_sample/ --submission_only_fasta {self.root_dir}/{output_dir}/{lift_dir_name}/*/fasta/ " + \
            f"--submission_only_gff {self.root_dir}/{output_dir}/{lift_dir_name}/*/liftoff/ --submission_output_dir {sub_dir_name}"
        )
        assert os.path.exists(f"{output_dir}/{sub_dir_name}")



class OutputChecks():
    def __init__(self):
        """
        """

    @staticmethod
    def check_meta_output(path_to_meta_dir):

        # cycle through the main directories 
        for dir_name in ['errors', 'tsv_per_sample']:

            # check that the directory name is created
            assert glob.glob(f"{path_to_meta_dir}/*/{dir_name}")

            # check the contents within the errors directory
            if dir_name == 'errors':
                # get the directory paths within errors
                sub_dir_ls = glob.glob(f"{path_to_meta_dir}/*/{dir_name}/*")
                # cycle through expected files 
                for sub_dir in ["checks.tsv", "full_error.txt"]:
                    assert glob.glob(f"{path_to_meta_dir}/*/{dir_name}/{sub_dir}")[0] in sub_dir_ls
                    # read in the checks.tsv to make sure properly populated
                    if sub_dir == 'checks.tsv':
                        df = pd.read_csv(glob.glob(f"{path_to_meta_dir}/*/{dir_name}/{sub_dir}")[0], delimiter='\t', header=None)
                        df.columns = ['sample_name', *df.iloc[0].tolist()[1:]]
                        # check that proper number of header values exist + number of samples
                        assert len(df.keys()) == 8
                        assert len(df['sample_name']) == 8

            # check the contents within the tsv_per_sample directory 
            elif dir_name == 'tsv_per_sample':
                # check the proper number of sample files exist
                assert len(glob.glob(f"{path_to_meta_dir}/*/{dir_name}/*.tsv")) == 7
                for tsv_file in glob.glob(f"{path_to_meta_dir}/*/{dir_name}/*.tsv"):
                    # read in the .tsv files to check content
                    df = pd.read_csv(tsv_file, delimiter='\t').iloc[0]
                    # check a few things 
                    sample_name = tsv_file.split('/')[-1].split('.')[0]
                    if sample_name == 'FL0015' or sample_name == 'OH0002':
                        infile_sample_name = 'TX0001'
                    else:
                        infile_sample_name = sample_name  
                    state = infile_sample_name[:2]
                    assert 'C.M. Gigante;' in df['author']
                    assert df['sample_name'] == sample_name
                    assert df['ncbi_sequence_name_biosample_genbank'] == f"MPXV_USA_2022_{infile_sample_name}"
                    assert df['geo_location'] == f"USA:{state}"


    @staticmethod
    def check_liftoff_output(path_to_lift_dir):
        
        # cycle through the main directories 
        for dir_name in ['errors', 'fasta', 'liftoff', 'tbl']:
            # check that the directory exists 
            assert glob.glob(f"{path_to_lift_dir}/*/{dir_name}")

            # get the list of paths within directory 
            sub_dir_ls = glob.glob(f"{path_to_lift_dir}/*/{dir_name}")

            # check outputs within errors directory 
            if dir_name == 'errors':
                for sub_file in ['annotation_error.txt', 'output.unmapped_features.txt']:
                    assert glob.glob(f"{path_to_lift_dir}/*/{dir_name}/{sub_file}")[0] in sub_dir_ls
            elif dir_name == 'fasta':
                # split the fasta and get sample name 
                """.DS_Store"""

            elif dir_name == 'liftoff':
                for sub_file in [x for x in glob.glob(f"{path_to_lift_dir}/*/{dir_name}/")]:
                    df = pd.read_csv(glob.glob(f"{path_to_lift_dir}/*/{dir_name}/{sub_file}")[0], delimiter='\t', header=None)
                    print(df)


if __name__ == "__main__":
	test_main()