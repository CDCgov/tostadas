import os 
import pytest
import glob
import shutil

# import the module for splitting fasta
import sys
sys.path.append(".")
sys.path.append("..")
from bin.annotation_utility import MainUtility as main_util


def test_main():

    # initialize a few parameters to test
    dir_name = 'test_main_workflow'
    meta_dir_name = 'test_meta_outputs'
    lift_dir_name = 'test_liftoff_outputs'
    sub_dir_name = 'test_sub_outputs'
    batch_name = 'batch_test'

    # initialize the checks class/methods + for utility
    metadata_checks = Metadata(path_to_meta_dir=f"{dir_name}/{meta_dir_name}")
    liftoff_checks = Liftoff(path_to_lift_dir=f"{dir_name}/{lift_dir_name}")
    submission_checks = Submission(path_to_sub_dir=f"{dir_name}/{sub_dir_name}/liftoff", batch_name=batch_name)
    util = UtilityFunctions()

    # run the main workflow command + output directory = main workflow
    os.system (
        f"nextflow run main.nf -profile test,docker --submission_wait_time 2 --submission_database all --output_dir {dir_name} " + \
        f"--val_output_dir {meta_dir_name} --final_liftoff_output_dir {lift_dir_name} --submission_output_dir {sub_dir_name} " + \
        f"--batch_name {batch_name} --submission_database all"
    )

    # check that the proper outputs are generated in the custom output directory
    assert os.path.exists(f"{dir_name}")

    for key,value in {'meta': meta_dir_name, 'lift': lift_dir_name, 'sub': sub_dir_name}.items():
        assert os.path.exists(f"{dir_name}/{value}")
        if key == 'meta':
            metadata_checks.meta_check_main()
        elif key == 'lift':
            liftoff_checks.liftoff_check_main()
        elif key == 'sub':
            submission_checks.submission_check_main(initial_or_update='both')

    # call the submission entrypoint
    util.call_submission (
        output_dir=dir_name,
        meta_dir_name=meta_dir_name,
        lift_dir_name=lift_dir_name,
        sub_dir_name=sub_dir_name,
        batch_name=batch_name
    )

    # run the submission check 
    submission_checks = Submission(path_to_sub_dir=f"{dir_name}/{sub_dir_name}", batch_name=batch_name)
    submission_checks.submission_check_main(initial_or_update='both')


@pytest.mark.run(order=1)
def test_meta_val():

    # initialize some other variables
    output_dir = "test_meta_val"
    meta_dir = "metadata_outputs_test"

    # initialize the checks class/methods + for utility
    metadata_checks = Metadata(path_to_meta_dir=f"{output_dir}/{meta_dir}")

    # run metadata validation entrypoint
    os.system (
        f"nextflow run main.nf -profile test,docker -entry only_validation --output_dir {output_dir} " + \
        f"--val_output_dir {meta_dir}"
    )

    # run the metadata checks 
    metadata_checks.meta_check_main()


@pytest.mark.run(order=2)
def test_liftoff():

    # initialize some other variables
    output_dir = "test_liftoff"
    lift_dir = "liftoff_outputs_test"

    # initialize the checks class/methods + for utility
    liftoff_checks = Liftoff(path_to_lift_dir=f"{output_dir}/{lift_dir}")
    util = UtilityFunctions()

    # run liftoff entrypoint
    os.system (
        f"nextflow run main.nf -profile test,docker -entry only_liftoff --output_dir {output_dir} " + \
        f"--final_liftoff_output_dir {lift_dir}"
    )
    assert os.path.exists(f"{output_dir}/{lift_dir}")

    # check the liftoff outputs 
    liftoff_checks.liftoff_check_main()


@pytest.mark.run(order=3)
def test_initial_sub():

    # initialize some other variables
    output_dir = "test_submission"
    meta_dir = "test_meta_val/metadata_outputs_test"
    lift_dir = "test_liftoff/liftoff_outputs_test"
    sub_dir = "submission_outputs_test"
    batch_name = "batch_test"

    # initialize the checks class/methods
    submission_checks = Submission(path_to_sub_dir=f"{output_dir}/{sub_dir}", batch_name=batch_name)
    util = UtilityFunctions()

    # run the initial submission entrypoint
    os.system (
        f"nextflow run main.nf -profile test,docker -entry only_initial_submission --output_dir {output_dir} " + \
        f"--submission_output_dir {sub_dir} --batch_name {batch_name} --submission_database all --submission_only_meta {util.root_dir}/{meta_dir}/*/tsv_per_sample " + \
        f"--submission_only_fasta {util.root_dir}/{lift_dir}/*/fasta --submission_only_gff {util.root_dir}/{lift_dir}/*/liftoff"
    )

    # run the submission checks
    submission_checks.submission_check_main(initial_or_update='initial')


@pytest.mark.run(order=4)
def test_update_sub():

    # initialize some other variables
    output_dir = "test_update_submission"
    batch_name = "batch_test"

    # initialize the checks class/methods
    submission_checks = Submission(path_to_sub_dir=f"test_submission/submission_outputs_test", batch_name=batch_name)
    util = UtilityFunctions()

    # run the update submission entrypoint
    os.system (
        f"nextflow run main.nf -profile test,docker -entry only_update_submission " + \
        f"--batch_name {batch_name} --processed_samples {util.root_dir}/test_submission/submission_outputs_test/"
    )

    # run the submission checks
    submission_checks.submission_check_main(initial_or_update='update')


class OutputChecks(object):
    def __init__(self):
        self.util = UtilityFunctions()

class Metadata(OutputChecks):
    def __init__(self, path_to_meta_dir):
        OutputChecks.__init__(self)
        self.path_to_meta_dir = path_to_meta_dir

    def meta_check_main(self):
        # cycle through the main directories 
        for dir_name in ['errors', 'tsv_per_sample']:
            # check that the directory name is created
            assert glob.glob(f"{self.path_to_meta_dir}/*/{dir_name}")
            if dir_name == 'errors':
                self.check_errors(dir_name=dir_name)
            elif dir_name == 'tsv_per_sample':
                self.check_tsvs(dir_name=dir_name)
            
    def check_errors(self, dir_name):
        # get the directory paths within errors
        sub_dir_ls = glob.glob(f"{self.path_to_meta_dir}/*/{dir_name}/*")
        # cycle through expected files 
        for sub_dir in ["checks.tsv", "full_error.txt"]:
            assert glob.glob(f"{self.path_to_meta_dir}/*/{dir_name}/{sub_dir}")[0] in sub_dir_ls
            # read in the checks.tsv to make sure properly populated
            if sub_dir == 'checks.tsv':
                df = pd.read_csv(glob.glob(f"{self.path_to_meta_dir}/*/{dir_name}/{sub_dir}")[0], delimiter='\t', header=None)
                df.columns = ['sample_name', *df.iloc[0].tolist()[1:]]
                # check that proper number of header values exist + number of samples
                assert len(df.keys()) == 8
                assert len(df['sample_name']) == 8

    def check_tsvs(self, dir_name):
        # check the proper number of sample files exist
        assert len(glob.glob(f"{self.path_to_meta_dir}/*/{dir_name}/*.tsv")) == 7
        for tsv_file in glob.glob(f"{self.path_to_meta_dir}/*/{dir_name}/*.tsv"):
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


class Liftoff(OutputChecks):
    def __init__(self, path_to_lift_dir):
        OutputChecks.__init__(self)
        self.path_to_lift_dir = path_to_lift_dir
        self.list_of_samples = ['FL0004', 'FL0015', 'IL0005', 'NY0006', 'NY0007', 'OH0002', 'TX0001']

    def liftoff_check_main(self):
        # cycle through the main directories 
        for dir_name in ['errors', 'fasta', 'liftoff', 'tbl']:
            # check that the directory exists 
            assert glob.glob(f"{self.path_to_lift_dir}/*/{dir_name}")
            if dir_name == 'errors':
                self.check_errors(dir_name=dir_name)
            elif dir_name == 'fasta':
                self.check_fasta(dir_name=dir_name)
            elif dir_name == 'liftoff':
                self.check_gffs(dir_name=dir_name)
            elif dir_name == 'tbl':
                self.check_tbls(dir_name=dir_name)

    def check_errors(self, dir_name):
        # get the list of paths within directory 
        sub_dir_ls = glob.glob(f"{self.path_to_lift_dir}/*/{dir_name}/*")

        # check outputs within errors directory 
        if dir_name == 'errors':
            for sub_file in ['annotation_error.txt', 'output.unmapped_features.txt']:
                assert glob.glob(f"{self.path_to_lift_dir}/*/{dir_name}/{sub_file}")[0] in sub_dir_ls

    def check_fasta(self, dir_name):
        # create the test fasta directory 
        if os.path.exists("test_fasta"):
            shutil.rmtree("test_fasta")
        os.mkdir("test_fasta")

        # split the fasta and get sample names + use the default one
        self.util.ext_util.split_fasta (
            fasta_path=f"{self.util.root_dir}/input_files/trialData.fasta",
            fasta_output=f"test_fasta/"
        )

        # check that it worked fine 
        new_fastas = glob.glob('test_fasta/*')
        orig_fastas = glob.glob(f"{self.path_to_lift_dir}/*/{dir_name}/*")
        assert len(orig_fastas) == 7
        assert len(orig_fastas) == len(new_fastas)
        for file_name in orig_fastas:
            fasta_lines = self.util.read_file_lines (
                path_to_file=file_name
            )
            fasta_sample_name = fasta_lines[0].split('>')[1]
            assert fasta_sample_name.strip() in self.list_of_samples
            assert fasta_sample_name.strip() == file_name.split('/')[-1].split('.')[0].strip()

    def check_gffs(self, dir_name):
        for sub_file in [x for x in glob.glob(f"{self.path_to_lift_dir}/*/{dir_name}/*")]:
            gff_lines = self.util.read_file_lines (
                path_to_file=sub_file
            )
            for line_idx in range(len(gff_lines)):
                line = gff_lines[line_idx].split('\t')
                if line_idx > 2:
                    if line_idx == 3:
                        assert True in [x == 'repeat_region' for x in line]
                    else:
                        assert True in [x == 'repeat_region' or x == 'gene' or x == 'CDS' or x == 'misc_feature' for x in line]
                        assert line[1] == 'Liftoff'
                        assert line[3].isnumeric() and line[4].isnumeric()
                        assert line[6] == '+' or line[6] == '-'

    def check_tbls(self, dir_name):
        # read each of the tables in and check content 
        for sub_file in [x for x in glob.glob(f"{self.path_to_lift_dir}/*/{dir_name}/*")]:
            tbl_lines = self.util.read_file_lines(
                path_to_file=sub_file
            )
            sample_name = sub_file.split('/')[-1].split('.')[0].strip()
            assert f">Feature {sample_name}"


class Submission(OutputChecks):
    def __init__(self, path_to_sub_dir, batch_name):
        OutputChecks.__init__(self)
        self.path_to_sub_dir = path_to_sub_dir
        self.batch_name = batch_name
        self.list_of_samples = ['FL0004', 'FL0015', 'IL0005', 'NY0006', 'NY0007', 'OH0002', 'TX0001']
    
    def submission_check_main(self, initial_or_update):
        batch_dirs = glob.glob(f"{self.path_to_sub_dir}/*")
        assert len(batch_dirs) == 7
        for directory in batch_dirs:
            # check that proper batch name was used 
            assert directory.split('/')[-1].split('.')[0].strip() == 'batch_test'
            # check that the proper sample names was used 
            sample_name = directory.split('/')[-1].split('.')[1].strip()
            assert sample_name in self.list_of_samples
            self.list_of_samples.remove(directory.split('/')[-1].split('.')[1].strip())
            # check that the proper sub directories exist 
            self.check_submit_info (
                initial_or_update=initial_or_update, 
                directory=directory,
                sample_name=sample_name
            )

    @staticmethod
    def check_submit_info(initial_or_update, directory, sample_name):
        if initial_or_update == 'initial' or initial_or_update == 'both':
            assert os.path.exists(f"{directory}/initial_submit_info/{sample_name}_initial_submit_info")
            assert os.path.exists(f"{directory}/initial_submit_info/{sample_name}_initial_terminal_output.txt")
        elif initial_or_update == 'update' or initial_or_update == 'both':
            assert os.path.exists(f"{directory}/update_submit_info/{sample_name}_update_terminal_output.txt")


class UtilityFunctions():
    def __init__(self):
        self.root_dir = '/'.join(__file__.split('/')[:-2])
        self.ext_util = main_util()

    def call_submission(self, output_dir, meta_dir_name, lift_dir_name, sub_dir_name, batch_name):
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
            f"--submission_only_gff {self.root_dir}/{output_dir}/{lift_dir_name}/*/liftoff/ --submission_output_dir {sub_dir_name} --batch_name {batch_name} " + \
            f"--submission_database all"
        )
        assert os.path.exists(f"{output_dir}/{sub_dir_name}")
    
    @staticmethod
    def read_file_lines(path_to_file):
        lines = open(glob.glob(path_to_file)[0], "r")
        lines = [x.strip() for x in lines]
        return lines
    
    @staticmethod
    def remove_all_files():
        """.DS_Store"""


if __name__ == "__main__":
	test_main()