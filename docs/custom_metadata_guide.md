# Custom Metadata Fields Guide

## Table of Contents
- [Introduction](#introduction)
    - [Summary](#summary)
    - [Input File (General)](#input-file-general)
    - [Input File (Specifics)](#input-file-specifics)
- [How To Run](#how-to-run)
- [Outputs](#outputs)
- [Capabilities / Limitations](#capabilities--limitations)

## Introduction:

### Summary:
TOSTADAS consists of a validation portion of the pipeline (1/3 major segments) to ensure that metadata is aligned with sample submission constraints for NCBI databases. By default, the pipeline performs general checks and makes appropriate corrections to metadata, but the option exists to extend this core-functionality further for the user. 

### Input File (General):

The pipeline will accept a .JSON file with the following structure:
* __Key__ = Custom field name
* __Value__ = Array consisting of sub-keys/values 

Each array contains multiple different key/value pairs, where the user can specify different checks and changes to take place for each custom field. 

Here is an example of the structure:
```
{
    "Name of Custom Field 1": {
        "type": "",
        "samples": [],
        "replace_empty_with": "",
        "new_field_name": ""
    },

    "Name of Custom Field 2": {
        "type": "",
        "samples": [],
        "replace_empty_with": "",
        "new_field_name": ""
    }
}
```

### Input File (Specifics):

Each key/value within a custom metadata field array will correspond to the different ways the user can perform checks and make changes for each custom metadata field. 

There are currently four properties:
* __Data Type__ ("type"):
    * Specifies the correct data type for the field
    * Must be one of the following: 
        * Integer
        * String
        * Boolean
        * Float
    * The pipeline will check the existing data type, and if it does not match the one specified in the JSON file, then it will attempt to cast it over

* __Samples__ ("samples"):
    * Specifies the list of samples the user wants to apply these checks/transformations to
    * Must be one of the following: 
        * "All" (it will run these checks/transformations for all samples within the batch)
        * Specific names of samples for application 
    * Will accept a single string or a list of strings for either option. Here are few acceptable variations:

        ```
        (1) "samples": "All"
        (2) "samples": ["All"]
        (3) "samples": ["FL0000", "FL0001", "FL0002"]
        (4) "samples": "FL0000"
        ```

* __Replace Empty Values__ ("replace_empty_with"):
    * Specifies the desired value the user would like to replace an empty value with
    * The actual value can be any of the following data types: string, number, float, boolean, or empty 

* __New Field Name__ ("new_field_name"):
    * Specifies the string to replace the existing field name with
    * Please note that the old field name will no longer exist in the final output 


A completed example of a JSON file can be found here: [JSON Example](../assets/custom_meta_fields/example_custom_fields.json). This is the same JSON used for a test profile run.

## How To Run:

There are two Nextflow parameters used:
* __validate_custom_fields__ = Toggles custom metadata field checks on/off. Must be set to __True__ if custom field checks are wanted.
* __custom_fields_file__ = Path to your JSON file containing custom field names and check/transformation properties for each.

** NOTE: The default value for validate_custom_fields is __False__ in the test profile, therefore this must be changed to __True__ if doing a test run. 

Once the JSON file for custom fields is set up, and the parameters above have been properly populated, the next step is to initiate the typical nextflow run for the pipeline (information can be found in the README.md here: [Quick Start](../README.md#quick-start)) 

## Outputs:

After running metadata validation, with the appropriate Nextflow parameters and your JSON file, there is a .txt log file that is generated as an output named ___custom_fields_error.txt__.

This .txt log file contains information about two aspects generally: 
* (1) The actual contents within the provided JSON file
    * It will provide information for each custom metadata field in the JSON
    * The following is an example log output for this: 
    ```
    test_field_1:
	    Found value(s) in subfield samples for the custom field named test_field_1 that are not all strings... will remove these
	    You specified some sample names that are not present within metadata file: ['FL00234']. Processed all others.

    test_field_2:
	    Found 'all' specified within samples list, AND other values as well. Proceeded with checking all samples in this case.

    After preliminary checks, valid information for custom field names have been passed in. Will now check these accordingly
    ```

* (2) For each sample, the outcome of performing a custom field check on it (if mentioned in any under "samples")
    * The following is an example of how this information appears and its content:
    ```
    FL0004:
	    test_field_2 not populated. 
	    Replaced field name (test_field_2) with new_field_name2

    IL0005:
	    test_field_1 value was not string. Converting to string
	    Successfully converted test_field_1 to a string
	    Replaced field name (test_field_1) with new_field_name

    NY0006:
	    All custom field checks passed
    ```

The custom_fields_error.txt file will be outputted under the __errors__ directory, which is nested within the validation outputs directory.

## Capabilities / Limitations:

- The custom field name must be populated, it cannot be an empty string within the JSON file. If it is empty, then it will be skipped.

- Different spelling/shortening/formatting/spacing variations for data types can be captured (i.e. boolean = Boolean = bool = bOoL). It will not capture spaces (i.e. b ool) or words that deviate too far (i.e. trueorfalsething != bool).

- If the string "All" is detected within a list, then all samples will be checked for that custom metadata field no matter what (i.e. "samples": ['all', <sample_name>, etc.]).

- If a sample name specified is not within the metadata sheet, then it will be skipped and captured within the log file.

- If the "samples" key is empty for a custom metadata field, or none of the provided values are strings (if some strings are present, then it will proceed with only those), then it will check __ALL__ samples within the batch by default.

- If the "type" key is empty for a custom metadata field, then it will only check if the field is empty or not.

** NOTE: The only time custom checks do not proceed is when (1) custom field name is empty OR (2) all string names for samples are not in metadata sheet.