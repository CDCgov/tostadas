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
errors = []

def check_file_exists(path):
    if not os.path.isfile(path):
        msg = f"File not found: {path}"
        logging.error(msg)
        errors.append(msg)

def check_file_size(path):
    size = os.path.getsize(path)
    if size > MAX_FILE_SIZE:
        msg = f"File size error: '{path}' is {size / (1024**3):.2f} GB, which exceeds the 2 GB limit."
        logging.error(msg)
        errors.append(msg)

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
                    msg = f"FASTA format error: Sequence found before header at line {line_num}"
                    logging.error(msg)
                    errors.append(msg)
                    continue
                seq_lines.append(line)
        if header:
            yield header, ''.join(seq_lines)

def clean_sequence(seq):
    return seq.lstrip("Nn").rstrip("Nn")

def validate_header_format(header):
    if not HEADER_PATTERN.match(header):
        msg = f"Invalid FASTA header format: {header}"
        logging.error(msg)
        errors.append(msg)

def check_unique_header(header):
    if header in used_headers:
        msg = f"Duplicate header found: {header}"
        logging.error(msg)
        errors.append(msg)
    used_headers.add(header)

def check_naming_conventions(header):
    # Extract plasmid/chromosome names from natural text headers
    plasmid_match = re.search(r'\bplasmid\b[:\s]*([^\],]+)', header, re.IGNORECASE)
    chrom_match = re.search(r'\bchromosome\b[:\s]*([^\],]+)', header, re.IGNORECASE)

    if plasmid_match:
        name = plasmid_match.group(1).strip()
        if 'plasmid' in name.lower():
            msg = f"Invalid plasmid name '{name}' contains the word 'plasmid': {header}"
            logging.error(msg)
            errors.append(msg)
        elif not (
            name == 'unnamed'
            or PLASMID_UNNAMED_PATTERN.match(name)
            or PLASMID_NAME_PATTERN.match(name)
        ):
            msg = f"Invalid plasmid name '{name}' in header: {header}"
            logging.error(msg)
            errors.append(msg)

    if chrom_match:
        name = chrom_match.group(1).strip()
        if any(sub in name.lower() for sub in ['chr', 'chromosome', 'unknown']) or name.lower() in ['un', 'unk', '0']:
            msg = f"Invalid chromosome name '{name}' in header: {header}"
            logging.error(msg)
            errors.append(msg)
        elif not CHROMOSOME_NAME_PATTERN.match(name.replace(" ", "")):  # allow spaces in LG names
            msg = f"Chromosome name '{name}' does not meet naming rules: {header}"
            logging.error(msg)
            errors.append(msg)
        elif re.search(r'\blg\b', name.lower()):
            logging.info(f"Chromosome '{name}' appears to represent a linkage group (LG): {header}")

def check_sequence_length(seq, header):
    cleaned_len = len(seq)
    if cleaned_len < MIN_SEQ_LENGTH:
        msg = (
            f"Sequence length error: {header} is only {cleaned_len} nt after trimming, "
            f"which is below the required minimum of {MIN_SEQ_LENGTH} nt."
        )
        logging.error(msg)
        errors.append(msg)
    elif cleaned_len < WARN_SEQ_LENGTH:
        logging.warning(
            f"Warning: Sequence '{header}' is {cleaned_len} nt after trimming. "
            "Lengths between 200 and 1000 nt may indicate the presence of contaminants."
        )

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
        msg = f"Sequence count error: {seq_count} sequences found, which exceeds the limit of {MAX_SEQUENCES}."
        logging.error(msg)
        errors.append(msg)
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

    base_fasta = os.path.splitext(os.path.basename(input_fasta))[0]
    outdir = os.path.join(os.path.dirname(input_fasta), "genbank")
    os.makedirs(outdir, exist_ok=True)
    output_fasta = os.path.join(outdir, f"{base_fasta}_cleaned.fsa")

    validate_and_clean_fasta(input_fasta, output_fasta)

    if errors:
        logging.error("\nValidation completed with errors:")
        for e in errors:
            logging.error(f" - {e}")
        sys.exit(1)
