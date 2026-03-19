#!/usr/bin/env bash
# Copies FASTAs into a clean working directory with corrected strain names.
# Ignored states go to a separate subdirectory. Source files are never modified.
set -euo pipefail

# -- Config --
export METADATA="/scicomp/groups-pure/OID/NCIRD/DVD/VVPDB/Projects/CLINICAL_PROJECTS/GenBank_submissions/WGS_consensus_GenBank_metadata.tsv"
export MYFILES="/scicomp/groups-pure/OID/NCIRD/DVD/VVPDB/Projects/CLINICAL_PROJECTS/GenBank_submissions/submissions/testrun/DSId_fasta/myfiles"
export BROAD="/scicomp/groups-pure/OID/NCIRD/DVD/VVPDB/Projects/CLINICAL_PROJECTS/BROAD_MEASEQ_FASTA/reheaded_renamed_non_duplicates_complete_90"
export MISSING_BROAD="/scicomp/groups-pure/OID/NCIRD/DVD/VVPDB/Projects/CLINICAL_PROJECTS/BROAD_MEASEQ_FASTA/MISSING_BROAD_SAMPLES/reheaded_renamed_non_duplicates_complete_90"
export OUTDIR="$HOME/measles_submission"
export IGNORE_STATES="Utah|Arizona|South Carolina|Texas"

export FASTA_OUT="$OUTDIR/fasta"
export IGNORED_OUT="$OUTDIR/ignored/fasta"
mkdir -p "$FASTA_OUT" "$IGNORED_OUT"

python3 << 'PYEOF'
import csv, re, os, shutil

metadata = os.environ["METADATA"]
myfiles = os.environ["MYFILES"]
broad = os.environ["BROAD"]
missing_broad = os.environ.get("MISSING_BROAD", "")
fasta_out = os.environ["FASTA_OUT"]
ignored_out = os.environ["IGNORED_OUT"]
outdir = os.environ["OUTDIR"]
ignore_states = {s.strip().lower() for s in os.environ["IGNORE_STATES"].split("|")}

# Index all FASTAs across source dirs (including subdirs of BROAD)
search_dirs = [myfiles, broad]
if missing_broad and os.path.isdir(missing_broad):
    search_dirs.append(missing_broad)
for d in search_dirs[:]:
    if os.path.isdir(d):
        for sub in os.listdir(d):
            subpath = os.path.join(d, sub)
            if os.path.isdir(subpath):
                search_dirs.append(subpath)

fasta_index = {}
for d in search_dirs:
    if not os.path.isdir(d):
        continue
    for f in os.listdir(d):
        if f.endswith(('.fasta', '.fa', '.fna', '.fas')) and f not in fasta_index:
            fasta_index[f] = os.path.join(d, f)

print(f"Indexed {len(fasta_index)} FASTAs across {len(search_dirs)} directories")

# Process each sample
copied = renamed = ignored_copied = ignored_renamed = 0
not_found = []
out_rows = []
ignored_rows = []

with open(metadata) as f:
    reader = csv.DictReader(f, delimiter="\t")
    fieldnames = reader.fieldnames
    for row in reader:
        seqid = row["SeqID"]
        state = row["Country"].split(":")[-1].strip() if ":" in row["Country"] else ""
        is_ignored = state.lower() in ignore_states

        old_fname = seqid + ".fasta"
        if re.search(r"_(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.", seqid):
            new_fname = old_fname
        else:
            iso_num = row["Isolate"].split("-")[-1] if "-" in row["Isolate"] else ""
            new_fname = f"MVs_{state}.USA_{row['Collection_date']}_{iso_num}.fasta"

        source = fasta_index.get(old_fname) or fasta_index.get(new_fname)
        if not source:
            not_found.append((seqid, state, "IGNORE" if is_ignored else "ACTIVE"))
            continue

        dest_dir = ignored_out if is_ignored else fasta_out
        dest = os.path.join(dest_dir, new_fname)
        if not os.path.exists(dest):
            shutil.copy2(source, dest)

        was_renamed = old_fname != new_fname
        new_seqid = new_fname.replace(".fasta", "")
        row["SeqID"] = new_seqid

        # Fix DSDId typo in note field
        if "note" in row:
            row["note"] = row["note"].replace("DSDId", "DSId")

        # Add BioSample fields
        row["isolation_source"] = "clinical"
        row["collected_by"] = "not provided"
        row["lat_lon"] = "not collected"
        row["host_disease"] = "measles"
        row["ncbi-bioproject"] = "PRJNA1137905"
        # SPUID: replace dots/slashes with underscores for XML safety
        spuid = re.sub(r'[./]', '_', new_seqid)
        row["ncbi-spuid"] = spuid
        row["ncbi-spuid-sra"] = spuid + "_SRA"

        if is_ignored:
            ignored_copied += 1
            ignored_renamed += was_renamed
            ignored_rows.append(row)
        else:
            copied += 1
            renamed += was_renamed
            out_rows.append(row)

# Add new columns to fieldnames
extra_cols = ["isolation_source", "collected_by", "lat_lon", "host_disease",
              "ncbi-bioproject", "ncbi-spuid", "ncbi-spuid-sra"]
fieldnames = list(fieldnames) + [c for c in extra_cols if c not in fieldnames]

# Write metadata
meta_out = os.path.join(outdir, "corrected_metadata.tsv")
with open(meta_out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
    w.writeheader()
    w.writerows(out_rows)

ignored_meta_out = os.path.join(outdir, "ignored", "ignored_metadata.tsv")
with open(ignored_meta_out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
    w.writeheader()
    w.writerows(ignored_rows)

# Summary
active_missing = [x for x in not_found if x[2] == "ACTIVE"]
print(f"\nActive:  {copied} samples ({renamed} renamed) -> {fasta_out}")
print(f"Ignored: {ignored_copied} samples ({ignored_renamed} renamed) -> {ignored_out}")
print(f"Missing: {len(not_found)} ({len(active_missing)} active)")

if active_missing:
    print("\nActive samples with no FASTA found:")
    for seqid, state, _ in active_missing:
        print(f"  {seqid} ({state})")

states = {}
for row in out_rows:
    s = row["Country"].split(":")[-1].strip() if ":" in row["Country"] else "?"
    states[s] = states.get(s, 0) + 1
print("\nBy state:")
for s, c in sorted(states.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")

# Split FASTAs into by_state directories
by_state_dir = os.path.join(outdir, "by_state")
for row in out_rows:
    state = row["Country"].split(":")[-1].strip() if ":" in row["Country"] else "unknown"
    state_dir = os.path.join(by_state_dir, state)
    os.makedirs(state_dir, exist_ok=True)
    fname = row["SeqID"] + ".fasta"
    src = os.path.join(fasta_out, fname)
    dst = os.path.join(state_dir, fname)
    if os.path.isfile(src) and not os.path.exists(dst):
        shutil.copy2(src, dst)

state_list = sorted(states.keys())
print(f"\nBy-state FASTAs: {by_state_dir}/")
print(f"  States: {', '.join(state_list)}")

print(f"\nTo run a state through TOSTADAS (e.g. Colorado):")
print(f"  nextflow run main.nf \\")
print(f"    -profile measles,test,singularity \\")
print(f"    --workflow genbank --genbank_only \\")
print(f"    --meta_path {meta_out} \\")
print(f"    --updated_meta_path {meta_out} \\")
print(f"    --fasta_dir {by_state_dir}/Colorado \\")
print(f"    --submission_config conf/submission_config.yaml \\")
print(f"    --outdir {outdir}/results/Colorado")
PYEOF
