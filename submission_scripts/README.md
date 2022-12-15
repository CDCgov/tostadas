# Public Database Submission Pipeline

**General disclaimer** This repository was created for use by CDC programs to collaborate on public health related projects in support of the [CDC mission](https://www.cdc.gov/about/organization/mission.htm).  GitHub is not hosted by the CDC, but is a third party website used by CDC and its partners to share information and collaborate on software. CDC use of GitHub does not imply an endorsement of any one particular service, product, or enterprise. 

## Common MPXV usage
Submitting annotated genome (with or without Illumina reads for SRA). Metadata sheets should be prepared using the template in [sample-submission](https://git.biotech.cdc.gov/monkeypox/sample-submission) and validated using [mpxv-annotation-transfer](https://git.biotech.cdc.gov/monkeypox/mpxv-annotation-transfer). Example:
```bash
source /scicomp/groups-pure/Projects/scbs_mpob/miniconda3.9/bin/activate /scicomp/groups-pure/Projects/scbs_mpob/miniconda3.9/envs/monkeypox/

/scicomp/groups-pure/Projects/scbs_mpob/submissions/repos/mpxv-database-submissions/submission.py submit \
--unique_name 20220913-0010.GA0001 \
--fasta /scicomp/groups-pure/Projects/scbs_mpob/results/annotation-transfer/20220913-0010/GA0001.fasta \
--metadata /scicomp/groups-pure/Projects/scbs_mpob/results/annotation-transfer/20220913-0010/20220913-0010.GA0001.tsv \
--gff /scicomp/groups-pure/Projects/scbs_mpob/results/annotation-transfer/20220913-0010/GA0001.gff \
--config mpxv-noSRA_config.yaml;

# wait ~15mins for BioSample to process

/scicomp/groups-pure/Projects/scbs_mpob/submissions/repos/mpxv-database-submissions/submission.py update_submissions

# submit the ASN1 (*.sqn) file to GenBank via email attachment to gb-submit@ncbi.nlm.nih.gov

```  

Submissions are usually processed in batches, but `submission.py` currently only processes Genomes individually, so a simple loop is helpful:
```bash
source /scicomp/groups-pure/Projects/scbs_mpob/miniconda3.9/bin/activate /scicomp/groups-pure/Projects/scbs_mpob/miniconda3.9/envs/monkeypox/

for f in $(ls *fasta ); do
        name=$(basename $f .fasta);
        /scicomp/groups-pure/Projects/scbs_mpob/submissions/repos/mpxv-database-submissions/submission.py submit \
        --unique_name 20220913-0010.$name \
        --fasta /scicomp/groups-pure/Projects/scbs_mpob/results/annotation-transfer/20220913-0010/$name.fasta \
        --metadata /scicomp/groups-pure/Projects/scbs_mpob/results/annotation-transfer/20220913-0010/20220913-0010.$name.tsv \
        --gff /scicomp/groups-pure/Projects/scbs_mpob/results/annotation-transfer/20220913-0010/$name.corrected.gff \
        --config mpxv_config.yaml;
done

# wait ~15mins for BioSample to process

/scicomp/groups-pure/Projects/scbs_mpob/submissions/repos/mpxv-database-submissions/submission.py update_submissions

# submit the ASN1 (*.sqn) files to GenBank via email attachment to gb-submit@ncbi.nlm.nih.gov

```  

Sometimes it's necessary to first submit to BioSample and GenBank only. Read submission to SRA can be performed later using the **same** [unique-name] with an **updated** [metadata sheet] and [config] via `submission.py prep`, for example:
```bash
source /scicomp/groups-pure/Projects/scbs_mpob/miniconda3.9/bin/activate /scicomp/groups-pure/Projects/scbs_mpob/miniconda3.9/envs/monkeypox/

for f in $(ls *fasta ); do
        name=$(basename $f .fasta);
        /scicomp/groups-pure/Projects/scbs_mpob/repos/mpxv-database-submissions/submission.py prep \
        --unique_name 20220913-0010.$name \
        --fasta /scicomp/groups-pure/Projects/scbs_mpob/results/annotation-transfer/20220913-0010/$name.fasta \
        --metadata /scicomp/groups-pure/Projects/scbs_mpob/results/annotation-transfer/20220913-0010/20220913-0010.$name.SRA.tsv \
        --gff /scicomp/groups-pure/Projects/scbs_mpob/results/annotation-transfer/20220913-0010/$name.corrected.gff \
        --config mpxv_config.yaml;

        /scicomp/groups-pure/Projects/scbs_mpob/repos/mpxv-database-submissions/submission.py sra \
        --unique_name 20220913-0010.$name \
        --config mpxv_config.yaml;

done
```  

The satus of all API submissions to BioSample and SRA can be viewed in the [NCBI submission portal](https://submit.ncbi.nlm.nih.gov/subs/).

---
---
## Overview
Public Database Submission Pipeline is used to generate the files necessary to upload via FTP to NCBI's databases Genbank, BioSample, and SRA, as well as, GISAID. The pipeline then automatically performs the sequential upload to these databases to ensure proper linkage of data. The pipeline is dynamic in that the user creates a config file to select which databases they would like to upload and allows for any possible metadata fields by using a YAML to pair the database's metadata fields which your personal metadata field columns. This pipeline is currently tested with uploading SARS-COV-2 data but the dynamic nature of this pipeline will allow for other organism's in future updates.
		
## Setup:
### 1. Account Creation:
- **NCBI:** A NCBI account is required along with a center account approved for submitting via FTP. Contact NCBI at gb-admin@ncbi.nlm.nih.gov to get a center account created.
- **GISAID:** A GISAID account is required for submitting, register at https://www.gisaid.org/. A test submission is required before production submissions are allowed. After making a test submission contact GISAID at hcov-19@gisaid.org to receive your personal CID.
		
### 2. Environment Setup:
- Clone files to working space and setup Python environment. Create a folder where you would like the program to generate the output to.
- Submission files will be created and processed here.
		
### 3. Config File Creation:
- The script will automatically default to the default_config.yaml. Multiple config files can be created and passed to the script via `--config <filename>.yaml`. 
- To create your config file fill out the empty spaces in the config file. Place the full path for the output directory you created and set what databases you want to submit to, to True or False. For the column_names sections of the config file place the corresponding datafield for the public repository to your metadata's column name for example`{"Public repository field":"Your metadata column"}`. 
- You must also create the naming schema for how you want the sequence to be named for the database and give the associated column name for the fields Genbank_sample_name_col, SRA_sample_name_col, BioSample_sample_name_col, and gisaid_sample_name_col. This is because the naming schema can vary between databases. 
- Refer to the database for what fields are required for submission and what options are available. For a full list of what is required in the config file, see the table below. 
	
### 4. Submission File Creation:
- Create all the submission files by running `submission.py prep --unique_name <> --fasta <> --metadata <>`. Provide the full path to the fasta and metadata file and give a unique name which will be used for the submission. 
- These cannot repeat as the submission name is what is used to upload to via FTP. Using a submission name again could result in your submission not processing.

### 5. GISAID Authentication (Required if submitting to GISAID):
- GISAID requires the script to be authenticated with the CID. To authenticate your script run `gisaid_uploader.py COV authenticate --cid TEST-EA76875B00C3`. 
- It will then ask you to provide your GISAID username and password. If this test CID no longer works refer to the GISAID upload CLI for the latest test CID on https://www.gisaid.org/.
- After performing a test submission you will need to run this command again with your official production CID provided by GISAID.

### 6. Test Submission:
- To perform your test submission run `submission.py submit --unique_name <> --fasta <> --metadata <> --test`. The flag `--test` will allow you to perform a test submission anytime to NCBI. However, this will not work for GISAID as submissions are based off the CID. This will submit the test submission to the automated pipeline using the test command. The automated pipeline will not submit test submissions to GISAID. To perform the test submission to GISAID run the command `submission.py gisaid --unique_name <> --test`, after running the submit command. 
- After performing the test submission run the command `submission.py update_submissions` for the script to automatically check the progress of submissions and to continue submitting sequences to the next database after accessions are generated for linking BioSample, SRA, and Genbank submissions together.
	
### 7. Final Setup:
- After successfully performing a test submission to every database you plan to submit to contact GISAID at hcov-19@gisaid.org to receive your production CID. Remember to update your config file to this new CID and authenticate the GISAID script with the new CID. 
- Contact gb-admin@ncbi.nlm.nih.gov to begin production submissions to NCBI after performing test submissions. 
- For production submissions run `submission.py submit --unique_name <> --fasta <> --metadata <>`, this will generate all the required file and place it in the automated pipeline. 
- To progress the automated pipeline run `submission.py update_submissions` every couple hours to process submissions.

## Commands:
- `submission.py submit --unique_name <> --fasta <> --metadata <>` Creates the files for submission and adds to automated submission pipeline and starts submission process. 
- `submission.py prep --unique_name <> --fasta <> --metadata <>` Creates the files for submission.
- `submission.py update_submissions` Updates process of all sequences in submission pipeline, performs submission to subsequent databases based on submission status.
- `submission.py gisaid --unique_name <>` Performs manual submission to GISAID.
- `submission.py genbank --unique_name <>` Performs manual submission to Genbank.
- `submission.py biosample --unique_name <>` Performs manual submission to BioSample.
- `submission.py sra --unique_name <>` Performs manual submission to SRA.
- `submission.py biosample_sra --unique_name <>` Performs manual joint submission to BioSample/SRA.

**Optional flags:**
- `--config <>` If using a different config file than the default config. Provide the full name of the config file stored in `config_files` folder. 
- `--test` Performs test submission to NCBI. Does not perform test submission to GISAID. You must used authenticated CID for test submission to GISAID.
- `--overwrite` Overwrites an existing submission on NCBI FTP. Used to update errored submissions. 

## Tips and Troubleshooting:
- If you need to update a submissions metadata mid submission run `submission.py prep --unique_name <> --fasta <> --metadata <>`. Then run `submission.py <database> --unique_name <> --fasta <> --metadata <> --overwrite` to overwrite an existing submission with the new files on the FTP server.
- If you receive an error for the config file it will notify you which line in the config file this is occurring. Common errors are missing quotes or having a comma after the last item.
- Large GISAID submissions occassionally time-out. The automated pipeline will attempt to make the submission again the next time it is ran. 
	
## Config File Fields:

| Section:             | Name:                                      | Description:                                                                                                                   | Required:                                             |
|----------------------|--------------------------------------------|--------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| General              | submission_directory                       | Output directory for script to process submissions at                                                                          | Yes                                                   |
| General              | submit_Genbank                             | Perform submission to Genbank                                                                                                  | Yes, True/False                                       |
| General              | submit_GISAID                              | Perform submission to GISAID                                                                                                   | Yes, True/False                                       |
| General              | submit_SRA                                 | Perform submission to SRA                                                                                                      | Yes, True/False                                       |
| General              | submit_BioSample                           | Perform submission to BioSample                                                                                                | Yes, True/False                                       |
| General              | joint_SRA_BioSample_submission             | Submit SRA and BioSample together as one submission                                                                            | Yes, True/False                                       |
| General              | contact_email1                             | Primary contact email                                                                                                          | Yes                                                   |
| General              | contact_email2                             | Secondary contact email                                                                                                        | No                                                    |
| General              | organization_name                          | Organization name                                                                                                              | Yes                                                   |
| General              | authorset                                  | List of authors for submission                                                                                                 | Yes                                                   |
| General              | ncbi_org_id                                | Center account organization ID                                                                                                 | Yes                                                   |
| General              | submitter_info                             | Primary submitter info                                                                                                         | Yes                                                   |
| General              | organism_name                              | Organism                                                                                                                       | Yes                                                   |
| General              | metadata_file_sep                          | File seperator used in your metadata file                                                                                      | Yes                                                   |
| General              | fasta_sample_name_col                      | Metadata column of sequence name used in fasta file                                                                            | Yes                                                   |
| General              | collection_date_col                        | Collection date for sequence                                                                                                   | Yes                                                   |
| General              | baseline_surveillance                      | If performing baseline_sequencing setting this to True will add   baseline_sequencing tag to all of your submissions           | Yes, True/False                                       |
| ncbi                 | hostname                                   | FTP site. Use ftp-private.ncbi.nlm.nih.gov                                                                                     | Yes                                                   |
| ncbi                 | api_url                                    | API url for pulling down files from NCBI   https://submit.ncbi.nlm.nih.gov/api/2.0/files/FILE_ID/?format=attachment            | Yes                                                   |
| ncbi                 | username                                   | NCBI center account username                                                                                                   | Yes                                                   |
| ncbi                 | password                                   | NCBI center account password                                                                                                   | Yes                                                   |
| ncbi                 | publication_title                          | Public facing title for submission                                                                                             | Yes                                                   |
| ncbi                 | ncbi_ftp_path_to_submission_folders        | If your FTP site does not directly have the folders for Production/Test   then provide the path for this. Typically left blank | No                                                    |
| ncbi                 | BioProject                                 | BioProject to link submissions to                                                                                              | No                                                    |
| ncbi                 | BioSample_sample_name_col                  | Sequence names for BioSample                                                                                                   | Yes, if submitting to BioSample                       |
| ncbi                 | SRA_sample_name_col                        | Sequence names for SRA                                                                                                         | Yes, if submitting to SRA                             |
| ncbi                 | Genbank_sample_name_col                    | Sequence names for Genbank                                                                                                     | Yes, if submitting to Genbank                         |
| ncbi                 | BioSample_package                          | Use SARS-CoV-2.cl.1.0                                                                                                          | Yes                                                   |
| ncbi                 | Center_title                               | Title for center account                                                                                                       | Yes                                                   |
| ncbi                 | Genbank_organization_type                  | Center organization type                                                                                                       | Yes                                                   |
| ncbi                 | Genbank_organization_role                  | Use owner unless otherwise specified                                                                                           | Yes                                                   |
| ncbi                 | Genbank_spuid_namespace                    | Use ncbi-sarscov2-genbank unless specified                                                                                     | Yes                                                   |
| ncbi                 | Genbank_auto_remove_sequences_that_fail_qc | Genbank can automatically remove sequences that fail submission qc in   order to not stall submissions                         | Yes True/False                                        |
| ncbi                 | Genbank_wizard                             | Use BankIt_SARSCoV2_api unless specified                                                                                       | Yes                                                   |
| ncbi                 | citation_address                           | Address of submitter organization                                                                                              | Yes                                                   |
| ncbi                 | SRA_file_location                          | Whether you are submitting SRA files via manual upload or cloud link                                                           | Yes, if submitting to SRA File/Cloud                  |
| ncbi                 | SRA_file_column1                           | Either name of file if uploading or full path to cloud link                                                                    | Yes, if submitting to SRA                             |
| ncbi                 | SRA_file_column2                           | Either name of file if uploading or full path to cloud link                                                                    | Yes, if submitting to SRA and you have multiple files |
| ncbi                 | SRA_file_loader                           | Leave blank unless notified by SRA team you need to use a specific loader for your SRA files                                                                    | No |
| genbank_src_metadata | column_names                               | Database field to column name of metadata                                                                                      | Yes                                                   |
| genbank_cmt_metadata | create_cmt                                 | Create cmt file to go with submission                                                                                          | Yes True/False                                        |
| genbank_cmt_metadata | column_names                               | Database field to column name of metadata                                                                                      | Yes                                                   |
| BioSample_attributes | column_names                               | Database field to column name of metadata                                                                                      | Yes                                                   |
| SRA_attributes       | column_names                               | Database field to column name of metadata                                                                                      | Yes                                                   |
| gisaid               | column_names                               | Database field to column name of metadata                                                                                      | Yes                                                   |
| gisaid               | gisaid_sample_name_col                     | Sequence names for GISAID                                                                                                      | Yes, if submitting to GISAID                          |
| gisaid               | cid                                        | CID used for submission                                                                                                        | Yes                                                   |
| gisaid               | username                                   | gisaid username                                                                                                                | Yes                                                   |
| gisaid               | password                                   | GISAID password                                                                                                                | Yes                                                   |
| gisaid               | type                                       | Use betacoronavirus unless specified                                                                                           | Yes                                                   |
| gisaid               | Update_sequences_on_Genbank_auto_removal   | If using Genbank auto-remove qc then use this to update the GISAID   submission based on what is accepted by Genbank           | Yes True/False                                        |

  
## Public Domain Standard Notice
This repository constitutes a work of the United States Government and is not
subject to domestic copyright protection under 17 USC § 105. This repository is in
the public domain within the United States, and copyright and related rights in
the work worldwide are waived through the [CC0 1.0 Universal public domain dedication](https://creativecommons.org/publicdomain/zero/1.0/).
All contributions to this repository will be released under the CC0 dedication. By
submitting a pull request you are agreeing to comply with this waiver of
copyright interest.

## License Standard Notice
The repository utilizes code licensed under the terms of the Apache Software
License and therefore is licensed under ASL v2 or later.

This source code in this repository is free: you can redistribute it and/or modify it under
the terms of the Apache Software License version 2, or (at your option) any
later version.

This source code in this repository is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the Apache Software License for more details.

You should have received a copy of the Apache Software License along with this
program. If not, see http://www.apache.org/licenses/LICENSE-2.0.html

The source code forked from other open source projects will inherit its license.

## Privacy Standard Notice
This repository contains only non-sensitive, publicly available data and
information. All material and community participation is covered by the
[Disclaimer](https://github.com/CDCgov/template/blob/master/DISCLAIMER.md)
and [Code of Conduct](https://github.com/CDCgov/template/blob/master/code-of-conduct.md).
For more information about CDC's privacy policy, please visit [http://www.cdc.gov/other/privacy.html](https://www.cdc.gov/other/privacy.html).

## Contributing Standard Notice
Anyone is encouraged to contribute to the repository by [forking](https://help.github.com/articles/fork-a-repo)
and submitting a pull request. (If you are new to GitHub, you might start with a
[basic tutorial](https://help.github.com/articles/set-up-git).) By contributing
to this project, you grant a world-wide, royalty-free, perpetual, irrevocable,
non-exclusive, transferable license to all users under the terms of the
[Apache Software License v2](http://www.apache.org/licenses/LICENSE-2.0.html) or
later.

All comments, messages, pull requests, and other submissions received through
CDC including this GitHub page may be subject to applicable federal law, including but not limited to the Federal Records Act, and may be archived. Learn more at [http://www.cdc.gov/other/privacy.html](http://www.cdc.gov/other/privacy.html).

## Records Management Standard Notice
This repository is not a source of government records, but is a copy to increase
collaboration and collaborative potential. All government records will be
published through the [CDC web site](http://www.cdc.gov).

## Additional Standard Notices
Please refer to [CDC's Template Repository](https://github.com/CDCgov/template)
for more information about [contributing to this repository](https://github.com/CDCgov/template/blob/master/CONTRIBUTING.md),
[public domain notices and disclaimers](https://github.com/CDCgov/template/blob/master/DISCLAIMER.md),
and [code of conduct](https://github.com/CDCgov/template/blob/master/code-of-conduct.md).
