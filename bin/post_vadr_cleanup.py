#!/usr/bin/env python3

import argparse
import os
from pathlib import Path

# import utility functions
from annotation_utility import MainUtility as main_util
from annotation_utility import MainVADRFuncs

def parse_args():
    parser = argparse.ArgumentParser(description="Post-process VADR outputs")
    parser.add_argument('--vadr_outputs', type=Path, required=True,
                        help='Path to VADR outputs directory (contains *.vadr.pass.tbl and *.vadr.fail.tbl)')
    parser.add_argument('--sample_id', type=str, required=True,
                        help='Sample ID (used to name output files)')
    parser.add_argument('--vadr_outdir', type=Path, default=Path('vadr_outputs'),
                        help='Top-level directory for VADR outputs')
    return parser.parse_args()

def main():
    args = parse_args()

    # Define directory layout
    transformed_outdir = args.vadr_outdir / args.sample_id

    # Create necessary directories
    transformed_outdir.mkdir(parents=True, exist_ok=True)
    for sub in ['gffs', 'tbl', 'errors']:
        (transformed_outdir / sub).mkdir(exist_ok=True)

    # Expect original_outdir to be populated externally (e.g., by Nextflow)
    parameters = {
        'vadr_outputs': str(args.vadr_outputs),
        'output_path': str(transformed_outdir),
        'sample_id': args.sample_id
    }

    # Run main logic
    processor = MainVADRFuncs(parameters)
    processor.split_table()
    processor.line_cleanup()

    # Convert each GFF to a .tbl file
    for sample in processor.sample_info:
        gff_file = transformed_outdir / 'gffs' / f'{sample}_reformatted.gff'
        tbl_outdir = transformed_outdir / 'tbl'
        main_util.gff2tbl(sample, str(gff_file), str(tbl_outdir))


if __name__ == "__main__":
    main()
