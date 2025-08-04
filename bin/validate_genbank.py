#!/usr/bin/env python3

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

MAX_FILE_SIZE = 2 * 1024 ** 3  # 2 GB
MAX_SEQUENCES = 20000
WARN_SEQUENCES = 10000
MIN_SEQ_LENGTH = 200
WARN_SEQ_LENGTH = 1000

def check_file_size(path):
    size = os.path.getsize(path)
    if size > MAX_FILE_SIZE:
        logging.error(
            f"File size error: '{path}' is {size / (1024**3):.2f} GB, which exceeds the 2 GB limit."
        )
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

def validate_and_clean_fasta(input_path, output_path):
    check_file_size(input_path)

    seq_count = 0
    with open(output_path, 'w') as out_f:
        for header, seq in read_fasta(input_path):
            seq_count += 1
            cleaned_seq = clean_sequence(seq)
            cleaned_len = len(cleaned_seq)

            if cleaned_len < MIN_SEQ_LENGTH:
                logging.error(
                    f"Sequence length error: {header} is only {cleaned_len} nt after trimming, "
                    f"which is below the required minimum of {MIN_SEQ_LENGTH} nt."
                )
                sys.exit(1)

            if cleaned_len < WARN_SEQ_LENGTH:
                logging.warning(
                    f"Sequence warning: {header} is {cleaned_len} nt after trimming, which is short (<{WARN_SEQ_LENGTH} nt)."
                )

            out_f.write(f"{header}\n")
            for i in range(0, cleaned_len, 60):
                out_f.write(f"{cleaned_seq[i:i+60]}\n")

    if seq_count > MAX_SEQUENCES:
        logging.error(
            f"Sequence count error: {seq_count} sequences found, which exceeds the limit of {MAX_SEQUENCES}."
        )
        sys.exit(1)
    elif seq_count > WARN_SEQUENCES:
        logging.warning(
            f"Sequence count warning: {seq_count} sequences found, which exceeds the recommended threshold of {WARN_SEQUENCES}."
        )

    logging.info(f"Successfully validated and cleaned {seq_count} sequences.")
    logging.info(f"Cleaned FASTA written to: {output_path}")

def validate_gff(input_path, output_path):
    """Copy the GFF file to a new validated GFF file without processing."""
    check_file_size(input_path)
    os.rename(input_path, output_path)
    logging.info(f"Validated GFF written to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        logging.error("Usage: validate_and_clean_fasta.py <input.fasta> <input.gff>")
        sys.exit(1)

    input_fasta = sys.argv[1]
    input_gff = sys.argv[2]

    if not os.path.isfile(input_fasta):
        logging.error(f"FASTA file not found: {input_fasta}")
        sys.exit(1)

    if not os.path.isfile(input_gff):
        logging.error(f"GFF file not found: {input_gff}")
        sys.exit(1)

    base_fasta, ext_fasta = os.path.splitext(input_fasta)
    output_fasta = f"{base_fasta}_cleaned{ext_fasta}"

    base_gff, ext_gff = os.path.splitext(input_gff)
    output_gff = f"{base_gff}_validated{ext_gff}"

    validate_and_clean_fasta(input_fasta, output_fasta)
    validate_gff