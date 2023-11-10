#!/usr/bin/env python3

## Written by Swarnali Louha
## Post bakta transformation of gff and fasta files,generation of tbl file
## Date: 11/01/2023

import argparse
import os
import re
import pandas as pd

def bakta_main():
	args = get_args().parse_args()
	parameters = vars(args)

	meta_filename = parameters['meta_path'].split('/')[-1].split('.')[0]
	parameters['output_path'] = f"{parameters['bakta_outdir']}/{meta_filename}"

	for dir_name in ['fasta', 'gff', 'tbl']:
        	os.system(f"mkdir -m777 -p {parameters['output_path']}/{dir_name}")

	bakta_funcs = BAKTAFuncs(parameters)

def get_args():
	""" Function to get the user defined parameters for bakta post cleanup
	"""
	parser = argparse.ArgumentParser(description="Parameters for BAKTA post processing")
	parser.add_argument("--bakta_outdir", type=str, default='bakta_outputs', help="Name of final bakta output directory")
	parser.add_argument("--bakta_results", type=str, help="Path to the raw bakta outputs")
	parser.add_argument("--fasta_path", type=str, help="Path to the input fasta file")
	parser.add_argument("--meta_path", type=str, help="Path to the input metadata file")
	return parser

class BAKTAFuncs:
	def __init__(self, parameters):
		self.parameters = parameters
		fasta_header = self.output_fasta()

		self.gff_transform(fasta_header)

	def output_fasta(self):
		"""
		Outputs fasta file with filename as fasta header 
		"""
		with open(self.parameters['fasta_path']) as f:
			fasta_lines = [line.strip() for line in f.readlines()]
			f.close()
			if fasta_lines[0].startswith(">"):
				fasta_header = fasta_lines[0].split(" ")[0].split(">")[-1]

			fasta_outfile = open(f"{self.parameters['output_path']}/fasta/{fasta_header}.fasta", "w")

			for line in fasta_lines:
				if line.startswith(">"):
					fasta_outfile.write(f">{fasta_header}\n")
				else:
					fasta_outfile.write(line)
			fasta_outfile.close()
		return fasta_header

	def gff_transform(self, fasta_header):
		""" Tranforms gff file and creates tbl file
		"""
		gff_filename = self.parameters['bakta_results'].split('/')[-1]
		gff_HeaderLines = []
		temp_gff = open(f"{self.parameters['output_path']}/gff/temp_{gff_filename}.gff3", "w")
		with open(f"{self.parameters['bakta_results']}/{gff_filename}.gff3") as input_gff:
			gff_lines = [line.strip() for line in input_gff.readlines()]
			input_gff.close()
			for line in gff_lines:
				if line.startswith("#"):
					gff_HeaderLines.append(line)
				match_obj = re.search("^(#|>|[AaTtGgCcNn-]{1,60}$)", line)
				if not match_obj:
					temp_gff.write(line + '\n')
			temp_gff.close()

		gff_HeaderList = ['seqid', 'source', 'type', 'start', 'end', 'score', 'strand', 'phase', 'attributes']
		df = pd.read_csv(f"{self.parameters['output_path']}/gff/temp_{gff_filename}.gff3", delimiter='\t', names=gff_HeaderList)
		df = df[df.type != 'region']
		df['seqid'] = fasta_header
		bakta_locus_tag = df.iloc[0].tolist()[-1].split(';')[0].split('=')[1].split('_')[0]
		df['attributes'] = df['attributes'].str.replace(bakta_locus_tag, fasta_header)
		for index, row in df.iterrows():
			list = row['attributes'].split(';')
			ID = list[0].split('=')
			new_ID = str(row['type'].lower() + '-' + ID[1])
			df['attributes'] = df['attributes'].str.replace(ID[1], new_ID, regex=True)

		with open(f"{self.parameters['output_path']}/gff/{fasta_header}_reformatted.gff", 'a') as final_gff:
			for line in gff_HeaderLines:
				final_gff.write(line+'\n')
			df.to_csv(final_gff, header=False, index=False, sep='\t' )
			final_gff.close()
		os.system(f"rm {self.parameters['output_path']}/gff/temp_{gff_filename}.gff3")


		with open(f"{self.parameters['output_path']}/tbl/{fasta_header}.tbl", "w") as tbl:
			tbl.write('>' + 'Feature' + ' ' + fasta_header + '\n')
			for index, row in df.iterrows():
				list = row['attributes'].split(';')
				x = dict([pair.split("=") for pair in list])
				key1 = 'ID'
				key2 = 'product'
				key3 = 'gene'
				key4 = 'Dbxref'
				key5 = 'anti_codon'
				key6 = 'amino_acid'
				tbl.write(str(row['end']) + '\t' + str(row['start']) + '\t' + str(row['type']) + '\n')
				tbl.write('\t' + '\t' + '\t' + key1 + '\t' + x[key1] + '\n')
				if 'gene' in x:
					tbl.write('\t' + '\t' + '\t' + key3 + '\t' + x[key3] + '\n')
				tbl.write('\t' + '\t' + '\t' + key2 + '\t' + x[key2] + '\n')
				if 'Dbxref' in x:
					tbl.write('\t' + '\t' + '\t' + key4 + '\t' + x[key4] + '\n')
				if 'anti_codon' in x:
					tbl.write('\t' + '\t' + '\t' + key5 + '\t' + x[key5] + '\n')
				if 'amino_acid' in x:
					tbl.write('\t' + '\t' + '\t' + key6 + '\t' + x[key6] + '\n')
			tbl.close()


if __name__ == "__main__":
	bakta_main()
