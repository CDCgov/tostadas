#!/usr/bin/env python3
import os
import shutil
import sys
import pandas as pd
from submission_helper import (
	GetParams,
	SubmissionConfigParser,
	Sample,
	BiosampleSubmission,
	SRASubmission,
	GenbankSubmission,
	get_compound_extension
)

def prepare_sra_fastqs(samples, outdir, copy=False):
	for sample in samples:
		if sample.fastq1 and sample.fastq2:
			ext1 = get_compound_extension(sample.fastq1)
			ext2 = get_compound_extension(sample.fastq2)
			dest_fq1 = os.path.join(outdir, f"{sample.sample_id}_R1{ext1}")
			dest_fq2 = os.path.join(outdir, f"{sample.sample_id}_R2{ext2}")
			if not os.path.exists(dest_fq1):
				if copy:
					shutil.copy(sample.fastq1, dest_fq1)
				else:
					os.symlink(sample.fastq1, dest_fq1)
			if not os.path.exists(dest_fq2):
				if copy:
					shutil.copy(sample.fastq2, dest_fq2)
				else:
					os.symlink(sample.fastq2, dest_fq2)

def main_prepare():
	# parse exactly the same CLI args you already have
	params = GetParams().parameters

	# load config & metadata
	config = SubmissionConfigParser(params).load_config()
	batch_id = os.path.splitext(os.path.basename(params['metadata_file']))[0]
	metadata_df = pd.read_csv(params['metadata_file'], sep='\t')
	identifier = params['identifier']
	submission_dir = 'Test' if params['test'] else 'Production'
	output_root = params['outdir']
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
		submission_dir = os.path.join(output_root, 'biosample')
		os.makedirs(submission_dir, exist_ok=True)
		bs = BiosampleSubmission(
			parameters=params,
			submission_config=config,
			metadata_df=metadata_df,
			outdir=submission_dir,
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
		open(os.path.join(submission_dir,'submit.ready'),'w').close()

	# 2) Prepare SRA XML + submit.ready (per-platform if needed)
	if params['sra']:
		illum = [s for s in samples if s.fastq1 and s.fastq2]
		nano  = [s for s in samples if s.nanopore]
		platforms = (('illumina',illum),('nanopore',nano)) if illum and nano else [(None, illum or nano)]
		for platform, samp_list in platforms:
			# submission_dir needs to be unique if submitting both illumina and nanopore
			submission_dir = os.path.join(output_root,'sra',platform) if platform else os.path.join(output_root,'sra')
			os.makedirs(submission_dir, exist_ok=True)
			sra = SRASubmission(
				parameters=params,
				submission_config=config,
				metadata_df=metadata_df,
				outdir=submission_dir,
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
			# write submit.ready
			open(os.path.join(submission_dir,'submit.ready'),'w').close()
			# copy/Symlink raw files to SRA folder
			prepare_sra_fastqs(samp_list, submission_dir, copy=False)

	# 3) Prepare GenBank submission, per-sample
	if params['genbank']:
		for s in samples:
			submission_dir = os.path.join(output_root, 'genbank', s.sample_id)
			os.makedirs(submission_dir, exist_ok=True)
			gb = GenbankSubmission(
				parameters=params,
				submission_config=config,
				metadata_df=metadata_df,
				outdir=submission_dir,
				submission_mode=params['submission_mode'],
				submission_dir=submission_dir,
				type='genbank',
				samples=samples,
				sample=s,               # class expects one sample
				accession_id=None,
				identifier=identifier
			)
			gb.genbank_submission_driver()

if __name__=="__main__":
	main_prepare()
