#!/usr/bin/env python3

import os
import sys
import logging
import shutil
import re
from submission_helper import setup_logging

# Constants
MAX_FILE_SIZE = 2 * 1024 ** 3  # 2 GB
MAX_SEQUENCES = 20000
WARN_SEQUENCES = 10000
MIN_SEQ_LENGTH = 200
WARN_SEQ_LENGTH = 1000

HEADER_PATTERN = re.compile(r'^>[\w\-.]+(?:\s+\[.+\])?')
PLASMID_NAME_PATTERN = re.compile(r'^p[\w\d\-_]{0,19}$')
PLASMID_UNNAMED_PATTERN = re.compile(r'^unnamed\d*$')  
CHROMOSOME_NAME_PATTERN = re.compile(r'^[\w\.\-_]{1,33}$')

used_headers = set()

def check_file_exists(path):
    if not os.path.isfile(path):
        logging.error(f"File not found: {path}")
        sys.exit(1)

def check_file_size(path):
    size = os.path.getsize(path)
    if size > MAX_FILE_SIZE:
        logging.error(f"File size error: '{path}' is {size / (1024**3):.2f} GB, which exceeds the 2 GB limit.")
        sys.exit(1)

def read_fasta(path):
    """Yield (header, sequence) tuples from FASTA file"""
    with open(path, 'r') as f:
        header = None
        seq_lines = []
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            if line.startswith(">"):
                if header:
                    yield header, ''.join(seq_lines)
                header = line
                seq_lines = []
            else:
                if not header:
                    logging.error(f"FASTA format error: Sequence found before header at line {line_num}")
                    sys.exit(1)
                seq_lines.append(line)
        if header:
            yield header, ''.join(seq_lines)

def clean_sequence(seq):
    return seq.lstrip("Nn").rstrip("Nn")

def validate_header_format(header):
    if not HEADER_PATTERN.match(header):
        logging.error(f"Invalid FASTA header format: {header}")
        sys.exit(1)

def check_unique_header(header):
    if header in used_headers:
        logging.error(f"Duplicate header found: {header}")
        sys.exit(1)
    used_headers.add(header)


def check_naming_conventions(header):
    """
    Check naming rules for chromosome and plasmid names based on GenBank rules.
    """
    plasmid_match = re.search(r'\[plasmid-name=(.*?)\]', header)
    chrom_match = re.search(r'\[chromosome=(.*?)\]', header)
    organelle_match = re.search(r'\[organelle=(.*?)\]', header)

    if plasmid_match:
        name = plasmid_match.group(1)
        if 'plasmid' in name.lower():
            logging.error(f"Invalid plasmid name '{name}' contains the word 'plasmid': {header}")
            sys.exit(1)
        if not (name == 'unnamed' or PLASMID_UNNAMED_PATTERN.match(name) or PLASMID_NAME_PATTERN.match(name)):
            logging.error(f"Invalid plasmid name '{name}' in header: {header}")
            sys.exit(1)

    if chrom_match:
        name = chrom_match.group(1)
        if 'chr' in name.lower() or 'chromosome' in name.lower() or 'unknown' in name.lower() or name.lower() in ['un', 'unk', '0']:
            logging.error(f"Invalid chromosome name '{name}' in header: {header}")
            sys.exit(1)
        if not CHROMOSOME_NAME_PATTERN.match(name):
            logging.error(f"Chromosome name '{name}' does not meet naming rules: {header}")
            sys.exit(1)
        if 'linkage' in header.lower() and 'lg' not in name.lower():
            logging.warning(f"Chromosome '{name}' may represent a linkage group but does not contain 'LG': {header}")


def check_sequence_length(seq, header):
    cleaned_len = len(seq)
    if cleaned_len < MIN_SEQ_LENGTH:
        logging.error(
            f"Sequence length error: {header} is only {cleaned_len} nt after trimming, "
            f"which is below the required minimum of {MIN_SEQ_LENGTH} nt."
        )
        sys.exit(1)
    if cleaned_len < WARN_SEQ_LENGTH:
        logging.warning(
            f"Warning: Sequence '{header}' is {cleaned_len} nt after trimming. Lengths between 200 and 1000 nt may indicate the presence of contaminants."        )

def validate_and_clean_fasta(input_path, output_path):
    check_file_size(input_path)

    seq_count = 0
    with open(output_path, 'w') as out_f:
        for header, raw_seq in read_fasta(input_path):
            seq_count += 1

            # Header checks
            validate_header_format(header)
            check_unique_header(header)
            check_naming_conventions(header)

            # Sequence cleaning and validation
            cleaned_seq = clean_sequence(raw_seq)
            check_sequence_length(cleaned_seq, header)

            # Write cleaned sequence
            out_f.write(f"{header}\n")
            for i in range(0, len(cleaned_seq), 60):
                out_f.write(f"{cleaned_seq[i:i+60]}\n")

    # Check number of sequences
    if seq_count > MAX_SEQUENCES:
        logging.error(f"Sequence count error: {seq_count} sequences found, which exceeds the limit of {MAX_SEQUENCES}.")
        sys.exit(1)
    elif seq_count > WARN_SEQUENCES:
        logging.warning(f"Sequence count warning: {seq_count} sequences found, which exceeds the recommended threshold of {WARN_SEQUENCES}.")

    logging.info(f"Successfully validated and cleaned {seq_count} sequences.")
    logging.info(f"Cleaned FASTA written to: {output_path}")
    logging.info("Note: For bacterial genomes, include gcode via table2asn if needed.")

if __name__ == "__main__":
    setup_logging(log_file='validate_genbank.log', level=logging.DEBUG)

    if len(sys.argv) != 2:
        logging.error("Usage: validate_and_clean_fasta.py <input.fasta>")
        sys.exit(1)

    input_fasta = sys.argv[1]

    check_file_exists(input_fasta)

    # Derive cleaned output with .fsa extension
    base_fasta = os.path.splitext(os.path.basename(input_fasta))[0]
    output_fasta = os.path.join(os.path.dirname(input_fasta), f"{base_fasta}_cleaned.fsa")


    validate_and_clean_fasta(input_fasta, output_fasta)
