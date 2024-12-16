<<<<<<< HEAD
#!/usr/bin/env python3
import argparse
import json
import os
from io import StringIO

import pandas as pd
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage


def get_args():
    """Function to get the user-defined parameters for metadata validation."""
    parser = argparse.ArgumentParser(description="Parameters for metadata validation")
    parser.add_argument("--api_key", type=str, required=True, help="OpenAI API Key")
    parser.add_argument("--meta_path", type=str, required=True, help="Path to the input metadata file")
    parser.add_argument("--out_dir", type=str, default=".", help="Path to the output directory")
    return parser


def load_file(file_path):
    """
    Function to load the input file.

    If the uploaded file is a .xlsx or .xls, it will be read using pandas.
    Assumes that the Excel file has two header rows:
    - The first header row is ignored.
    - The second header row is used as column names.
    """
    file_type = os.path.splitext(file_path)[-1].lower()
    if file_type == ".csv":
        # For CSV files, we assume a single header row
        df = pd.read_csv(file_path, keep_default_na=True)
        return df
    elif file_type in [".xlsx", ".xls"]:
        # For Excel files, skip the first header row and use the second header row
        df = pd.read_excel(file_path, keep_default_na=True, header=1)
        return df
    else:
        raise ValueError(
            "Unsupported format. Please make sure that the uploaded file is one of the following formats: .xlsx, .xls, or .csv"
        )


def create_json_string(df):
    """Convert the DataFrame to a JSON string."""
    # Convert datetime columns to strings to make them JSON serializable
    datetime_columns = df.select_dtypes(include=['datetime64[ns]', 'datetimetz']).columns
    if datetime_columns.any():
        df[datetime_columns] = df[datetime_columns].astype(str)

    input_data = df.to_dict(orient="records")
    input_data_str = json.dumps(input_data)
    return input_data_str

def create_llm_agent(api_key):
    """Create an instance of the ChatOpenAI LLM."""
    llm = ChatOpenAI(temperature=0.0, openai_api_key=api_key)
    return llm


def run_data_validation(prompt, agent, input_data):
    """
    Use the LLM to validate and correct the data based on the provided rules.

    Returns the response content as a string.
    """
    formatted_prompt = prompt.format(rules=rules, input_data=input_data)
    messages = [HumanMessage(content=formatted_prompt)]
    response = agent.invoke(messages)
    response_content = response.content
    return response_content


def format_llm_response(response):
    """
    Parse the LLM response, which should be JSON-formatted data, into a DataFrame.
    """
    formatted_response = json.loads(response)
    new_df = pd.DataFrame(formatted_response)
    return new_df


def save_corrected_file(updated_df, out_dir):
    """
    Save the updated DataFrame to an Excel file in the specified output directory.
    """
    output_file = os.path.join(out_dir, "validated_metadata.xlsx")
    updated_df.to_excel(output_file, index=False)
    print(f"Changes saved to {output_file}!")


def create_per_sample_tsv(updated_df, out_dir):
    """
    Create and save a TSV file for each sample (row) in the DataFrame.
    """
    # Ensure the output directory exists
    per_sample_dir = os.path.join(out_dir, "tsv_per_sample")
    os.makedirs(per_sample_dir, exist_ok=True)

    # Possible sample name columns
    possible_sample_name_columns = ['sample_name', 'Sample Name']

    # Iterate over each row
    for index, row in updated_df.iterrows():
        # Create a DataFrame with only this row and the correct headers
        sample_df = pd.DataFrame([row], columns=updated_df.columns)
        # Get a sample identifier for the file name
        sample_id = None
        for col_name in possible_sample_name_columns:
            if col_name in updated_df.columns:
                sample_id = str(row[col_name]).strip()
                if sample_id and sample_id.lower() != 'nan':
                    # Replace any illegal filename characters
                    sample_id = sample_id.replace('/', '_').replace('\\', '_')
                    break  # Exit the loop once we've found a valid sample name
        # If no valid sample name is found, default to 'sample_{index}'
        if not sample_id or sample_id.lower() == 'nan':
            sample_id = f'sample_{index}'
        # Define the output file path
        output_file = os.path.join(per_sample_dir, f"{sample_id}.tsv")
        # Save the DataFrame to TSV with proper formatting
        sample_df.to_csv(output_file, index=False, sep='\t')
        print(f"Saved {output_file}")


def main():
    parser = get_args()
    args = parser.parse_args()

    # Set the OpenAI API Key
    OPENAI_API_KEY = args.api_key
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

    # Load the input metadata file
    df = load_file(args.meta_path)

    # Convert the DataFrame to a JSON string for the prompt
    input_data = create_json_string(df)

    # Create the LLM agent
    agent = create_llm_agent(OPENAI_API_KEY)

    # Run data validation
    response = run_data_validation(prompt=prompt3, agent=agent, input_data=input_data)

    # Format the LLM response into a DataFrame
    updated_df = format_llm_response(response)

    # Save the corrected DataFrame to an Excel file
    save_corrected_file(updated_df, args.out_dir)

    # Create per-sample TSV files
    create_per_sample_tsv(updated_df, args.out_dir)

    print("Data validation successful!")


# Prompt for the LLM
prompt3 = """
You are a data cleaning assistant. You are given data from an Excel file and must reformat or correct it according to the rules provided below. If you reformat data, report on what changes were made.

### Rules:
{rules}

### Input Data:
{input_data}

Please return the corrected data as a JSON object with the same structure as the input.
"""

<<<<<<< HEAD
# Rules for data validation
rules = """
Reformat the input data to match NCBI Biosample, BioProject, or Genbank rules and expectations.
"""

if __name__ == "__main__":
    main()
=======
rules = """
1. 'collection_date' is a column containing dates and should be formatted as <b>YYYY-MM-DD<b>. For example if you see the date 06/2022 it should be formatted as 2022/06. Only include data that is already present and do not assume the day, month, or year.
2. 'host' is a column that contains the organism that hosts a virus and should using binomial nomenclature (or scientific name) rather than the common english name. If a response is not in the correct format please identify can change that. For example if you see 'human' as a value that should be corrected to 'Homo sapien.'
3. 'authors' column contains names of individuals that contributed to a project. It is a list that should be formatted as <b>Last, First Middle, suffix <b> seperated by a semicolon ";". For example: "Baker, Howard Henry, Jr.; Powell, Earl Alexander, II.;" 
4. 'lat_lon' column is looking for lattitude and longitude formatted as "d[d.dddd] N|S d[dd.dddd] W|E", eg, 38.98 N 77.11 W'. Please only correct values for formatting and do not alter any values that are not lattitude or longitude. Values may be left blank or have a filler value such as 'N/A'
5. 'file_location' column there are two options that the user may enter: Either 'local' or 'cloud'. You may see mispellings or different capitalization in these but please correct that to the two previously mentioned options. eg 'Local' should be 'local'
6. 'sra-file_name' column contains one or more unique file names. If there are multiple files, concatenate them with a comma (","), eg. "sample1_R1.fastq.gz, sample1_R2.fastq.gz"
7. 'illumina_library_layout' column should only have two options: 'single' or 'paired.' Please check for any spelling mistakes and return any synonyms to the option that is most appropriate.
8. 'publication_title' column may contain unique text. If it is left blank it should then use the value found in 'title' column in the same row.
9. 'publication_status' column should only have three options: 'unpublished' or 'in-press' or 'published.' Please check for any spelling mistakes and return any synonyms to the option that is most appropriate.
"""

def load_file(file):
    """Function to load in the file. If the uploaded file is a .xlsx it will be converted into a .csv format for easier processing in the LLM"""
    file_type = os.path.splitext(file)[-1].lower()
    if file_type == ".csv":
        df = pd.read_csv(file, keep_default_na=True)
        return df
    elif file_type in [".xlsx", ".xls"]:
        df1 = pd.read_excel(file, keep_default_na=True)
        csv_io = StringIO()
        df1.to_csv(csv_io, index=False)
        return df1
    else:
        raise ValueError("Unsupported format, please make sure that the uploaded file is one of the following formats: .xlsx, .xls, or .csv")
    
def create_JSON_file(df):
    input_data = df.to_dict(orient="records")
    return input_data

def create_LLM_agent(): #removed db parameter
    """Create instance of the LLM that will check the table"""
    llm = ChatOpenAI(temperature=0.5, api_key=OPENAI_API_KEY)
    #agent = SmartDataframe(df=db, config={'llm':llm})
    return llm

#MARSHALL - make sure to double check that the formats you have listed in the rules is correct
def run_data_validation(prompt, agent, df):
    """Feeding in both the agent and table to and retrieving the output of the LLM in the form of a pandas df"""
    formatted_prompt = prompt.format(rules=rules, input_data=df)
    response = agent(formatted_prompt)
    response_content = response.content
    return response_content

def format_llm_response(response):
    """Taking the response from the llm and extracting the content as json in order to use to overwrite the excel file."""
    formatted_response = json.loads(response) #issue here loading the 'AIMessage' object
    new_df = pd.DataFrame(formatted_response)
    return new_df

def new_file(updated_df):
    """Taking the updated data that was run through the LLM and creating a new excel workbook."""
    corrected_df = pd.DataFrame(updated_df)
    output_file = "new_Copy of mpxv_user_provided_annotations_metadata.xlsx"
    corrected_df.to_excel(output_file, index=False)
    print(f"Changed saved to {output_file}!")

def main():
    df = load_file(args.meta_file)
    json_df = create_JSON_file(df)
    agent = create_LLM_agent()
    response = run_data_validation(prompt=prompt3, agent = agent, df=json_df)
    updated_df = format_llm_response(response)
    new_file(updated_df)
    print("Data Validation Successful!")

if __name__ == "__main__":
    main()


"""
In this section are some notes for how this file should be updated to accomodate the front-end development or further improvements beyond the intial POC

    1. the load_file function call on line 38 currently is set to the static filepath where there excel file sits within the project rather than pointing to where the program allows the user to upload a file themselves
    2. As prompt grows to include rules down below RAG might become necessary to build out the knowledge base, if some of the referenced databases should be brought in
    3. Below rules can most likely be ignored - will use rules developed by Sahar to implement RAG into python script prompt

    Additional column rules to be added to prompt:
    1. Certain field we can bring in extra formatting (ie organism database: <a href="https://www.ncbi.nlm.nih.gov/taxonomy" target="_blank">NCBI Taxonomy database</a>)
    2. bs-geoloc_name name from <a href="http://www.insdc.org/documents/country-qualifier-vocabulary" target="_blank">this list</a>
    3. Host_disease: <a href="http://bioportal.bioontology.org/ontologies/1009" target="_blank">Human Disease Ontology</a> or <a href="http://www.ncbi.nlm.nih.gov/mesh" target="_blank">MeSH</a>
    4. sra-library_name: 'Short unique identifier for sequencing library. <b>Each name must be unique!</b>'
    5. sra-instrument_model: 'Type of instrument model used for sequencing. See a list of options <a href="sra_options.html#instrument_model" target="_blank">here</a>.'
    6. sra-library_strategy: 'The sequencing technique intended for the library. See a list of options <a href="sra_options.html#library_strategy" target="_blank">here</a>.'
    7. sra-library_source: 'The type of source material that is being sequenced. See a list of options <a href="sra_options.html#library_source" target="_blank">here</a>.'
    8. sra-library_selection: 'The method used to select and/or enrich the material being sequenced. See a list of options <a href="sra_options.html#library_selection" target="_blank">here</a>.'
    9. src-country: 'Geographical origin of the sample; use the appropriate name from <a href="http://www.insdc.org/documents/country-qualifier-vocabulary" target="_blank">this list</a>. Use a colon to separate the country or ocean from more detailed information about the location, eg "Canada: Vancouver" or "Germany: halfway down Zugspitze, Alps". Entering multiple localities in one attribute is not allowed.'
    10. src-serotype: 'For Influenza A only; must be in format HxNx, Hx, Nx or mixed; where x is a numeral'
    11. cmt-StructuredCommentPrefix: 'Structured comment keyword. For FLU use "FluData", HIV use "HIV-DataBaseData", and for COV and other organisms use "Assembly-Data".'
    12. cmt-StructuredCommentSuffix: 'Structured comment keyword. For FLU use "FluData", HIV use "HIV-DataBaseData", and for COV and other organisms use "Assembly-Data".'
    13. gs-subm_lab: 'Full name of laboratory submitting this record to GISAID. See a list of options <a href="gisaid_options.html#subm_lab" target="_blank">here</a>.'
"""