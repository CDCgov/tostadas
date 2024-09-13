#!/usr/bin/env python3

# Created by Zelaikha Yosufzai

import pandas as pd
import warnings
import os
import re
import argparse
import sys

# import utility functions 
from annotation_utility import MainUtility
#from annotation_utility import GFFChecksUtility as gff_checks_util

def get_args():        
    """get comand-line arguments"""
        
    parser = argparse.ArgumentParser(description="Parameters for Running Annotation Submission", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        
    parser.add_argument("--repeatm_gff", type=str, help="GFF file from Repeat Masker \n", required=True)
    parser.add_argument("--liftoff_gff", type=str, help="GFF file from Liftoff \n", required=True)
    parser.add_argument("--refgff", type=str, help="Reference GFF to gather the ITR attributes and sample ID \n", required=True)
    parser.add_argument("--fasta", type=str, help="FASTA file for sample \n", required=True)
    parser.add_argument("--outdir", type=str, default=".", help="Output directory, defualt is current directory")
    parser.add_argument("--sample_name", type=str, default=".", help="Sample name")
        
    args = parser.parse_args()
        
    return args

def count_rows_starting_with_comment(file_path):
    count = 0
    with open(file_path, 'r') as file:
        for line in file:
            if line.startswith('#'):
                count += 1
            else:
                break  # Stop counting once a line is encountered that doesn't start with '#'
    return count

def annotation_main():
    """ Main function for calling the annotation transfer pipeline
    """
    #warnings.filterwarnings('ignore')

    # get all parameters needed for running the steps
    args = get_args()
    
    #create output directory if need be
    if not os.path.exists(args.outdir):
        os.makedirs(args.outdir)
    
    ##set header for gff files; following gff3 format
    headerList = ['seq_id', 'source', 'type', 'start', 'end', 'score', 'strand', 'phase', 'attributes']
    
    #####GATHER REF INFO#####
    #load in repeatmasker gff skip commented lines that dont belong in dataframe
    #ref_gff = pd.read_csv(args.refgff, delimiter='\t', skip_blank_lines=True, names=headerList, comment='#')
    ref_gff = pd.read_csv(args.refgff, delimiter='\t', skip_blank_lines=True, names=headerList, skiprows=count_rows_starting_with_comment(args.refgff))
    
    #gather ref sample id
    ref_id=ref_gff['seq_id'][0]
    print(f'refgff is {args.refgff}')
    #print(ref_gff.head())
    #gather index of attributes for first and second ITRs; needed for repeatmasker ITR attributes
    #print(ref_gff[ref_gff['attributes'][0]])
    first_ITR_index=ref_gff[ref_gff['attributes'].str.contains("ITR",na=False)].index[0]
    last_ITR_index=ref_gff[ref_gff['attributes'].str.contains("ITR",na=False)].index[-1]
    print(first_ITR_index,last_ITR_index)
    #gather the acutal attributes from the index
    first_ITR_refattr=ref_gff.loc[first_ITR_index,'attributes']
    last_ITR_refattr=ref_gff.loc[last_ITR_index,'attributes']
    print(first_ITR_refattr, last_ITR_refattr)
    #####RUN MAIN PROCESS#####

    repMannotation_prep = RepeatMasker_Annotations(args.repeatm_gff, headerList, first_ITR_refattr, last_ITR_refattr, args.outdir)
    samp_name = '.'.join(args.fasta.split('.')[:-1])
    #samp_name=repMannotation_prep.sample_info()[0]
    #repMannotation_prep.repM_prep_main()
    
    LOannotation_prep=Liftoff_Annotations(args.liftoff_gff, headerList, args.sample_name, args.outdir)
    #LOannotation_prep.LO_prep_main()
    #repMannotation_prep.sample_info()
    new_gff=concat_gffs(args.liftoff_gff, repMannotation_prep.repM_prep_main(), LOannotation_prep.LO_prep_main(), ref_id, args.sample_name, args.outdir)
    
    new_gff.concat_LO_RM()
   
    #####CREATE TBL FILE#####
    main_util=MainUtility()
    main_util.gff2tbl(
        samp_name=samp_name,
        gff_loc=f"{args.outdir}/{args.sample_name}_reformatted.gff",
        tbl_output=f"{args.outdir}/"
    )

class RepeatMasker_Annotations:
    def __init__(self, rem_infile, headerList, first_ITR_refattr, last_ITR_refattr, outdir):
        self.repeatMGFF = rem_infile
        self.headerList=headerList
        self.first_ITR_refattr= first_ITR_refattr
        self.last_ITR_refattr= last_ITR_refattr
        self.samp_name=''
        self.samp_end=None
        self.first_ITR=None
        self.last_ITR=None
        self.outdir=outdir
    
    #@staticmethod
    def repM_prep_main(self):
        """ Main prep function for gathering sample information, cleaning up the repeat masker gff, and checking itr are correct (if not it fixes them)
        """
        # gather sample info
        self.sample_info()
        # clean up repeat masker gff
        ###self.cleanup_repeat_masker_gff()
        rem_gff = self.cleanup_repeat_masker_gff()
        # check itr lengths and positions
        self.check_itr(rem_gff)
       
        return rem_gff
 
    def sample_info(self):
        """Gather sample name and end positions from second line in RepeatMasker gff output, use for itr check
        """
        with open(self.repeatMGFF, 'r') as f:
            for i, line in enumerate(f):
                if i == 1:
                    samp_info=line.split(' ')
            self.samp_name=samp_info[1]
            #self.samp_start=int(samp_info[2])
            try:
                self.samp_end=int(samp_info[3].strip())
            except:
                raise Exception(f"A fourth element is not present in: {samp_info}")
        return self.samp_name, self.samp_end
        
    def cleanup_repeat_masker_gff(self):
        #load in repeatmasker gff skip the first two lines that dont belong in dataframe
        rem_gff = pd.read_csv(self.repeatMGFF, delimiter='\t', skip_blank_lines=True, names=self.headerList, skiprows=count_rows_starting_with_comment(self.repeatMGFF))
        #correct repeat region labels; repeatmasker labels repeat regions as dispersed_repeat 
        rem_gff['type'] = rem_gff['type'].replace({'dispersed_repeat': 'repeat_region'}, regex=True)
        
        #filter dataframe to only show ITR and AT repeat region matches; only ones we care about
        rem_gff=rem_gff[rem_gff["attributes"].str.contains("\(AT\)n|\(T\)n|ITR", regex=True)]
        
        #saving index of the first and last(aka second) ITR, AT, and T regions        
        self.first_ITR=rem_gff[rem_gff['attributes'].str.contains("ITR")].index[0]
        self.last_ITR=rem_gff[rem_gff['attributes'].str.contains("ITR")].index[-1]
        at_region=rem_gff[rem_gff['attributes'].str.contains("\(AT\)n")].index.values
        t_region=rem_gff[rem_gff['attributes'].str.contains("\(T\)n")].index.values
        
        if self.first_ITR == self.last_ITR:
            print("ERROR: Only one ITR present")
            error = "Only one ITR present!"
            itr_errors.append(error)
                  
        #replaced attributes with same ones as ref; repeatmasker doesnt have appropriate attribute values
        rem_gff.at[self.first_ITR,'attributes'] = self.first_ITR_refattr
        rem_gff.at[self.last_ITR,'attributes'] = self.last_ITR_refattr
        rem_gff.loc[at_region,'attributes'] = f'ID=AT-{self.samp_name}-RPT;note=hypervariable AT repeat region'
        rem_gff.loc[t_region,'attributes'] = f'ID=T-{self.samp_name}-RPT;note=hypervariable T repeat region'
        
        #filter one more time to remove bad ITR matches
        rem_gff=rem_gff[~rem_gff["attributes"].str.contains("Target", regex=True)]
        
        return rem_gff
        
    def check_itr(self, rem_gff):
        """ For checking all ITR information is present and correct... raises flags and writes errors
        """
        itr_errors = []
        #save value of start and end position of ITRs
        first_region_coord1 = rem_gff.loc[self.first_ITR,'start']
        first_region_coord2 = rem_gff.loc[self.first_ITR,'end']
        second_region_coord1 = rem_gff.loc[self.last_ITR,'start']
        second_region_coord2 = rem_gff.loc[self.last_ITR,'end']
        
        if self.first_ITR == self.last_ITR:
            print("ERROR: Only one ITR present")
            error = "Only one ITR present!"
            itr_errors.append(error)

        # check that the first ITR has coordinates that start at 1, if not output so in errors file
        if rem_gff.loc[self.first_ITR,'start'] !=1:
            error = f"First repeat region coordinates does not start at 1: ({first_region_coord1}, {first_region_coord2}) in {self.samp_name} gff"
            itr_errors.append(error)
            # change the ITR to start at 1
            rem_gff.loc[self.first_ITR,'start'] = 1

        # Check that the final coordinate in the second ITR extends to the end, if not output so in errors file
        if rem_gff.loc[self.last_ITR,'end'] < self.samp_end:
            error = f"Second repeat region does not extend to end in {self.samp_name} gff file: {second_region_coord1}, {second_region_coord2} coordinates " \
                    f"with overall seq length of {self.samp_end}"
            itr_errors.append(error)
            # change the last coordinate of second ITR to extend to end
            rem_gff.loc[self.last_ITR,'end'] = self.samp_end

        # check that both repeat_regions are the same length if they are not output so in errors file
        length_region0 = first_region_coord2 - 1
        length_region1 = self.samp_end - second_region_coord1
        if length_region0 != length_region1:
            error = f"First repeat region length of {length_region0} at {1, first_region_coord2} does not " \
                    f"equal second repeat region length of {length_region1} at {second_region_coord1, self.samp_end} " \
                    f"in {self.samp_name}.repeatmasker-orig.out.gff file"
            itr_errors.append(error)
            
        with open(f"{self.outdir}/{self.samp_name}_annotation_error.txt", 'w') as out:
            out.write(f"{self.samp_name}:\n")
            # write the ITR check
            out.write(f"\n\tITR CHECK:\n")
            if len(itr_errors) !=0:
                for itr_error in itr_errors:
                    out.write(f"\t{itr_error}\n")
            else:
                out.write(f"\tNo ITR errors\n")
                
        return  rem_gff

class Liftoff_Annotations:
    def __init__(self, liftoff_infile, headerList, samp_name, outdir):
        self.headerList=headerList
        self.liftoffGFF = liftoff_infile
        self.samp_name=samp_name
        self.outdir=outdir
    def LO_prep_main(self):
        """ Main prep function for calling split_fasta, split gff for itr mapping, and load_meta
        """
        fields_to_drop = ['coverage', 'sequence_ID', 'matches_ref_protein', 'valid_ORF', 'valid_ORFs', 'extra_copy_number',
                              'copy_num_ID', 'pseudogene', 'partial_mapping', 'low_identity']
        #load in liftoff gff with same headers as Repeatmasker and skip commented lines at dont belong to dataframe
        lo_gff = pd.read_csv(self.liftoffGFF, delimiter='\t', skip_blank_lines=True, names=self.headerList, skiprows=count_rows_starting_with_comment(self.liftoffGFF))
        
        #run function to find and drop fields in attributes
        lo_gff['attributes']=lo_gff['attributes'].apply(lambda row : self.fix_attributes(fields_to_drop, row))
        # run codon check on new formated gff dataframe
        self.codon_check(lo_gff)
        return lo_gff
    
    def fix_attributes(self, fields_to_drop, attr):
        """ To fit GenBank submission standards some fields that liftoff adds to the attributes must be removed.
        """
        attr_list=attr.split(';')
        for l in fields_to_drop:
            for i, s in enumerate(attr_list):
                if l in s:
                    attr_list.pop(i)
        return (';'.join(attr_list))
    
    def codon_check(self, lo_gff):
        """ To fit GenBank submission standards if the attributes hold a bad_codon_field the the CDS has to changed to 'misc_feature'
        """ 
        codon_errors = []
        bad_codon_fields = ['missing_start_codon', 'missing_stop_codon', 'inframe_stop_codon']
        
        
        #gather which codons are found in gff
        codon=[c for c in bad_codon_fields for att in lo_gff['attributes'] if c in att]
        #gather a list of indexs that have bad_codon_fields in attributes
        bad_codon_index=[lo_gff.index[lo_gff['attributes'].str.contains(bc, regex=True)].tolist() for bc in bad_codon_fields]
        bad_codon_index = [val for sublist in bad_codon_index for val in sublist]
        
        #add errors
        for i in range(len(codon)):
            codon_errors.append(f"Field for stop codon found in {self.samp_name}.liftoff-orig.gff: {codon[i]} in line " + \
                                f"{bad_codon_index[i]} at coordinates {lo_gff['start'].loc[bad_codon_index[i]]}, {lo_gff['end'].loc[bad_codon_index[i]]}")
            
        #loop through bad_codon_indexs and change mention of 'cds' to 'misc_feature'. Finally remove 'product' from attributes.
        for c_i in bad_codon_index:
            cds_index=int(lo_gff[(lo_gff['start'] == lo_gff.loc[c_i, 'start']) & (lo_gff['end'] == lo_gff.loc[c_i, 'end']) & (lo_gff['type'] == 'CDS')].index.values)
            lo_gff.at[cds_index,'type']='misc_feature'
            lo_gff.loc[cds_index,'attributes']=lo_gff.loc[cds_index,'attributes'].replace('cds', 'misc_feature')
            lo_gff.loc[cds_index,'attributes']=self.fix_attributes(['product='], lo_gff.loc[cds_index,'attributes']) 
        
        #write errors to annotation_error file    
        with open(f"{self.outdir}/{self.samp_name}_annotation_error.txt", 'a') as out:
            # write the stop codon check
            out.write(f"\n\tSTOP CODON CHECK:\n")
            if len(codon_errors) !=0:
                for codon_error in codon_errors:
                    out.write(f"\t{codon_error}\n")
            else:
                out.write(f"\tNo codon errors\n")
        return lo_gff

class concat_gffs:
    def __init__(self, liftoffGFF, rem_gff, lo_gff, ref_id, samp_name, outdir):
        self.liftoffGFF = liftoffGFF
        self.rem_gff = rem_gff
        self.lo_gff = lo_gff
        self.ref_id=ref_id
        self.samp_name=samp_name
        self.outdir=outdir
        
    def lo_gff_headliners(self):
        #grab the first three line (headliners) in liftoff gff, this will be added as first three lines in new concat gff
        gff_info=[]
        with open(self.liftoffGFF, 'r') as f:
            for row in f:
                if row.startswith('#'):                   
                    gff_info.append(row)
        return gff_info
    
    def concat_LO_RM(self):       
        gff_info=self.lo_gff_headliners()
        rep = {self.ref_id : self.samp_name, "_###_" : "_"}
        #concat horizontally the repeatmasker and liftoff gff
        horizontal_concat = pd.concat([self.rem_gff, self.lo_gff], axis=0)
        #sort concatenated gff by start position of features
        horizontal_concat = horizontal_concat.sort_values(['start'], ignore_index=True)
        #use rep dic to replace unwanted values
        for k in rep:
            horizontal_concat['attributes'] = horizontal_concat['attributes'].apply(lambda a: str(a).replace(k,rep[k]))
        ### final step output new concat gff as file starting off with the headliners from the original liftoff gff
        with open(f'{self.outdir}/{self.samp_name}_reformatted.gff', 'w') as fp:
            for x in gff_info:
                fp.write(x)
            horizontal_concat.to_csv(fp, sep='\t', index=False, header=False)
        fp.close()

if __name__ == "__main__":
    annotation_main()
