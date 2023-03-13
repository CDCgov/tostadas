#!/usr/bin/env python3

import pandas as pd
from datetime import datetime, date
import xml.etree.ElementTree as ET
from Bio import SeqIO
import sys
import os
import yaml
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord
import csv
from xml.dom import minidom
import shutil

config_dict = dict()
required_config = dict()
pd.set_option("display.max_columns", None)
pd.set_option("max_colwidth", None)
pd.set_option("display.max_rows", None)

#Create BioSample/SRA xml
def generate_XML(unique_name, main_df, generate_biosample, generate_sra, config_dict):
    day = str(date.today())
    dt = datetime.strptime(day, "%Y-%m-%d")
    submission = ET.Element("Submission")
    description = ET.SubElement(submission, "Description")
    title = ET.SubElement(description, "Title")
    if generate_biosample == True and generate_sra == True:
        title.text = unique_name + "_Biosample_SRA"
        comment = ET.SubElement(description, "Comment")
        comment.text = "BP(1.0)+BS(1.0)+SRA"
    elif generate_biosample == False and generate_sra == True:
        title.text = unique_name + "_SRA"
        comment = ET.SubElement(description, "Comment")
        comment.text = "SRA"
    elif generate_biosample == True and generate_sra == False:
        title.text = unique_name + "_Biosample"
        comment = ET.SubElement(description, "Comment")
        comment.text = "BP(1.0)+BS(1.0)"
    else:
        print("Error: This should not be reachable.", file=sys.stderr)
        sys.exit(1)
    org = ET.SubElement(description, "Organization")
    org.set("role", "owner")
    org.set("type","institute")
    if config_dict["general"]["ncbi_org_id"] != "":
        org.set("org_id", config_dict["general"]["ncbi_org_id"])
    name = ET.SubElement(org, "Name")
    email = ET.SubElement(org, "Contact")
    email.set("email", config_dict["general"]["contact_email1"])
    name.text = config_dict["general"]["organization_name"]
    name = ET.SubElement(email, "Name")
    first = ET.SubElement(name, "First")
    last = ET.SubElement(name, "Last")
    first.text = config_dict["general"]["submitter_info"]["first"]
    last.text = config_dict["general"]["submitter_info"]["last"]
    if generate_biosample == True:
        required = set(required_config["BioSample"])
        if required.issubset(config_dict["BioSample_attributes"]["column_names"].values()) == False:
            print("Error: Metadata file is missing required columns for BioSample file. Required columns in config are: " + str(required_config["BioSample"]), file=sys.stderr)
            sys.exit(1)
        for index, row in main_df.iterrows():
            action2 = ET.SubElement(submission, "Action")
            addData = ET.SubElement(action2, "AddData")
            addData.set("target_db","BioSample")
            data_tag = ET.SubElement(addData, "Data")
            data_tag.set("content_type","xml")
            xmlC = ET.SubElement(data_tag, "XmlContent")
            bioS = ET.SubElement(xmlC, "BioSample")
            bioS.set("schema_version","2.0")
            samID = ET.SubElement(bioS, "SampleId")
            spuid = ET.SubElement(samID, "SPUID")
            spuid.set("spuid_namespace",config_dict["ncbi"]["Center_title"])
            spuid.text = row[config_dict["ncbi"]["BioSample_sample_name_col"]]
            des = ET.SubElement(bioS, "Descriptor")
            title = ET.SubElement(des, "Title")
            title.text = config_dict["ncbi"]["publication_title"]
            org = ET.SubElement(bioS, "Organism")
            orgName = ET.SubElement(org, "OrganismName")
            orgName.text = config_dict["general"]["organism_name"]
            if config_dict["ncbi"]["BioProject"] != "":
                biop = ET.SubElement(bioS, "BioProject")
                primeID = ET.SubElement(biop, "PrimaryId")
                primeID.set("db","BioProject")
                primeID.text = config_dict["ncbi"]["BioProject"]
            pack = ET.SubElement(bioS, "Package")
            pack.text = config_dict["ncbi"]["BioSample_package"]
            attr = ET.SubElement(bioS,"Attributes")
            attr_str = ET.SubElement(attr, "Attribute")
            attr_str.set("attribute_name", "collection_date")
            attr_str.text = row[config_dict["general"]["collection_date_col"]]
            for key, value in config_dict["BioSample_attributes"]["column_names"].items():
                attr_str = ET.SubElement(attr, "Attribute")
                attr_str.set("attribute_name", key)
                attr_str.text = row[value]
            if config_dict["general"]["baseline_surveillance"] == True:
                attr_str = ET.SubElement(attr, "Attribute")
                attr_str.set("attribute_name", "purpose_of_sequencing")
                attr_str.text = "baseline surveillance (random sampling)"
            id = ET.SubElement(addData, "Identifier")
            spuid = ET.SubElement(id, "SPUID")
            spuid.set("spuid_namespace",config_dict["ncbi"]["Center_title"])
            spuid.text = row[config_dict["ncbi"]["BioSample_sample_name_col"]]
    if generate_sra == True:
        required = set(required_config["SRA"])
        if required.issubset(config_dict["SRA_attributes"]["column_names"].values()) == False:
            print("Error: Metadata file is missing required columns for SRA file. Required columns in config are: " + str(required_config["SRA"]), file=sys.stderr)
            sys.exit(1)
        for index, row in main_df.iterrows():
            #Add Illumina data
            if row[config_dict["ncbi"]["SRA_file_column1"]] != "" and pd.isnull(row[config_dict["ncbi"]["SRA_file_column1"]]) == False:
                action3 = ET.SubElement(submission, "Action")
                addfile = ET.SubElement(action3, "AddFiles")
                addfile.set("target_db","SRA")
                file = ET.SubElement(addfile, "File")
                file.set("file_path", os.path.basename(row[config_dict["ncbi"]["SRA_file_column1"]]))
                datatype=ET.SubElement(file, "DataType")
                datatype.text = "generic-data"
                if row[config_dict["ncbi"]["SRA_file_column2"]] != "" and pd.isnull(row[config_dict["ncbi"]["SRA_file_column2"]]) == False:
                    file = ET.SubElement(addfile, "File")
                    file.set("file_path", os.path.basename(row[config_dict["ncbi"]["SRA_file_column2"]]))
                    datatype=ET.SubElement(file, "DataType")
                    datatype.text = "generic-data"
                for key, value in config_dict["SRA_attributes"]["column_names"].items():
                    attr_str = ET.SubElement(addfile, "Attribute")
                    attr_str.set("name", key)
                    if key in ["sequencing_instrument", "library_strategy", "library_source", "library_selection", "library_layout", "library_name"]:
                        attr_str.text = row["illumina_" + value]
                    else:
                        attr_str.text = row[value]
                if any(x.isalpha() for x in config_dict["ncbi"]["SRA_file_loader"]):
                    attr_str = ET.SubElement(addfile, "Attribute")
                    attr_str.set("name", "loader")
                    attr_str.text = config_dict["ncbi"]["SRA_file_loader"]
                if config_dict["ncbi"]["BioProject"] != "":
                    Attr_ref = ET.SubElement(addfile, "AttributeRefId")
                    Attr_ref.set("name","BioProject")
                    refid = ET.SubElement(Attr_ref, "RefId")
                    primid = ET.SubElement(refid, "PrimaryId")
                    primid.text = config_dict["ncbi"]["BioProject"]
                if generate_biosample == True or config_dict["general"]["submit_BioSample"] == True:
                    Attr_ref = ET.SubElement(addfile, "AttributeRefId")
                    Attr_ref.set("name","BioSample")
                    refid = ET.SubElement(Attr_ref, "RefId")
                    spuid = ET.SubElement(refid, "SPUID")
                    spuid.set("spuid_namespace",config_dict["ncbi"]["Center_title"])
                    spuid.text = row[config_dict["ncbi"]["BioSample_sample_name_col"]]
                id = ET.SubElement(addfile, "Identifier")
                spuid = ET.SubElement(id, "SPUID")
                spuid.set("spuid_namespace",config_dict["ncbi"]["Center_title"])
                spuid.text = row[config_dict["ncbi"]["SRA_sample_name_col"]] + "_illumina"
            #Add Nanopore data
            if row[config_dict["ncbi"]["SRA_file_column3"]] != "" and pd.isnull(row[config_dict["ncbi"]["SRA_file_column3"]]) == False:
                action3 = ET.SubElement(submission, "Action")
                addfile = ET.SubElement(action3, "AddFiles")
                addfile.set("target_db","SRA")
                file = ET.SubElement(addfile, "File")
                file.set("file_path", os.path.basename(row[config_dict["ncbi"]["SRA_file_column3"]]))
                datatype=ET.SubElement(file, "DataType")
                datatype.text = "generic-data"
                for key, value in config_dict["SRA_attributes"]["column_names"].items():
                    attr_str = ET.SubElement(addfile, "Attribute")
                    attr_str.set("name", key)
                    if key in ["sequencing_instrument", "library_strategy", "library_source", "library_selection", "library_layout", "library_name"]:
                        attr_str.text = row["nanopore_" + value]
                    else:
                        attr_str.text = row[value]
                if any(x.isalpha() for x in config_dict["ncbi"]["SRA_file_loader"]):
                    attr_str = ET.SubElement(addfile, "Attribute")
                    attr_str.set("name", "loader")
                    attr_str.text = config_dict["ncbi"]["SRA_file_loader"]
                if config_dict["ncbi"]["BioProject"] != "":
                    Attr_ref = ET.SubElement(addfile, "AttributeRefId")
                    Attr_ref.set("name","BioProject")
                    refid = ET.SubElement(Attr_ref, "RefId")
                    primid = ET.SubElement(refid, "PrimaryId")
                    primid.text = config_dict["ncbi"]["BioProject"]
                if generate_biosample == True or config_dict["general"]["submit_BioSample"] == True:
                    Attr_ref = ET.SubElement(addfile, "AttributeRefId")
                    Attr_ref.set("name","BioSample")
                    refid = ET.SubElement(Attr_ref, "RefId")
                    spuid = ET.SubElement(refid, "SPUID")
                    spuid.set("spuid_namespace",config_dict["ncbi"]["Center_title"])
                    spuid.text = row[config_dict["ncbi"]["BioSample_sample_name_col"]]
                id = ET.SubElement(addfile, "Identifier")
                spuid = ET.SubElement(id, "SPUID")
                spuid.set("spuid_namespace",config_dict["ncbi"]["Center_title"])
                spuid.text = row[config_dict["ncbi"]["SRA_sample_name_col"]] + "_nanopore"
    xml_file = minidom.parseString(ET.tostring(submission, encoding="unicode", method="xml")).toprettyxml(indent = "   ")
    if generate_sra == True:
        main_df.to_csv(os.path.join(unique_name, "biosample_sra", unique_name + "_sra_path.csv"), header = True, index = 0, columns = [config_dict["ncbi"]["SRA_file_column1"], config_dict["ncbi"]["SRA_file_column2"], config_dict["ncbi"]["SRA_file_column3"]])
    if generate_sra == True and generate_biosample == True:
        with open(os.path.join(unique_name, "biosample_sra", unique_name + "_biosample_sra_submission.xml"),"w+") as f:
            f.write(xml_file)
    elif generate_sra == False and generate_biosample == True:
        with open(os.path.join(unique_name, "biosample_sra", unique_name + "_biosample_submission.xml"),"w+") as f:
            f.write(xml_file)
    elif generate_sra == True and generate_biosample == False:
        with open(os.path.join(unique_name, "biosample_sra", unique_name + "_sra_submission.xml"),"w+") as f:
            f.write(xml_file)
    else:
        print("Error: This should not be reachable.", file=sys.stderr)
        sys.exit(1)

#Initialize config file
def initialize_global_variables(config):
    if os.path.isfile(config) == False:
        print("Error: Cannot find submission config at: " + config, file=sys.stderr)
        sys.exit(1)
    else:
        with open(config, "r") as f:
            global config_dict
            config_dict = yaml.safe_load(f)
        if isinstance(config_dict, dict) == False:
            print("Config Error: Config file structure is incorrect.", file=sys.stderr)
            sys.exit(1)

#Initialize required columns config file
def initialize_required_columns(config):
    if os.path.isfile(config) == False:
        print("Error: Cannot find submission config at: " + config, file=sys.stderr)
        sys.exit(1)
    else:
        with open(config, "r") as f:
            global required_config
            required_config = yaml.safe_load(f)
        if isinstance(required_config, dict) == False:
            print("Config Error: Config file structure is incorrect.", file=sys.stderr)
            sys.exit(1)

#Convert fasta into df
def fasta_processing(fasta_file):
    if os.path.isfile(fasta_file) == False:
        print("Error: Fasta file does not exist at: \n" + fasta_file, file=sys.stderr)
        sys.exit(1)
    fasta_dict = []
    with open(fasta_file, "r") as fsa:
        records = SeqIO.parse(fsa, "fasta")
        for record in records:
            fasta_dict.append({"fasta_name_orig":record.id, "fasta_sequence_orig":record.seq, "fasta_description_orig":record.description})
    return pd.DataFrame(fasta_dict)

#Convert metadata into df
def metadata_processing(metadata_file, config_dict):
    if os.path.isfile(metadata_file) == False:
        print("Error: Metadata file does not exist at: \n" + metadata_file, file=sys.stderr)
        sys.exit(1)
    metadata = pd.read_csv(metadata_file, header = 0, dtype = str, sep = config_dict["general"]["metadata_file_sep"], engine = "python", encoding="windows-1254")
    metadata = metadata.fillna("")
    return metadata

#Merge files and checks
def merge(fasta_file, metadata_file, config_dict):
    fasta = fasta_processing(fasta_file)
    metadata = metadata_processing(metadata_file, config_dict)
    main_df = fasta.merge(metadata, left_on = "fasta_name_orig",  right_on = config_dict["general"]["fasta_sample_name_col"], how = "left")
    if main_df[config_dict["general"]["fasta_sample_name_col"]].isnull().values.any():
        print("Error: Fasta has sequences not in metadata: \n\n", file=sys.stderr)
        print(main_df[main_df[config_dict["general"]["fasta_sample_name_col"]].isna()]["fasta_name_orig"], file=sys.stderr)
        sys.exit(1)
    try:
        main_df[config_dict["general"]["collection_date_col"]] = pd.to_datetime(main_df[config_dict["general"]["collection_date_col"]])
        main_df[config_dict["general"]["collection_date_col"]] = main_df[config_dict["general"]["collection_date_col"]].dt.strftime('%Y-%m')
        main_df["sequencing_instrument"] = (main_df["illumina_sequencing_instrument"] + "; " + main_df["nanopore_sequencing_instrument"]).str.strip('; ')
    except:
        print("Error: datetime column error for " + config_dict["general"]["collection_date_col"])
    return main_df

# Write gisaid files
def gisaid_write(unique_name, main_df, config_dict):
    gisaid_df = pd.DataFrame()
    for key, val in config_dict["gisaid"]["column_names"].items():
        gisaid_df[key] = main_df[val]
    gisaid_df["covv_virus_name"] = main_df[config_dict["gisaid"]["gisaid_sample_name_col"]]
    gisaid_df["covv_collection_date"] = main_df[config_dict["general"]["collection_date_col"]]
    gisaid_columns = set(gisaid_df.columns.values.tolist())
    all_columns = ["submitter","fn","covv_virus_name","covv_type","covv_passage","covv_collection_date","covv_location","covv_add_location","covv_host","covv_add_host_info","covv_gender","covv_patient_age","covv_patient_status","covv_specimen","covv_outbreak","covv_last_vaccinated","covv_treatment","covv_seq_technology","covv_assembly_method","covv_sampling_strategy","covv_coverage","covv_orig_lab","covv_orig_lab_addr","covv_provider_sample_id","covv_subm_lab","covv_subm_lab_addr","covv_subm_sample_id","covv_authors","covv_comment","comment_type"]
    required = set(required_config["Gisaid"])
    if required.issubset(gisaid_columns) == False:
        print("Error: Metadata file is missing required columns for Gisaid file. Required columns in config are: " + str(required_config["Gisaid"]), file=sys.stderr)
        sys.exit(1)
    gisaid_df["submitter"] = config_dict["gisaid"]["username"]
    gisaid_df["fn"] = unique_name + "_gisaid.fsa"
    gisaid_df["covv_type"] = config_dict["gisaid"]["type"]
    gisaid_df["covv_subm_lab"] = config_dict["ncbi"]["citation_address"]["affil"] + " " + config_dict["ncbi"]["citation_address"]["div"]
    gisaid_df["covv_subm_lab_addr"] = config_dict["ncbi"]["citation_address"]["street"] + ", " + config_dict["ncbi"]["citation_address"]["city"] + ", " + config_dict["ncbi"]["citation_address"]["sub"] + ", " + config_dict["ncbi"]["citation_address"]["country"] + config_dict["ncbi"]["citation_address"]["postal-code"]
    author_list = ""
    for name in config_dict["general"]["authorset"]:
        if author_list == "":
            author_list = name["first"] + " " + name["last"]
        else:
            author_list = author_list + "," + name["first"] + " " + name["last"]
    gisaid_df["covv_authors"] = author_list
    if config_dict["general"]["baseline_surveillance"] == True:
        gisaid_df["covv_sampling_strategy"] = "Baseline surveillance"
    for col in all_columns:
        if col not in gisaid_df:
            gisaid_df[col] = ""
    gisaid_df = gisaid_df[all_columns]
    gisaid_df = gisaid_df.fillna("Unknown")
    gisaid_df = gisaid_df.replace(r'^\s*$', "Unknown", regex=True)
    gisaid_df = gisaid_df.replace(r'^\s*$', "Unknown", regex=True)
    gisaid_df["covv_comment"] = gisaid_df["covv_comment"].replace("Unknown", "")
    gisaid_df["comment_type"] = gisaid_df["comment_type"].replace("Unknown", "")
    gisaid_df.to_csv(os.path.join(unique_name,"gisaid",unique_name + "_gisaid.csv"), na_rep="Unknown", index = False, header = True, quoting=csv.QUOTE_ALL)
    records = []
    for index, row in main_df.iterrows():
        records.append(SeqRecord(row["fasta_sequence_orig"], id = row[config_dict["gisaid"]["gisaid_sample_name_col"]], description = ""))
    with open(os.path.join(unique_name,"gisaid",unique_name + "_gisaid.fsa"), "w+") as fasta_file:
        SeqIO.write(records, fasta_file, "fasta")

#Merge user's metadata file into genbank formatted metadata files
def write_metadata_files(unique_name, main_df, config_dict):
    src_df = pd.DataFrame()
    for key, val in config_dict["genbank_src_metadata"]["column_names"].items():
        src_df[key] = main_df[val]
    src_df["sequence_ID"] = main_df[config_dict["ncbi"]["Genbank_sample_name_col"]]
    if config_dict["ncbi"]["BioProject"] != "":
        src_df["BioProject"] = config_dict["ncbi"]["BioProject"]
    src_df["organism"] = config_dict["general"]["organism_name"]
    src_df["collection-date"] = main_df[config_dict["general"]["collection_date_col"]]
    src_columns = src_df.columns.values.tolist()
    src_columns_set = set(src_columns)
    src_columns.remove("sequence_ID")
    src_columns.insert(0, "sequence_ID")
    src_df = src_df[src_columns]
    required = set(required_config["Genbank"]['required_src_columns'])
    if required.issubset(src_columns_set) == False:
        print("Error: Metadata file is missing required columns for src file. Required columns in config are: " + str(required_config["Genbank"]['required_src_columns']), file=sys.stderr)
        sys.exit(1)
    src_df.to_csv(os.path.join(unique_name,"genbank",unique_name + "_source.src"), header = True, index = False, sep = "\t")
    #Create optional cmt file
    if config_dict["genbank_cmt_metadata"]['create_cmt'] == True:
        cmt_df = pd.DataFrame()
        for key, val in config_dict["genbank_cmt_metadata"]["column_names"].items():
            cmt_df[key] = main_df[val]
        cmt_df["SeqID"] = main_df[config_dict["ncbi"]["Genbank_sample_name_col"]]
        cmt_columns = set(cmt_df.columns.values.tolist())
        required = set(required_config["Genbank"]['required_cmt_columns'])
        if required.issubset(cmt_columns) == False:
            print("Error: Metadata file is missing required columns for cmt file. Required columns in config are: " + str(required_config["Genbank"]['required_cmt_columns']), file=sys.stderr)
            sys.exit(1)
        ordered_columns = ["SeqID","StructuredCommentPrefix","Assembly Method", "Sequencing Technology"]
        for col in cmt_columns:
            if col not in ["SeqID","StructuredCommentPrefix","Assembly Method", "Sequencing Technology","StructuredCommentSuffix"]:
                ordered_columns.append(col)
        ordered_columns.append("StructuredCommentSuffix")
        cmt_df = cmt_df.reindex(columns=ordered_columns)
        cmt_df.to_csv(os.path.join(unique_name,"genbank",unique_name + "_comment.cmt"), header = True, index = False, sep = "\t")

#Write submission file
def write_submission_files(unique_name, main_df, config_dict):
    with open(os.path.join(unique_name, "genbank", "submission.xml"), "w+") as f:
        f.write("<?xml version=\"1.0\"?>\n")
        f.write("<Submission>\n")
        f.write("  <Description>\n")
        f.write("    <Title>" + unique_name + "</Title>\n")
        f.write("    <Comment>FTP submission</Comment>\n")
        f.write("    <Organization type=\"" + config_dict["ncbi"]["Genbank_organization_type"] + "\" role=\"" + config_dict["ncbi"]["Genbank_organization_role"] + "\">\n")
        f.write("      <Name>" + config_dict["ncbi"]["Center_title"] + "</Name>\n")
        f.write("    </Organization>\n")
        f.write("  </Description>\n")
        f.write("  <Action>\n")
        f.write("    <AddFiles target_db=\"GenBank\">\n")
        f.write("      <File file_path=\"" + unique_name + ".zip\">\n")
        f.write("        <DataType>genbank-submission-package</DataType>\n")
        f.write("      </File>\n")
        f.write("      <Attribute name=\"wizard\">" + config_dict["ncbi"]["Genbank_wizard"] + "</Attribute>\n")
        if config_dict["ncbi"]["Genbank_auto_remove_sequences_that_fail_qc"] == True:
            f.write("      <Attribute name=\"auto_remove_failed_seqs\">yes</Attribute>\n")
        else:
            f.write("      <Attribute name=\"auto_remove_failed_seqs\">no</Attribute>\n")
        f.write("      <Identifier>\n")
        f.write("        <SPUID spuid_namespace=\"" + config_dict["ncbi"]["Genbank_spuid_namespace"] + "\">" + unique_name + "</SPUID>\n")
        f.write("      </Identifier>\n")
        f.write("    </AddFiles>\n")
        f.write("  </Action>\n")
        f.write("</Submission>\n")
    #Create authorset file
    with open(os.path.join(unique_name, "genbank", unique_name + "_authorset.sbt"), "w+") as f:
        f.write("Submit-block ::= {\n")
        f.write("  contact {\n")
        f.write("    contact {\n")
        f.write("      name name {\n")
        f.write("        last \"" + config_dict["general"]["submitter_info"]["last"] + "\",\n")
        f.write("        first \"" + config_dict["general"]["submitter_info"]["first"] + "\",\n")
        f.write("        middle \"" + config_dict["general"]["submitter_info"]["middle"] + "\",\n")
        f.write("        initials \"" + config_dict["general"]["submitter_info"]["initials"] + "\",\n")
        f.write("        suffix \"" + config_dict["general"]["submitter_info"]["suffix"] + "\",\n")
        f.write("        title \"" + config_dict["general"]["submitter_info"]["title"] + "\"\n")
        f.write("      },\n")
        f.write("      affil std {\n")
        f.write("        affil \"" + config_dict["ncbi"]["citation_address"]["affil"] + "\",\n")
        f.write("        div \"" + config_dict["ncbi"]["citation_address"]["div"] + "\",\n")
        f.write("        city \"" + config_dict["ncbi"]["citation_address"]["city"] + "\",\n")
        f.write("        sub \"" + config_dict["ncbi"]["citation_address"]["sub"] + "\",\n")
        f.write("        country \"" + config_dict["ncbi"]["citation_address"]["country"] + "\",\n")
        f.write("        street \"" + config_dict["ncbi"]["citation_address"]["street"] + "\",\n")
        f.write("        email \"" + config_dict["ncbi"]["citation_address"]["email"] + "\",\n")
        f.write("        phone \"" + config_dict["ncbi"]["citation_address"]["phone"] + "\"\n")
        f.write("      }\n")
        f.write("    }\n")
        f.write("  },\n")
        f.write("  cit {\n")
        f.write("    authors {\n")
        f.write("      names std {\n")
        total_names = len(config_dict["general"]["authorset"])
        name_counter = 0
        for person in config_dict["general"]["authorset"]:
            f.write("        {\n")
            f.write("          name name {\n")
            f.write("            last \"" + person["last"] + "\",\n")
            f.write("            first \"" + person["first"] + "\",\n")
            f.write("            middle \"" + person["middle"] + "\",\n")
            f.write("            initials \"" + person["initials"] + "\",\n")
            f.write("            suffix \"" + person["suffix"] + "\",\n")
            f.write("            title \"" + person["title"] + "\"\n")
            f.write("          }\n")
            name_counter += 1
            if name_counter == total_names:
                f.write("        }\n")
            else:
                f.write("        },\n")
        f.write("      },\n")
        f.write("      affil std {\n")
        f.write("        affil \"" + str(config_dict["ncbi"]["citation_address"]["affil"]) + "\",\n")
        f.write("        div \"" + str(config_dict["ncbi"]["citation_address"]["div"]) + "\",\n")
        f.write("        city \"" + str(config_dict["ncbi"]["citation_address"]["city"]) + "\",\n")
        f.write("        sub \"" + str(config_dict["ncbi"]["citation_address"]["sub"]) + "\",\n")
        f.write("        country \"" + str(config_dict["ncbi"]["citation_address"]["country"]) + "\",\n")
        f.write("        street \"" + str(config_dict["ncbi"]["citation_address"]["street"]) + "\",\n")
        f.write("        postal-code \"" + str(config_dict["ncbi"]["citation_address"]["postal-code"]) + "\"\n")
        f.write("      }\n")
        f.write("    }\n")
        f.write("  },\n")
        f.write("  subtype new\n")
        f.write("}\n")
        f.write("Seqdesc ::= pub {\n")
        f.write("  pub {\n")
        f.write("    gen {\n")
        f.write("      cit \"unpublished\",\n")
        f.write("      authors {\n")
        f.write("        names std {\n")
        total_names = len(config_dict["general"]["authorset"])
        name_counter = 0
        for person in config_dict["general"]["authorset"]:
            f.write("          {\n")
            f.write("            name name {\n")
            f.write("              last \"" + person["last"] + "\",\n")
            f.write("              first \"" + person["first"] + "\",\n")
            f.write("              middle \"" + person["middle"] + "\",\n")
            f.write("              initials \"" + person["initials"] + "\",\n")
            f.write("              suffix \"" + person["suffix"] + "\",\n")
            f.write("              title \"" + person["title"] + "\"\n")
            f.write("            }\n")
            name_counter += 1
            if name_counter == total_names:
                f.write("          }\n")
            else:
                f.write("          },\n")
        f.write("        }\n")
        f.write("      },\n")
        f.write("      title \"" + config_dict["ncbi"]["publication_title"] + "\"\n")
        f.write("    }\n")
        f.write("  }\n")
        f.write("}\n")
        f.write("Seqdesc ::= user {\n")
        f.write("  type str \"Submission\",\n")
        f.write("  data {\n")
        f.write("    {\n")
        f.write("      label str \"AdditionalComment\",\n")
        f.write("      data str \"ALT EMAIL:" + config_dict["general"]["contact_email2"] + "\"\n")
        f.write("    }\n")
        f.write("  }\n")
        f.write("}\n")
        f.write("Seqdesc ::= user {\n")
        f.write("  type str \"Submission\",\n")
        f.write("  data {\n")
        f.write("    {\n")
        f.write("      label str \"AdditionalComment\",\n")
        f.write("      data str \"" + unique_name + "\"\n")
        f.write("    }\n")
        f.write("  }\n")
        f.write("}\n")

# Write fasta files
def ncbi_write(unique_name, main_df, gff_file, config_dict):
    if config_dict["general"]["baseline_surveillance"] == True:
        main_df["final_ncbi_fasta_name"] = main_df[config_dict["ncbi"]["Genbank_sample_name_col"]] +  " [keyword=purposeofsampling:baselinesurveillance]"
    else:
        main_df["final_ncbi_fasta_name"] = main_df[config_dict["ncbi"]["Genbank_sample_name_col"]]
    records = []
    for index, row in main_df.iterrows():
        records.append(SeqRecord(row["fasta_sequence_orig"], id = row["final_ncbi_fasta_name"], description = ""))
    with open(os.path.join(unique_name, "genbank", unique_name + "_ncbi.fsa"), "w+") as fasta_file:
        SeqIO.write(records, fasta_file, "fasta")
    if gff_file is not None:
        gff_df = pd.read_csv(gff_file, header = None, comment = "#", sep = "\t")
        column_names = range(len(gff_df. columns))
        column_names = [str(x) for x in column_names]
        gff_df.columns = column_names
        for index, row in main_df.iterrows():
            gff_df['0'] = gff_df['0'].replace([row[config_dict["general"]["fasta_sample_name_col"]]], row["final_ncbi_fasta_name"])
        #Read in comments
        comment_line = ""
        with open(gff_file, "r") as file:
            line = file.readline()
            while line:
                if line.startswith("#"):
                    comment_line = comment_line + line
                line = file.readline()
        with open(os.path.join(unique_name, "genbank", unique_name + ".gff"), "w+") as file:
            file.write(comment_line)
        gff_df.to_csv(os.path.join(unique_name, "genbank", unique_name + ".gff"), header = False, index = False, sep = "\t", mode = "a")

#If uploading files for SRA create csv with file paths
def write_sra_file_path(unique_name, main_df, config_dict):
    if config_dict["ncbi"]["SRA_file_location"] == "file":
        if config_dict["ncbi"]["SRA_file_column2"] != "":
            main_df.to_csv(os.path.join(unique_name,"biosample_sra", "sra_file_path.csv"), header = False, index = False, sep = ",", columns = [config_dict["ncbi"]["SRA_file_column1"], config_dict["ncbi"]["SRA_file_column2"]])
        else:
            main_df.to_csv(os.path.join(unique_name,"biosample_sra", "sra_file_path.csv"), header = False, index = False, sep = ",", columns = [config_dict["ncbi"]["SRA_file_column1"]])

def author_column_update(authorlist, config_dict):
    config_dict["general"]["authorset"] = authorlist

#For updating sequences based on auto-remove
def write_ncbi_names(unique_name, main_df, config_dict):
    tmp = pd.DataFrame()
    if config_dict["general"]["submit_SRA"] == True:
        tmp["SRA_sequence"] = main_df[config_dict["ncbi"]["SRA_sample_name_col"]]
    if config_dict["general"]["submit_BioSample"] == True:
        tmp["BioSample_sequence"] = main_df[config_dict["ncbi"]["BioSample_sample_name_col"]]
    if config_dict["general"]["submit_Genbank"] == True:
        tmp["Genbank_sequence"] = main_df[config_dict["ncbi"]["Genbank_sample_name_col"]]
    if config_dict["general"]["submit_GISAID"] == True:
        tmp["GISAID_sequence"] = main_df[config_dict["gisaid"]["gisaid_sample_name_col"]]
    tmp.to_csv(os.path.join(unique_name, "accessions.csv"), header = True, index = False, sep = ",")

def process_submission(unique_name, fasta_file, metadata_file, gff_file, config, req_col_config, config_dict):
    print("\nProcessing " + unique_name + ".")

    initialize_required_columns(req_col_config)
    
    print("Processing Files.")

    main_df = merge(fasta_file, metadata_file, config_dict)

    if not isinstance(config_dict["general"]["authorset"], list):
        authorlist = []
        name_list = main_df[config_dict["general"]["authorset"]].iloc[0].split(";")
        for name in name_list:
            name = name.strip()
            if len(name.split(" ")) == 2:
                authorlist.append({"first": name.split(" ")[0], "last": name.split(" ")[-1], "middle": "", "initials": name.split(" ")[0][0] + ".", "suffix": "", "title": ""})
            else:
                authorlist.append({"first": name.split(" ")[0], "last": name.split(" ")[-1], "middle": name.split(" ")[1], "initials": name.split(" ")[0][0] + "." + name.split(" ")[1][0] + ".", "suffix": "", "title": ""})
        author_column_update(authorlist, config_dict)

    os.makedirs(os.path.join(unique_name), exist_ok = True)

    if config_dict["general"]["submit_GISAID"] == True:
        print("Creating GISAID files.")
        os.makedirs(os.path.join(unique_name, "gisaid"), exist_ok = True)
        gisaid_write(unique_name, main_df, config_dict)

    if config_dict["general"]["submit_Genbank"] == True:
        print("Creating Genbank files.")
        os.makedirs(os.path.join(unique_name, "genbank"), exist_ok = True)
        write_metadata_files(unique_name, main_df, config_dict)
        write_submission_files(unique_name, main_df, config_dict)
        ncbi_write(unique_name, main_df, gff_file, config_dict)

    if config_dict["general"]["submit_BioSample"] == True and config_dict["general"]["submit_SRA"] == True and config_dict["general"]["joint_SRA_BioSample_submission"] == True:
        print("Creating BioSample/SRA files.")
        os.makedirs(os.path.join(unique_name, "biosample_sra"), exist_ok = True)
        generate_XML(unique_name = unique_name, main_df = main_df, generate_biosample = True, generate_sra = True, config_dict=config_dict)
        write_sra_file_path(unique_name, main_df, config_dict)

    else:
        if config_dict["general"]["submit_BioSample"] == True:
            print("Creating BioSample files.")
            os.makedirs(os.path.join(unique_name, "biosample_sra"), exist_ok = True)
            generate_XML(unique_name = unique_name, main_df = main_df, generate_biosample = True, generate_sra = False, config_dict=config_dict)

        if config_dict["general"]["submit_SRA"] == True:
            print("Creating SRA files.")
            os.makedirs(os.path.join(unique_name, "biosample_sra"), exist_ok = True)
            generate_XML(unique_name = unique_name, main_df = main_df, generate_biosample = False, generate_sra = True, config_dict=config_dict)
            write_sra_file_path(unique_name, main_df, config_dict)

    if config_dict["general"]["submit_BioSample"] == True or config_dict["general"]["submit_SRA"] == True or config_dict["general"]["submit_Genbank"] == True:
        write_ncbi_names(unique_name, main_df, config_dict)

    print(unique_name + " complete.\n")
