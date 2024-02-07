/*
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
                    GET SAMPLES AND PATHS FROM METADATA FOR RAW SUBMISSION
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
*/
process METADATA_RAW_SUBMISSION {

    label 'main'

    if ( params.run_conda == true ) {
        try {
            conda params.env_yml
        } catch (Exception e) {
            System.err.println("WARNING: Unable to use conda env from $params.env_yml")
        }
    }

    publishDir "$params.output_dir", mode: 'copy', overwrite: params.overwrite_output

    // Define input parameters
    input:
    val signal
    path meta_path
    
    // Script section
    script:
    """
    # Very simple py script to extract sample names and corresponding file paths from metadata file

    import pandas as pd
    
    # Read metadata file
    df = pd.read_excel('${meta_path}', header=[1])
    
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
    """

    // Define output channels
    output:
    val sample_names, emit: sample_names
    val sample_file_paths, emit: sample_paths
}