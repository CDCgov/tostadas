#!/usr/bin/env bash
set -euo pipefail

export METADATA="/scicomp/groups-pure/OID/NCIRD/DVD/VVPDB/Projects/CLINICAL_PROJECTS/GenBank_submissions/WGS_consensus_GenBank_metadata.tsv"
export CONSENSUS_1="/scicomp/groups-pure/OID/NCIRD/DVD/VVPDB/Projects/CLINICAL_PROJECTS/BROAD_MEASEQ_FASTA/reheaded_renamed_non_duplicates_complete_90_withAVI"
export CONSENSUS_2="/scicomp/groups-pure/OID/NCIRD/DVD/VVPDB/Projects/CLINICAL_PROJECTS/BROAD_MEASEQ_FASTA/MISSING_BROAD_SAMPLES/reheaded_renamed_non_duplicates_complete_90"
export OUTDIR="$HOME/measles_submission"

mkdir -p "$OUTDIR"

python3 << 'PYEOF'
import csv, re, os, shutil

metadata = os.environ["METADATA"]
consensus_dirs = [os.environ["CONSENSUS_1"], os.environ["CONSENSUS_2"]]
outdir = os.environ["OUTDIR"]

# Index all consensus FASTAs
fasta_index = {}
for d in consensus_dirs:
    if not os.path.isdir(d):
        continue
    for sub in [d] + [os.path.join(d, s) for s in os.listdir(d) if os.path.isdir(os.path.join(d, s))]:
        for f in os.listdir(sub):
            if f.endswith(('.fasta', '.fa', '.fna')) and f not in fasta_index:
                fasta_index[f] = os.path.join(sub, f)

print(f"Indexed {len(fasta_index)} consensus FASTAs")

copied = 0
renamed = 0
not_found = []
out_rows = []
fieldnames = None

with open(metadata) as f:
    reader = csv.DictReader(f, delimiter="\t")
    fieldnames = reader.fieldnames
    for row in reader:
        seqid = row["SeqID"]
        state = row["Country"].split(":")[-1].strip() if ":" in row["Country"] else ""

        old_fname = seqid + ".fasta"
        if re.search(r"_(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.", seqid):
            new_fname = old_fname
        else:
            iso_num = row["Isolate"].split("-")[-1] if "-" in row["Isolate"] else ""
            new_fname = f"MVs_{state}.USA_{row['Collection_date']}_{iso_num}.fasta"

        source = fasta_index.get(old_fname) or fasta_index.get(new_fname)
        if not source:
            not_found.append((seqid, state))
            continue

        state_dir = os.path.join(outdir, "by_state", state or "unknown")
        os.makedirs(state_dir, exist_ok=True)
        dest = os.path.join(state_dir, new_fname)
        if not os.path.exists(dest):
            shutil.copy2(source, dest)

        if old_fname != new_fname:
            renamed += 1
        copied += 1

        new_seqid = new_fname.replace(".fasta", "")
        row["SeqID"] = new_seqid
        if "note" in row:
            row["note"] = row["note"].replace("DSDId", "DSId")
        row["isolation_source"] = "clinical"
        row["collected_by"] = "not provided"
        row["lat_lon"] = "not collected"
        row["host_disease"] = "measles"
        row["ncbi-bioproject"] = "PRJNA1137905"
        spuid = re.sub(r'[./]', '_', new_seqid)
        row["ncbi-spuid"] = spuid
        row["ncbi-spuid-sra"] = spuid + "_SRA"
        out_rows.append(row)

extra_cols = ["isolation_source", "collected_by", "lat_lon", "host_disease",
              "ncbi-bioproject", "ncbi-spuid", "ncbi-spuid-sra"]
fieldnames = list(fieldnames) + [c for c in extra_cols if c not in fieldnames]

meta_out = os.path.join(outdir, "corrected_metadata.tsv")
with open(meta_out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
    w.writeheader()
    w.writerows(out_rows)

states = {}
for row in out_rows:
    s = row["Country"].split(":")[-1].strip() if ":" in row["Country"] else "unknown"
    states[s] = states.get(s, 0) + 1

print(f"\nProcessed: {copied} samples ({renamed} renamed)")
print(f"Not found: {len(not_found)}")
print(f"\nBy state:")
for s, c in sorted(states.items(), key=lambda x: -x[1]):
    print(f"  {s}: {c}")

if not_found:
    print(f"\nMissing consensus FASTAs:")
    for seqid, state in not_found[:10]:
        print(f"  {seqid} ({state})")
    if len(not_found) > 10:
        print(f"  ... and {len(not_found) - 10} more")

print(f"\nMetadata: {meta_out}")
print(f"FASTAs:   {outdir}/by_state/<State>/")
print(f"\nTo run a state:")
print(f"  nextflow run main.nf \\")
print(f"    -profile measles,test,singularity \\")
print(f"    --workflow genbank --genbank_only \\")
print(f"    --meta_path {meta_out} \\")
print(f"    --updated_meta_path {meta_out} \\")
print(f"    --fasta_dir {outdir}/by_state/Colorado \\")
print(f"    --sbt {outdir}/template.sbt \\")
print(f"    --submission_config conf/submission_config.yaml \\")
print(f"    --outdir {outdir}/results/Colorado")
PYEOF
