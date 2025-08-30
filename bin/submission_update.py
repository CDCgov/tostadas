#!/usr/bin/env python3
import os
import argparse
import datetime
import logging
import xml.etree.ElementTree as ET
import pandas as pd
from submission_helper import (
	SubmissionConfigParser,
	FTPClient,
	SFTPClient,
	setup_logging
)

# Immutable fields: {xpath : corresponding metadata column name}
FORBIDDEN_UPDATE_FIELDS = {
    ".//BioProject/PrimaryId": "bioproject",
    ".//Organism/OrganismName": "organism",
    ".//Attributes/Attribute[@attribute_name='strain']": "strain",
    ".//Attributes/Attribute[@attribute_name='isolate']": "isolate",
    ".//Attributes/Attribute[@attribute_name='serovar']": "serovar",
    ".//Attributes/Attribute[@attribute_name='serotype']": "serotype",
}

def get_args():
	parser = argparse.ArgumentParser(
		description="Update BioSample submissions based on new metadata"
	)
	parser.add_argument("--submission_folder", required=True,
						help="Top-level folder containing original batch_<n>/biosample/submission.xml")
	parser.add_argument("--submission_name", required=True,
						help="Name of the batch to update (e.g., batch_1)")
	parser.add_argument("--identifier", required=True,
						help="Original metadaata file prefix as unique identifier for NCBI FTP site folder name")
	parser.add_argument("--config_file", required=True,
						help="NCBI credentials/config YAML")
	parser.add_argument("--metadata_file", required=True,
						help="TSV file with updated metadata")
	parser.add_argument("--submission_mode", choices=['ftp','sftp'], default='ftp')
	parser.add_argument("-o", "--outdir", type=str, default='submission_outputs',
						help="Output Directory for final Files, default is current directory")
	parser.add_argument("--test", action="store_true",
						help="Use Test mode instead of Production")
	parser.add_argument("--dry_run", action="store_true",
						help="Print actions without uploading files")
	return parser.parse_args()

def find_biosample_by_spuid(root, spuid_value):
    """Find a BioSample element by SPUID (case-insensitive)."""
    for sample_elem in root.findall(".//BioSample"):
        spuid_elem = sample_elem.find("./SampleId/SPUID")
        if spuid_elem is not None and spuid_elem.text and spuid_elem.text.strip().lower() == spuid_value.lower():
            return sample_elem
    return None

def match_samples(root, metadata_df):
    """Return mapping of sample_id -> BioSample element (or None if not found)."""
    matches = {}
    for _, md_row in metadata_df.iterrows():
        sample_id = md_row['ncbi-spuid']
        sample_elem = find_biosample_by_spuid(root, sample_id)
        if sample_elem is None:
            logging.warning(f"No BioSample element found for sample {sample_id}")
        matches[sample_id] = sample_elem
    return matches

def validate_original_submission(matches, metadata_df):
    errors = []
    for _, md_row in metadata_df.iterrows():
        sample_id = md_row['ncbi-spuid']
        sample_elem = matches.get(sample_id)
        if sample_elem is None:
            continue  # already warned in match_samples
        for xpath, col_name in FORBIDDEN_UPDATE_FIELDS.items():
            orig_elem = sample_elem.find(xpath)
            if orig_elem is None:
                continue
            orig_val = orig_elem.text.strip() if orig_elem.text else ""
            if col_name in md_row and pd.notna(md_row[col_name]):
                new_val = str(md_row[col_name])
                if new_val != orig_val:
                    errors.append(
                        f"Immutable field mismatch for sample {sample_id} ({col_name}): "
                        f"original='{orig_val}' vs new='{new_val}'"
                    )
    if errors:
        raise ValueError("\n".join(errors))


def add_primary_id(sample_elem, biosample_accession):
    """Ensure <PrimaryId db="BioSample"> exists immediately after <SPUID>."""
    sample_id_elem = sample_elem.find("SampleId")
    if sample_id_elem is None:
        raise ValueError("No <SampleId> element found")

    existing_primary = sample_id_elem.find("PrimaryId[@db='BioSample']")
    if existing_primary is None:
        spuid_elem = sample_id_elem.find("SPUID")
        primary_elem = ET.Element("PrimaryId", db="BioSample")
        primary_elem.text = biosample_accession

        if spuid_elem is not None:
            spuid_index = list(sample_id_elem).index(spuid_elem)
            sample_id_elem.insert(spuid_index + 1, primary_elem)  # after SPUID
        else:
            sample_id_elem.append(primary_elem)
    else:
        existing_primary.text = biosample_accession

def update_submission_xml(tree, root, matches, metadata_df, updated_xml):
    updated = 0
    for _, md_row in metadata_df.iterrows():
        sample_id = md_row['ncbi-spuid']
        biosample_acc = md_row['biosample_accession']
        sample_elem = matches.get(sample_id)
        if sample_elem is None:
            continue

        updated += 1

        # Add PrimaryId
        add_primary_id(sample_elem, biosample_acc)

        # Update attributes
        attributes_elem = sample_elem.find("Attributes")
        if attributes_elem is None:
            attributes_elem = ET.SubElement(sample_elem, "Attributes")
        existing_attrs = {attr.get("attribute_name"): attr for attr in attributes_elem.findall("Attribute")}
        for col_name, value in md_row.items():
            if pd.isna(value) or col_name in FORBIDDEN_UPDATE_FIELDS.values():
                continue
            if col_name in existing_attrs:
                existing_attrs[col_name].text = str(value)
            else:
                ET.SubElement(attributes_elem, "Attribute", {"attribute_name": col_name}).text = str(value)

    for attribute in FORBIDDEN_UPDATE_FIELDS.values():
        logging.info(f"Skipping {attribute} because it is an immutable field (NCBI doesn't allow it to change).")

    if updated == 0:
        logging.error("No matching BioSample elements found for any sample; exiting without writing.")
        return False
    
    # Write updated XML
    tree.write(updated_xml, encoding="utf-8", xml_declaration=True)
    return True

def main():
    args = get_args()
    os.makedirs(args.outdir, exist_ok=True)

    # Prepare updated folder
    stamp = datetime.datetime.now().strftime("%Y%m%d")
    updated_folder = f"{args.submission_name}_biosample_update_{stamp}" 
    os.makedirs(updated_folder, exist_ok=True)
    updated_xml = os.path.join(updated_folder, "submission.xml")

    parent_dir = os.path.dirname(updated_folder)
    log_file_path = os.path.join(parent_dir, "update_submission.log")
    setup_logging(log_file=log_file_path, level=logging.DEBUG)
    logging.info("Starting BioSample batch update.")

    metadata_df = pd.read_csv(args.metadata_file, sep='\t')
    config = SubmissionConfigParser(vars(args)).load_config()
    client = SFTPClient(config) if args.submission_mode == 'sftp' else FTPClient(config)
    mode = 'Test' if args.test else 'Production'

    # Locate original XML
    batch_path = os.path.join(args.submission_folder, args.submission_name)
    biosample_xml = os.path.join(batch_path, "biosample", "submission.xml")
    
    tree = ET.parse(biosample_xml)
    root = tree.getroot()

    if not os.path.exists(biosample_xml):
        logging.error(f"No submission.xml found at {biosample_xml}")
        return
    matches = match_samples(root, metadata_df)
    
    # Validate before editing
    try:
        validate_original_submission(matches, metadata_df)
    except ValueError as e:
        logging.error(f"Validation failed for batch {args.submission_name}: {e}")
        return

    # Update XML with metadata + PrimaryIds
    success = update_submission_xml(tree, root, matches, metadata_df, updated_xml)
    if not success:
        return
    #update_submission_xml(biosample_xml, metadata_df, updated_xml)

    # Create submit.ready
    open(os.path.join(updated_folder, "submit.ready"), "w").close()
    logging.info(f"Batch submission ready at {updated_folder}")

    # Upload updated folder
    remote_dir = f"submit/{mode}/{updated_folder}"
    if args.dry_run:
        logging.info(f"[DRY-RUN] Would upload {updated_folder} → {remote_dir}")
    else:
        client.connect()
        client.make_dir(remote_dir)
        client.change_dir(remote_dir)
        for file_name in os.listdir(updated_folder):
            local_file = os.path.join(updated_folder, file_name)
            client.upload_file(local_file, file_name)
        client.close()

if __name__ == "__main__":
	main()