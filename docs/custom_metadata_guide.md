# Custom Metadata Fields Guide

## Summary:
TOSTADAS consists of a validation portion of the pipeline (1/3 major segments) to ensure that metadata is aligned with sample submission constraints for NCBI databases. By default, the pipeline performs general checks and makes appropriate corrections to metadata, but the option exists to extend this core-functionality further for the user. 

TOSTADAS will accept a .JSON file consisting of 



## Get Started:

HOW TO SETUP .JSON FILE (WHAT EACH REPRESENTS):


LINK TO EXAMPLE .JSON FILE (RELATIVE)

## Assumptions / Limitations:
CONSTRAINTS/ASSUMPTIONS FOR CUSTOM FIELDS:

- Test when custom field name is empty (should not proceed) within clean_lists

- Test that proper error message is added when this is the case

- Test that if "type" or "samples" is empty then wont clean it in clean_lists

- Test that general strip() is working as expected within clean_lists

- Test that 'all' is properly captured for sample names and that erorr is provided if ['all', <sample_name>, etc.] is provdied in clean_sample_names

- Test that if a sample mentioned in "samples" is not in metadata list, handled appropriately in clean_sample_names

- Test that if ALL samples mentioned in "samples" are not in metadata list, then it is handled appropriately in clean_sample_names (skips)

- Test that all samples are checked if "samples" is empty

- Test that the "type" is changed to present if empty for a custom field

- Test that you proceed with "all" if no values in sample list for custom field are a string

- Test that you remove only non-strings from sample list

- The only time custom checks do not proceed is (1) custom field name is empty OR (2) all string names for samples are not in metadata sheet