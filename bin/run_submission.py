import argparse
import os
import glob
import subprocess


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
    parser.add_argument("--launch_dir", type=str, help='Path to directory containing main.nf')
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
            self.parameters['nf_output_dir'] = f"{self.parameters['launch_dir']}/{self.parameters['nf_output_dir']}"
            if self.parameters['entry_flag'].lower() != 'true':
                self.parameters['validated_meta_path'] = f"{self.parameters['launch_dir']}/{self.parameters['validated_meta_path']}"
                self.parameters['lifted_fasta_path'] = f"{self.parameters['launch_dir']}/{self.parameters['lifted_fasta_path']}"
                self.parameters['lifted_gff_path'] = f"{self.parameters['launch_dir']}/{self.parameters['lifted_gff_path']}"

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
        dirs_to_check = {
            'root': f"{self.parameters['nf_output_dir']}/{self.parameters['submission_output_dir']}",
            'terminal': f"{self.parameters['nf_output_dir']}/{self.parameters['submission_output_dir']}/terminal_outputs",
            'commands': f"{self.parameters['nf_output_dir']}/{self.parameters['submission_output_dir']}/commands_used"
        }
        for path in dirs_to_check: 
            if not os.path.isdir(dirs_to_check[path]):
                os.mkdir(dirs_to_check[path])
        
        # sort file lists to ensure they are in the same order, assumes you have alpha prefix
        meta_files = sorted(meta_files)
        fasta_files = sorted(fasta_files)
        gff_files = sorted(gff_files)

        for meta, fasta, gff in zip(meta_files, fasta_files, gff_files):
            # get the sample names and specify command
            sample_name = (meta.split('/')[-1]).split('.')[0]
            command = f"python {self.parameters['submission_script']} submit --unique_name {self.parameters['batch_name']}.{sample_name} --fasta {fasta}" + \
                      f" --metadata {meta} --gff {gff} --config {self.parameters['config']} --{self.parameters['prod_or_test']}"

            # write the text file with information
            with open(f"{dirs_to_check['commands']}/submit_info_{sample_name}.txt", 'w') as f:
                f.write(f"{meta}\n")
                f.write(f"{fasta}\n")
                f.write(f"{gff}\n")
                f.write(f"{command}\n")
            f.close()
            # store the final command within dictionary
            commands[sample_name] = command

        # cycle through the commands stored and initiate subprocesses for these + write terminal output to file
        for key in commands.keys():
            file_ = open(f"{dirs_to_check['terminal']}/terminal_output_{key}.txt", "w+")
            subprocess.run(commands[key], shell=True, stdout=file_)
            file_.close()

    def update_submission(self):
        """ Calls update submission
        """
        os.system(f"python {self.parameters['submission_script']} update_submissions")

if __name__ == "__main__":
    submit_to_database = SubmitToDatabase()
    submit_to_database.main()