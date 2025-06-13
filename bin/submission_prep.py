#!/usr/bin/env python3
import os
import sys
import pandas as pd
from submission_helper import (
	GetParams,
	SubmissionConfigParser,
	Sample,
	BiosampleSubmission,
	SRASubmission,
	GenbankSubmission
)

def main_prepare():
	# parse exactly the same CLI args you already have
	params = GetParams().parameters

	# load config & metadata
	config = SubmissionConfigParser(params).load_config()
	batch_id = os.path.splitext(os.path.basename(params['metadata_file']))[0]
	metadata_df = pd.read_csv(params['metadata_file'], sep='\t')
	identifier = params['identifier']
	submission_dir = 'Test' if params['test'] else 'Production'
	output_root = params['output_dir']
	# build sample objects
	samples = []
	for s in params['sample']:
		d = dict(item.split('=') for item in s.split(','))
		samples.append(Sample(
			sample_id   = d['sample_id'],
			batch_id    = batch_id,
			fastq1      = d.get('fq1'),
			fastq2      = d.get('fq2'),
			nanopore    = d.get('nanopore'),
			species     = params['species'],
			databases   = [db for db in params if params[db] and db in ['biosample','sra','genbank']],
			fasta_file  = d.get('fasta'),
			annotation_file = d.get('gff')
		))

	# 1) Prepare BioSample XML + submit.ready
	if params['biosample']:
		bs_out = os.path.join(output_root, 'biosample')
		bs = BiosampleSubmission(
			parameters=params,
			submission_config=config,
			metadata_df=metadata_df,
			output_dir=bs_out,
			submission_mode=params['submission_mode'],
			submission_dir=submission_dir,
			type='biosample',
			sample=None,
			accession_id=None,
			identifier=identifier
		)
		bs.init_xml_root()
		for s in samples:
			md = metadata_df[metadata_df['sample_name']==s.sample_id]
			bs.add_sample(s, md)
		bs.finalize_xml()
		# write submit.ready
		open(os.path.join(bs_out,'submit.ready'),'w').close()

	# 2) Prepare SRA XML + submit.ready (per-platform if needed)
	if params['sra']:
		illum = [s for s in samples if s.fastq1 and s.fastq2]
		nano  = [s for s in samples if s.nanopore]
		platforms = (('illumina',illum),('nanopore',nano)) if illum and nano else [(None, illum or nano)]
		for platform, samp_list in platforms:
			outdir = os.path.join(output_root,'sra',platform) if platform else os.path.join(output_root,'sra')
			sra = SRASubmission(
				parameters=params,
				submission_config=config,
				metadata_df=metadata_df,
				output_dir=outdir,
				submission_mode=params['submission_mode'],
				submission_dir=submission_dir,
				type='sra',
				samples=samp_list,
				sample=None,
				accession_id=None,
				identifier=identifier
			)
			sra.init_xml_root()
			for s in samp_list:
				md = metadata_df[metadata_df['sample_name']==s.sample_id]
				sra.add_sample(s, md, platform)
			sra.finalize_xml()
			open(os.path.join(outdir,'submit.ready'),'w').close()

	# 3) Prepare GenBank (if FTP) or manual
	if params['genbank']:
		gb = GenbankSubmission(
			parameters=params,
			submission_config=config,
			metadata_df=metadata_df,
			output_dir=os.path.join(output_root,'genbank',params['submission_name']),
			submission_mode=params['submission_mode'],
			submission_dir=submission_dir,
			type='genbank',
			sample=samples[0],               # class expects one sample
			accession_id=None,
			identifier=identifier
		)
		if samples[0].ftp_upload:
			gb.prepare_files_ftp_submission()
		else:
			gb.prepare_files_manual_submission()
			if params['send_email']:
				gb.sendemail()

if __name__=="__main__":
	main_prepare()
