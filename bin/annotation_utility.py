#!/usr/bin/env python3

import gzip
import shutil
import os
import re
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
        out_name = f"{tbl_output}/{samp_name}.tbl"
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
class GFFChecks:
    def __init__(self, parameters=None):
        self.parameters = parameters
        self.bad_codon_fields = ['missing_start_codon', 'missing_stop_codon', 'inframe_stop_codon']
        self.fields_to_drop = [
            'coverage', 'sequence_ID', 'matches_ref_protein', 'valid_ORF', 'valid_ORFs',
            'extra_copy_number', 'copy_num_ID', 'pseudogene', 'partial_mapping', 'low_identity'
        ]

    def check_stop_codon(self, line_dict):
        get_next_line = False
        for key in list(line_dict.keys()):
            if key in self.fields_to_drop:
                line_dict.pop(key)
            if key in self.bad_codon_fields:
                get_next_line = True
        return get_next_line, line_dict

    def modify_line_after_stop(self, line_dict, stop_codon_flag, sample):
        line_dict['ID'] = line_dict['ID'].replace(line_dict['type'].lower(), 'misc_feature')
        line_dict.pop('product', None)
        line_dict['type'] = 'misc_feature'
        stop_codon_flag[sample] = True
        return line_dict, stop_codon_flag

    def check_repeat_regions(self, line_dict, repeat_flag, sample, repeat_region_counter, check_second_repeat, index, second_itr_index):
        if repeat_region_counter == 1:
            if int(line_dict['coord1']) != 1 and int(line_dict['coord2']) != 1:
                if line_dict['orientation'] == '+':
                    line_dict['coord1'] = 1
                else:
                    line_dict['coord2'] = 1
                repeat_flag['first_region'][sample] = True
        elif repeat_region_counter == 2:
            second_itr_index = index
            check_second_repeat = True
        return line_dict, repeat_flag, second_itr_index, check_second_repeat

    def check_second_itr(self, samp_lines, repeat_flag, sample, second_itr_index):
        end_coord = max(int(samp_lines[-1][1]['coord1']), int(samp_lines[-1][1]['coord2']))
        target_line = samp_lines[second_itr_index][1]
        if max(int(target_line['coord1']), int(target_line['coord2'])) < end_coord:
            if target_line['orientation'] == '+':
                target_line['coord2'] = end_coord
            else:
                target_line['coord1'] = end_coord
            repeat_flag['second_region'][sample] = True
        return repeat_flag, samp_lines

    @staticmethod
    def check_note(field_value_mapping):
        if 'note' in field_value_mapping and '#' in field_value_mapping['note']:
            field_value_mapping['note'] = field_value_mapping['note'].replace('#', '')
            if '#' in field_value_mapping['note']:
                raise AssertionError(f"Could not remove # from note: {field_value_mapping['note']}")
        return field_value_mapping

class MainVADRFuncs:
    def __init__(self, parameters):
        self.parameters = parameters 
        self.sample_info = {}
        self.get_next_line = False
        self.gff_checks = GFFChecks(parameters)
        self.stop_codon_flag = {}
        self.repeat_flag = {}
        self.table_fail_errors = {}
        self.repeat_region_counter = 0
        self.check_second_repeat = False
        self.second_itr_index = None

    def split_table(self): 
        """ splits the pass table and fail table into individual samples and store it
        """
        # get the name of the actual output folder from path + specify paths 
        dir_name = self.parameters['vadr_outputs'].split('/')[-1]
        pass_tbl = f"{self.parameters['vadr_outputs']}/{dir_name}.vadr.pass.tbl"
        fail_tbl = f"{self.parameters['vadr_outputs']}/{dir_name}.vadr.fail.tbl"

        # concatenate the tables together 
        new_tbl = f"{self.parameters['output_path']}/{dir_name}.vadr.cat.tbl"
        cat_cmd = f"cat {pass_tbl} {fail_tbl} > {new_tbl}"
        os.system(cat_cmd)

        # split the combined table into individual samples
        with open(new_tbl, 'r') as tbl: 
            lines = [line.strip() for line in tbl.readlines() if line.strip()]

            tbl.close() 

        # get where the sample names are
        indices = [x for x in range(len(lines)) if lines[x][0] == '>']
        for i in range(len(indices)): 
            key = lines[indices[i]].strip('>Feature').strip('\n').strip()
            if i != len(indices)-1:
                self.sample_info[key] = lines[indices[i]+1:indices[i+1]]
            else:
                self.sample_info[key] = lines[indices[i]+1:]
            
            # # assert that there is not three repeat regions in the sample block (could cause issues)
            # try:
            #     num_repeat_regions = len([x for x in self.sample_info[key] if 'repeat_region' in x])
            #     assert num_repeat_regions == 2
            # except AssertionError:
            #     raise AssertionError(f"Found either less than or greater than two repeat regions in {key}: {num_repeat_regions}")
            
        # using the sample names, update the two flag dictionaries
        self.stop_codon_flag = {key: False for key in self.sample_info.keys()}
        self.repeat_flag = {'first_region': {key: False for key in self.sample_info.keys()}, 'second_region': {key: False for key in self.sample_info.keys()}}

    def line_cleanup(self):
        self.get_new_error_file()
        for sample in self.sample_info.keys():
            self.final_samp_lines = []
            self.get_new_gff(sample)
            self.split_raw_strings(sample)
            self.clean_lines(sample)

            if self.check_second_repeat is True:
                self.repeat_flag, self.final_samp_lines = self.gff_checks.check_second_itr(
                    samp_lines=self.final_samp_lines,
                    repeat_flag=self.repeat_flag, 
                    sample=sample, 
                    second_itr_index=self.second_itr_index
                )

            # else:
            #     raise ValueError(f"Did not find a second ITR in {sample}")

            # write the sample information to gff 
            self.write_to_gff(sample)

            # reset the repeat region counter 
            self.repeat_region_counter = 0
            self.check_second_repeat = False
            self.second_itr_index = None

        self.update_error_file()
        
    def split_raw_strings(self, sample):
        # split the sample block from table into each line for the sample
        self.raw_strings = []
        markers = [i for i, x in zip(range(len(self.sample_info[sample])), self.sample_info[sample]) if x.split('\t')[-1] == 'gene' or 'repeat_region' in x]
        for m in range(len(markers)):
            if m != len(markers)-1:
                string_list = []
                self.raw_strings.append([self.sample_info[sample][i] for i in range(markers[m], markers[m+1])])
            else: 
                last_portion = self.sample_info[sample][markers[m]:len(self.sample_info[sample])]
                find_notes = [i for string, i in zip(last_portion, range(len(last_portion))) if 'Additional note(s) to submitter' in string]
                if len(find_notes) != 0:
                    # save the error and change the flag
                    table_fail_error = f"\n\tERROR FROM FAIL TABLE:\n\t\t"
                    table_fail_error += '\n\t\t'.join(last_portion[find_notes[0]:])
                    self.table_fail_errors[sample] = table_fail_error 
                    # write the remaining part to raw strings
                    self.raw_strings.append(last_portion[:find_notes[0]])
                else:
                    self.raw_strings.append(self.sample_info[sample][markers[m]:len(self.sample_info[sample])])

        try:
            assert True not in ['Additional notes(s) to submitter' in string for string in self.raw_strings] 
        except AssertionError:
            raise AssertionError(f"Notes was stored in the raw_strings list... assumes that 'Additional notes(s) to submitter' prefixes the entire error message. Please fix.")
        
        # assert that there is not three repeat regions in the sample block (could cause issues)
        # try:
        #     repeat = 0
        #     for x in self.raw_strings:
        #         for y in x:
        #             if "repeat_region" in y:
        #                 repeat += 1 
        #     assert repeat == 2
        # except AssertionError:
        #     raise AssertionError(f"Found either less than or greater than two repeat regions in {sample}: {repeat} total found")

    def clean_lines(self, sample):

        # split the line up properly 
        for line_list, i in zip(self.raw_strings, range(len(self.raw_strings))):
            # convert the line to dictionary 
            self.store_line_to_dict(
                line_list=line_list
            )
            # get the orientation 
            self.get_orientation()
            # check the stop codons 
            self.get_next_line, self.line_dict = self.gff_checks.check_stop_codon(
                line_dict=self.line_dict
            )
            # now check if the repeat region starts at one and the other repeat region extends to end 
            if self.line_dict['type'] == 'repeat_region':
                self.repeat_region_counter += 1
                self.line_dict, self.repeat_flag, self.second_itr_index, self.check_second_repeat = self.gff_checks.check_repeat_regions(
                    line_dict=self.line_dict, 
                    repeat_flag=self.repeat_flag, 
                    sample=sample, 
                    repeat_region_counter=self.repeat_region_counter, 
                    check_second_repeat=self.check_second_repeat, 
                    index=i, 
                    second_itr_index=self.second_itr_index
            )
            # check note to make sure it does not have a #
            self.line_dict = self.gff_checks.check_note(self.line_dict)
            # save line to list
            self.final_samp_lines.append([self.get_next_line, self.line_dict])

    def store_line_to_dict(self, line_list):
        # indices_to_loop = list(filter(lambda x: x != 2, [x for x in range(1, len(line_list))]))
        self.line_dict = {}
        for i in range(len(line_list)):
            if i == 0:
                self.line_dict['coord1'], self.line_dict['coord2'] = line_list[i].split('\t')[0], line_list[i].split('\t')[1]
                self.line_dict['type'] = line_list[i].split('\t')[-1]
            elif i == 1: 
                self.line_dict['gene'] = line_list[i].split('\t')[-1]
            elif line_list[i].split('\t')[0] == 'protein_id' or line_list[i].split('\t')[0] == 'ID':
                self.line_dict['ID'] = str(line_list[i].split('\t')[-1])
            else:
                if line_list[i].split('\t')[0] != self.line_dict['coord1'] and line_list[i].split('\t')[0] != self.line_dict['coord2']:
                    # fix up the individual line for the sample and write it 
                    splitted = line_list[i].split('\t')
                    self.line_dict[splitted[0]] = splitted[1]
    def format_attributes(self, line_dict, prefix):
        """
        Create GFF attribute string from line_dict, skipping coordinates and internal fields.
        """
        attributes = []
        for k, v in line_dict.items():
            if k in ['coord1', 'coord2', 'type', 'orientation']:
                continue
            if k == 'ID':
                attributes.append(f"ID={prefix}-{v}")
            else:
                attributes.append(f"{k}={v}")
        return ';'.join(attributes)

    def write_to_gff(self, sample):
        for line_info in self.final_samp_lines:
            is_repeat = line_info[1]['type'] == 'repeat_region'
            line_data = line_info[1]

            if is_repeat:
                line = self.write_line(line_data, sample, 'repeat_region')
                attributes = self.format_attributes(line_data, 'gene')
                line += attributes
                self.new_gff.write(f"{line}\n")
            else:
                # Gene line
                gene_line = self.write_line(line_data, sample, 'gene')
                gene_attrs = self.format_attributes(line_data, 'gene')
                # Stop codon check → change type to misc_feature
                if line_info[0]:
                    line_data, self.stop_codon_flag = self.gff_checks.modify_line_after_stop(
                        line_data, self.stop_codon_flag, sample
                    )
                # CDS line
                cds_line = self.write_line(line_data, sample, 'CDS')
                cds_attrs = self.format_attributes(line_data, 'cds')

                self.new_gff.write(f"{gene_line}{gene_attrs}\n")
                self.new_gff.write(f"{cds_line}{cds_attrs}\n")
    
    def get_new_gff(self, sample):
        self.new_gff = open(f"{self.parameters['output_path']}/gffs/{sample}_reformatted.gff", 'w', encoding='utf-8')
    
    def get_new_error_file(self):
        self.new_error_file = open(os.path.join(self.parameters['output_path'], 'errors/annotation_error.txt'), 'w', encoding='utf-8')
    
    def get_orientation(self):
        # strip any non numerical characters
        self.line_dict['coord1'] = re.sub(r'[^0-9]', '', self.line_dict['coord1'])
        self.line_dict['coord2'] = re.sub(r'[^0-9]', '', self.line_dict['coord2'])

        # get the orientation based on coordinates 
        if int(self.line_dict['coord1']) < int(self.line_dict['coord2']):
            # then forward (+)
            self.line_dict['orientation'] = '+'
            try: 
                assert (int(self.line_dict['coord1']) - int(self.line_dict['coord2'])) < 0 
            except AssertionError:
                raise AssertionError(f"Found coordinate1 < coordinate2 but this is incorrect!")
        elif int(self.line_dict['coord1']) > int(self.line_dict['coord2']):
            # then reversed (-)
            self.line_dict['orientation'] = '-'
            try: 
                assert (int(self.line_dict['coord1']) - int(self.line_dict['coord2'])) > 0 
            except AssertionError:
                raise AssertionError(f"Found coordinate1 > coordinate2 but this is incorrect!")
            # switch it for the sake of consistency 
            # self.line_dict['coord1'], self.line_dict['coord2'] = self.line_dict['coord2'], self.line_dict['coord1']
        else: 
            raise ValueError(f"Coordinates are potentially equal... double check!!!")

    def update_error_file(self):
        try:
            assert set(list(self.stop_codon_flag.keys())) == set(list(self.repeat_flag['first_region'].keys())) == set(list(self.repeat_flag['second_region'].keys()))
        except AssertionError:
            raise AssertionError(f"The dictionary for stop codon flags and the one for repeat flag have different keys as samples")

        with open(os.path.join(self.parameters['output_path'], 'errors/annotation_error.txt'), 'a') as error_file:
            for sample in self.stop_codon_flag.keys():

                # write the sample to the error . txt file
                error_file.write(f"{sample}:")

                if self.stop_codon_flag[sample] is True:
                    error_file.write(f"\n\tSTOP CODON CHECK:\n\t\tStop Codon Found in {sample}\n")
                else: 
                    error_file.write(f"\n\tSTOP CODON CHECK:\n\t\tNo Stop Codon Found in {sample}\n")
                
                # write the ITR error 
                ITR_error = f"\n\tITR CHECK:"

                if self.repeat_flag['first_region'][sample] is True:
                    ITR_error += f"\n\t\tFirst ITR does not extend to beginning in {sample}"
                else:
                    ITR_error += f"\n\t\tFirst ITR is good in {sample}"

                if self.repeat_flag['second_region'][sample] is True:
                    ITR_error += f"\n\t\tSecond ITR does not extend to end in {sample}\n"
                else:
                    ITR_error += f"\n\t\tSecond ITR is good in {sample}\n"
                
                error_file.write(ITR_error)

                # write the table fail error 
                if sample in self.table_fail_errors.keys(): 
                    # check whether or not the table fail errors needs to be written
                    error_file.write(f"{self.table_fail_errors[sample]}\n")
                
                error_file.write(f"\n")
        error_file.close()

    @staticmethod
    def write_line(line_dict, sample, type):
        return f"{sample}\tVADR\t{type}\t{line_dict['coord1']}\t{line_dict['coord2']}\t.\t{line_dict['orientation']}\t.\t"