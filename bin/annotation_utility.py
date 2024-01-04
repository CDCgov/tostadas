#!/usr/bin/env python3

import gzip
import shutil
import os
import glob


class MainUtility:
    """ Class constructor for the main utility functions shared between annotation pipelines 
    """
    def __init__(self):
        """
        """
    
    def split_fasta(self, fasta_path, fasta_output):
        """
        Parses fasta file and writes it
        Possible bash command to make it work but cannot get rid of hanging new space, switching to less efficent but working solution
        os.system('cat multiFasta | awk '{ if (substr($0, 1, 1)==">"){filename=(substr($0,2) ".fasta")} print$0>>filename close(filename) }'')
        """
        # check if the fasta file needs to be unzipped 
        if fasta_path.split('/')[-1].split('.')[-1] == 'gz':
            new_fasta_path = self.unzip_fasta(fasta_path)
            # now change the variable name to the proper directory 
            fasta_dir = self.get_dir(fasta_path=fasta_path)
            fasta_path = f"{fasta_dir}/{new_fasta_path.split('/')[-1]}"

        # get the fasta lines that non empty
        with open(fasta_path, "r") as fasta_input:
            fasta_lines = [line.strip() for line in fasta_input.readlines() if line.strip()]
            fasta_input.close()

        # get the delimiter for the fasta file 
        delimiter = self.get_fasta_delimiter(fasta_path=fasta_path)
        
        # loop through list and write the lines
        for line in fasta_lines:
            if delimiter in line:
                sample_name = line.split(delimiter)[-1]
                fasta_sample_out = open(f"{fasta_output}{sample_name}.fasta", "w")
                fasta_sample_out.write(f">{sample_name}\n")
            else:
                fasta_sample_out.write(line)
                fasta_sample_out.close()

    def unzip_fasta(self, fasta_path):
        """ Unzips fasta.gz compressed files
        """
        # get the directory to the fasta_path
        fasta_dir = self.get_dir(fasta_path=fasta_path)

        with gzip.open(fasta_path, 'rb') as f_in:
            # get the extension for the file 
            extension = fasta_path.split('/')[0].split('.')[1]
            # get the descriptor for the file 
            new_fasta_path = f"{fasta_dir}/unzipped_fasta.{extension}"
            descriptor = self.change_file_permissions(file_path=new_fasta_path)
            with open(descriptor, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        return new_fasta_path

    @staticmethod
    def get_dir(fasta_path):
        if '/' in fasta_path:
            fasta_dir = '/'.join(fasta_path.split('/')[:-1])
        else:
            fasta_dir = '.'
        return fasta_dir

    @staticmethod
    def change_file_permissions(file_path):
        """ Changes permissions for the file that is being written/created
        """
        # change some meta properties of the file to be written
        descriptor = os.open (
            path=file_path,
            flags= (
                os.O_WRONLY  # access mode: write only
                | os.O_CREAT  # create if not exists
                | os.O_TRUNC  # truncate the file to zero
            ),
            mode=0o777
        )
        return descriptor
    
    def get_fasta_sample_names(self, fasta_path):
        """ Gets the sample names from the fasta file 
        """
        fasta_file = open(fasta_path, "r")
        # check the extension of the file to determine delimiter to use
        delimiter = self.get_fasta_delimiter(fasta_path=fasta_path)
        # cycle through the fasta to get names
        fasta_names = []
        while True:
            line = fasta_file.readline()
            if not line:
                break
            if line[0] == delimiter and line.strip()[1:].split('_')[0] != 'no' and line.strip()[1:].split('_')[0] != 'not':
                name = line.strip()[1:]
                if name not in fasta_names:
                    fasta_names.append(name)
        try:
            assert bool(fasta_names) is True
        except AssertionError:
            raise AssertionError(f'The names in the fasta file could not be properly parsed')
        return fasta_names

    @staticmethod
    def get_fasta_delimiter(fasta_path):
        """ Determines whether file is FQ or Fasta 
        """
        last_part = fasta_path.split('/')[-1]
        if '.fq' in last_part:
            delimiter = '@'
        elif '.fasta' in last_part:
            delimiter = '>'
        else:
            raise ValueError(f"Not valid file type for fasta: {fasta_path}")
        return delimiter
    
    @staticmethod
    def gff2tbl(samp_name, gff_loc, tbl_output):
        """ Converts the reformatted gff file to a table
        """
        # read in the reformatted gff file from above
        gff_input = open(f"{gff_loc}", "r")
        # specify the output tbl file path and open it up
        out_name = f"{tbl_output}{samp_name}.tbl"
        tbl = open(out_name, "w")

        # write fasta header for the sample name
        tbl.write('>' + 'Feature' + ' ' + samp_name + '\n')
        # iterate and skip the first two header rows
        for line in gff_input:
            line = line.split("\t")
            if not line[0].startswith('#'):
                # get the important features that we will write to tbl file
                feature = line[0]
                _type = line[2]
                start = line[3]
                stop = line[4]
                strand = line[6]
                if strand == '+':
                    tbl.write(start + '\t' + stop + '\t' + _type + '\n')
                else:
                    tbl.write(stop + '\t' + start + '\t' + _type + '\n')

                anns = line[8].split(';')
                check_unwanted_vals = [x for x in anns if x in ['\n', '\t', '/n', '/t']]
                if check_unwanted_vals:
                    [anns.remove(x) for x in check_unwanted_vals]
                # check if unwanted characters in there
                for x in range(len(anns)):
                    anns[x] = anns[x].replace('%3B', ';')
                    anns[x] = anns[x].replace('%2C', ',')
                    try:
                        assert '%3B' not in anns[x] and '%2C' not in anns[x]
                    except AssertionError:
                        raise AssertionError(f"Could not replace %3B or %2C from line")

                for item in anns[0:-2]:
                    item = item.split('=')
                    tbl.write('\t' + '\t' + '\t' + item[0] + '\t' + item[1] + '\n')
                    
                item = anns[-1].split('=')
                tbl.write('\t' + '\t' + '\t' + item[0] + '\t' + item[1])

            if not line:
                break


class GFFChecksUtility:
    def __init__(self):
        """
        """
    
    @staticmethod
    def check_note(field_value_mapping):
        # now check whether a # sign is in the note section
        if 'note' in list(field_value_mapping.keys()) and '#' in field_value_mapping['note']:
            field_value_mapping['note'] = field_value_mapping['note'].replace('#', '')
            try:
                assert '#' not in field_value_mapping['note']
            except AssertionError:
                raise AssertionError(
                    f"Found a # sign in the note field that could not be removed: {field_value_mapping['note']}")
        return field_value_mapping
    
