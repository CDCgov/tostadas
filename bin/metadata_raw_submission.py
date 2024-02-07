#!/usr/bin/env python3

# Very simple py script to extract sample names and corresponding file paths from metadata file
import argparse
import pandas as pd
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--meta_path", help='path to metadata file')
    return parser

def main():
    args = get_args().parse_args()
    # Read metadata file
    df = pd.read_excel(args.meta_path, header=[1])

    # Extract sample names and file paths
    sample_names = df['sample_name'].tolist()

    # Define columns for file paths
    illumina_columns = ['illumina_sra_file_path_1', 'illumina_sra_file_path_2']
    nanopore_columns = ['nanopore_sra_file_path_1']

    # Initialize list for file paths
    file_paths_list = []

    # Iterate over rows in metadata dataframe
    for _, row in df.iterrows():
        file_paths = []
        for col in illumina_columns:
            if pd.notna(row[col]):
                file_paths.append(row[col])
        if pd.notna(row[nanopore_columns[0]]):
            file_paths.append(row[nanopore_columns[0]])
        file_paths_list.append(file_paths)
    return(sample_names, file_paths_list)

if __name__ == "__main__":
    main()