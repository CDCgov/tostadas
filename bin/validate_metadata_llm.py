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

# Rules for data validation
rules = """
Reformat the input data to match NCBI Biosample, BioProject, or Genbank rules and expectations.
"""

if __name__ == "__main__":
    main()