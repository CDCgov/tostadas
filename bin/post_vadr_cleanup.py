#!/usr/bin/env python3

import argparse
import os
import pandas as pd 
import re
import shutil

# import utility functions
from annotation_utility import MainUtility as main_util
from annotation_utility import GFFChecksUtility as gff_checks_util


def vadr_main(): 
    # get the parameters
    args = get_args().parse_args()
    parameters = vars(args)

    # get the path for outputs
    meta_filename = parameters['meta_path'].split('/')[-1].split('.')[0]
    parameters['output_path'] = f"{parameters['vadr_outdir']}/{meta_filename}/transformed_outputs"

    # initialize the directory structure + move the original input files into this location
    shutil.copytree(parameters['vadr_outputs'], f"{parameters['vadr_outdir']}/{meta_filename}/original_outputs")
    for dir_name in ['', 'fasta', 'gffs', 'tbl', 'errors']:
        os.mkdir(f"{parameters['output_path']}/{dir_name}")

    # instantiate the class object 
    main_funcs = MainVADRFuncs(parameters)

    # split the fasta file and save it
    main_util.split_fasta (
        fasta_path=parameters['fasta_path'], 
        fasta_output=f"{parameters['output_path']}/fasta/"
    )

    # split the outputted tables into separate samples
    main_funcs.split_table()

    # cleanup the lines 
    main_funcs.line_cleanup()

    # convert the gff back to a table
    for sample in main_funcs.sample_info.keys():
        main_util.gff2tbl(
            samp_name=sample, 
            gff_loc=f"{parameters['output_path']}/gffs/{sample}_reformatted.gff",
            tbl_output=f"{parameters['output_path']}/tbl/"
        )


def get_args():
    parser = argparse.ArgumentParser(description="Parameters for Running VADR Annotation")
    parser.add_argument("--vadr_outdir", type=str, default='vadr_outputs', help="Name of vadr output directory")
    parser.add_argument("--vadr_outputs", type=str, help="Path to the vadr outputs")
    parser.add_argument("--fasta_path", type=str, help="Path to the input fasta file")
    parser.add_argument("--meta_path", type=str, help="Path to the input metadata file")
    return parser


class MainVADRFuncs:
    def __init__(self, parameters):
        self.parameters = parameters 
        self.sample_info = {}
        self.get_next_line = False
        self.gff_checks = VadrGFFChecks(parameters=parameters)
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
            
            # assert that there is not three repeat regions in the sample block (could cause issues)
            try:
                num_repeat_regions = len([x for x in self.sample_info[key] if 'repeat_region' in x])
                assert num_repeat_regions == 2
            except AssertionError:
                raise AssertionError(f"Found either less than or greater than two repeat regions in {key}: {num_repeat_regions}")
            
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
            else:
                raise ValueError(f"Did not find a second ITR in {sample}")

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
        try:
            repeat = 0
            for x in self.raw_strings:
                for y in x:
                    if "repeat_region" in y:
                        repeat += 1 
            assert repeat == 2
        except AssertionError:
            raise AssertionError(f"Found either less than or greater than two repeat regions in {sample}: {repeat} total found")

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
            self.line_dict = gff_checks_util.check_note (
                field_value_mapping=self.line_dict
            )

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
    
    def write_to_gff(self, sample):
        for line_info in self.final_samp_lines:

            # figure out if repeat region or not
            if line_info[1]['type'] == 'repeat_region':

                line_sub1 = self.write_line(line_info[1], sample, 'repeat_region')

            else:
                # write the first line
                line_sub1 = self.write_line(line_info[1], sample, 'gene')

                # check if you need to modify second line due to stop codon
                if line_info[0] is True:
                    line_info[1], self.stop_codon_flag = self.gff_checks.modify_line_after_stop(
                        line_dict=line_info[1], 
                        stop_codon_flag=self.stop_codon_flag, 
                        sample=sample
                )

                # write the second line 
                line_sub2 = self.write_line(line_info[1], sample, 'CDS')

            # write the rest of the fields to the strings (might have to refactor this... looks messy)
            rem_keys = line_info[1].copy()
            [rem_keys.pop(x) for x in ['coord1', 'coord2', 'type', 'orientation']]

            for key in rem_keys.keys():
                if key == 'ID':
                    line_sub1 += f"ID=gene-{line_info[1]['ID']}"
                    if line_info[1]['type'] != 'repeat_region':
                        line_sub2 += f"ID=cds-{line_info[1]['ID']}"
                else:
                    line_sub1 += f"{key}={line_info[1][key]}"
                    if line_info[1]['type'] != 'repeat_region':
                        line_sub2 += f"{key}={line_info[1][key]}"
                
                # now check if it is the last one... if it is not then add ;
                if key != list(rem_keys.keys())[-1]:
                    line_sub1 += ';'
                    if line_info[1]['type'] != 'repeat_region':
                        line_sub2 += ';'
            
            # finally write to gff 
            with open(f"{self.parameters['output_path']}/gffs/{sample}_reformatted.gff", 'a', encoding='utf-8') as gff: 
                self.new_gff.write(f"{line_sub1}\n")
                if line_info[1]['type'] != 'repeat_region':
                    self.new_gff.write(f"{line_sub2}\n")
            gff.close()
    
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


class VadrGFFChecks():
    def __init__(self, parameters):
        self.parameters = parameters 
        self.bad_codon_fields = ['missing_start_codon', 'missing_stop_codon', 'inframe_stop_codon']
        self.fields_to_drop = ['coverage', 'sequence_ID', 'matches_ref_protein', 'valid_ORF', 'valid_ORFs', 'extra_copy_number',
		                       'copy_num_ID', 'pseudogene', 'partial_mapping', 'low_identity']

    def check_stop_codon(self, line_dict):
        # now check for fields to drop in line dict + whether stop codon is present
        get_next_line = False
        for key in line_dict.keys():
            if key in self.fields_to_drop:
                line_dict.pop(key)
            if key in self.bad_codon_fields:
                get_next_line = True 
        return get_next_line, line_dict
    
    @staticmethod
    def modify_line_after_stop(line_dict, stop_codon_flag, sample):
        # now perform misc_feature changes (change type to misc_feature and replace in id)
        line_dict['ID'] = line_dict['ID'].replace(line_dict['type'].lower(), 'misc_feature')
        line_dict.pop('product')
        line_dict['type'] = 'misc_feature'
        stop_codon_flag[sample] = True
        return line_dict, stop_codon_flag
    
    @staticmethod
    def check_repeat_regions(line_dict, repeat_flag, sample, repeat_region_counter, check_second_repeat, index, second_itr_index):
        # check first repeat region that it starts at one
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
        else: 
            pass
            # raise ValueError(f"Found greater than 2 repeat regions in {sample}")
        return line_dict, repeat_flag, second_itr_index, check_second_repeat
    
    @staticmethod 
    def check_second_itr(samp_lines, repeat_flag, sample, second_itr_index):
        if max([int(samp_lines[second_itr_index][1]['coord1']), int(samp_lines[second_itr_index][1]['coord2'])]) < max([int(samp_lines[-1][1]['coord1']), int(samp_lines[-1][1]['coord2'])]):
            # make changes in samp lines to the second ITR 
            if samp_lines[second_itr_index][1]['orientation'] == '+':
                samp_lines[second_itr_index][1]['coord2'] = max([int(samp_lines[-1][1]['coord1']), int(samp_lines[-1][1]['coord2'])])
            else: 
                samp_lines[second_itr_index][1]['coord1'] = max([int(samp_lines[-1][1]['coord1']), int(samp_lines[-1][1]['coord2'])])
            repeat_flag['second_region'][sample] = True
        return repeat_flag, samp_lines


if __name__ == "__main__":
    vadr_main()