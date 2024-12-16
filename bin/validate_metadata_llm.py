import pandas as pd
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv
from langchain.prompts import PromptTemplate
from pandasai import SmartDataframe
from io import StringIO
import openpyxl
import json

def get_args():
	""" Function to get the user defined parameters for bakta post cleanup
	"""
	parser = argparse.ArgumentParser(description="Parameters for metadata validation")
	parser.add_argument("--llm_key", type=str, default='bakta_outputs', help="Name of final bakta output directory")
	parser.add_argument("--meta_path", type=str, help="Path to the input metadata file")
	parser.add_argument("--out_dir", type=str, help="Path to the output directory")
	return parser

#loading in the OpenAi API Key
OPENAI_API_KEY = args.llm_key
os.environ["POC"] = OPENAI_API_KEY

#Relevant prompts - depreciate prompt 1 & 2
prompt = """
You are a helpful data validation assistant that will be assisting the user with checking their data against a set of rules. Your objective is to go through each of the columns in the dataframe and check the values that have been enetered against
    a set of predefined rules. For each column specified in these rules, please check each value against what is expected and update any value that does not comply to the corrected value labeled in the rules. The output should be a Dataframe.
    The input should have the same titles to the columns and the output should maintain the format of the input, only with updated values. In each rule I will give you the column title followed by a ':' and then I will provide the rule
    and finally the expected output format (string, int, date, etc.). The rules can be found below:

    1. Collection Date: This column contains dates that should be formatted as YYYY-MM-DD. For example if a value is listed as '08-24-2024', please change it to '2024-08-24'. The expected format here would be a date format.
"""

prompt2 = """
    You are a helpful data validation assitant that will be checking a dataframe for incorrect entries and formatting errors. Please respond only with the updated dataframe as an output. The column names appear on row 0 of the dataframe.
    Please check each column against the rules provided and update and row that does not meet the requirements. All columns should be changed to NCBI-accepted format. The rules can be found below:

    The following rules are specific to columns in the dataframe. For each rule I will write out a column name and then ':' followed by the rule for the data in that column. You will recognize the start of a new rule with a column name and at the end of the rule I will mark with 
    <end>, indicating the next rule is about to start.
    1. Collection Date: This column contains dates that must be formatted as MMDDYYYY. For example if you see the date 2022/6, it should be switched to 06/2022. Only include data that is already present do not assume the day, month, or year. <end>
    2. Host: This column contains text data. The values in this column represent who is the host of a virus and must be formatted as a latin genus name. For example if someone has put 'human' that should be changed to 'Homo sapiens' <end>

    Please return the corrected data as a JSON object with the same structure as the input.
"""

prompt3 = """
You are a data cleaning assistant. You are given data from an Excel file and must reformat or correct it according to the rules provided below.

### Rules:
{rules}

### Input Data:
{input_data}

Please return the corrected data as a JSON object with the same structure as the input.
"""

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