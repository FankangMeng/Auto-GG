import streamlit as st
import pandas as pd
import json
import csv
import io
import os
import time

# Functions for processing data

def process_plate_map_df(df):
    """
    Converts a DataFrame into a list of lists representing plate maps.
    Ignores rows where the first column contains NaN values.
    """
    plate_map = []
    for index, row in df.iterrows():
        # Includes rows where the first column is not NaN
        if pd.notna(row[0]):
            plate_map.append(row.tolist())
    return plate_map

def generate_plate_maps(df1, df2):
    """
    Generates plate maps from two input DataFrames.

    Args:
        df1 (DataFrame): Fixed plate map.
        df2 (DataFrame): Customized plate map.

    Returns:
        dict: A dictionary containing plate maps with corresponding names.
    """
    plate_maps = {}

    # Process the first DataFrame
    plate_map1 = process_plate_map_df(df1)
    plate_name1 = "PlateMap1"  # Name for the first plate map
    plate_maps[plate_name1] = plate_map1

    # Process the second DataFrame
    plate_map2 = process_plate_map_df(df2)
    plate_name2 = "PlateMap2"  # Name for the second plate map
    plate_maps[plate_name2] = plate_map2

    return plate_maps

def generate_combinations(df):
    """
    Creates a list of combinations to assemble based on a DataFrame.

    Args:
        df (DataFrame): DataFrame containing combination details.

    Returns:
        list: A list of dictionaries with combination names and parts.
    """
    combinations_to_make = []
    for index, row in df.iterrows():
        if pd.notna(row[0]):  # Include rows with valid 'name' entries
            combination = {
                "name": row[0],
                "parts": [x for x in row[1:] if pd.notna(x)]  # Add non-NaN parts
            }
            combinations_to_make.append(combination)
    return combinations_to_make

def check_number_of_combinations(combinations_to_make):
    """
    Ensures the number of combinations does not exceed 96.

    Args:
        combinations_to_make (list): List of combinations.

    Raises:
        ValueError: If the number of combinations exceeds 96.
    """
    number_of_combinations = len(combinations_to_make)
    if number_of_combinations > 96:
        raise ValueError(
            f'Too many combinations ({number_of_combinations}) requested. Max for single combinations is 96.'
        )

def generate_and_save_output_plate_maps(combinations_to_make):
    """
    Creates CSV output for plate maps based on combinations.

    Args:
        combinations_to_make (list): List of combinations.

    Returns:
        str: CSV content as a string.
    """
    output_plate_map_flipped = []
    for i, combo in enumerate(combinations_to_make):
        name = combo["name"]
        if i % 2 == 0:
            output_plate_map_flipped.append([name])
        else:
            output_plate_map_flipped[-1].append(name)

    output_plate_map = []
    for i, row in enumerate(output_plate_map_flipped):
        for j, element in enumerate(row):
            if j >= len(output_plate_map):
                output_plate_map.append([element])
            else:
                output_plate_map[j].append(element)

    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    for row in output_plate_map:
        writer.writerow(row)

    return csv_buffer.getvalue()

def create_protocol(dna_plate_map_dict, combinations_to_make, protocol_template_file):
    """
    Generates a protocol file based on inputs and a template.

    Args:
        dna_plate_map_dict (dict): Plate map dictionary.
        combinations_to_make (list): List of combinations.
        protocol_template_file (UploadedFile): Template file uploaded by the user.

    Returns:
        str: The complete protocol as a string.
    """
    # Read the contents of the uploaded template file
    template_string = protocol_template_file.getvalue().decode("utf-8")

    # Append the plate map and combination data at the start of the protocol
    protocol_string = 'dna_plate_map_dict = ' + json.dumps(dna_plate_map_dict) + '\n\n'
    protocol_string += 'combinations_to_make = ' + json.dumps(combinations_to_make) + '\n\n'
    protocol_string += template_string  # Append the existing template content

    return protocol_string

def create_download_button(file_path, label, file_name):
    """
    Creates a download button in the Streamlit app.

    Args:
        file_path (str): Path to the file to be downloaded.
        label (str): Label for the download button.
        file_name (str): Name of the file to download.
    """
    with open(file_path, 'rb') as file:
        st.download_button(
            label=label,
            data=file,
            file_name=file_name,
            mime="text/plain"
        )

def reset_state():
    """
    Resets the application state.
    """
    st.session_state.process_data = False

def main():
    """
    Main function defining the Streamlit app.
    """
    st.header("Auto-GG: Opentrons protocol generator for MoClo assembly, transformation and colony PCR")

    if 'process_data' not in st.session_state:
        st.session_state.process_data = False

    # Sidebar for user interface
    with st.sidebar:
        st.image("Slowpoke.png", use_column_width="always")
        st.markdown("Authored by Fankang Meng & Koray Malci from Imperial College London.")

        # Download section for template files
        st.subheader('Download template files')
        files_to_download = [
            ('template_files/fixed_input_dna_map.csv', "moclo_plate_template", "fixed_input_dna_map.csv"),
            ('template_files/customised_input_dna_map.csv', "customised_plate_template",
             "customised_input_dna_map_template.csv"),
            ('template_files/combination-to-make.csv', "combinations_template",
             "combination-to-make.csv"),
            ('template_files/template_BsmbI_moclo_protocol_EP_tubes.py', "opentrons_protocol_template",
             "template_BsmbI_moclo_protocol_EP_tubes.py"),
        ]
        for file_path, label, file_name in files_to_download:
            create_download_button(file_path, label, file_name)

    # File upload section
    st.header("Input Files")
    col1, col2 = st.columns(2)
    moclo_plate_map_file = col1.file_uploader("Upload Moclo parts map", type=["csv"])
    customised_plate_map_file = col2.file_uploader("Upload customised parts map", type=["csv"])

    col3, col4 = st.columns(2)
    combinations_file = col3.file_uploader("Upload assembly-info file", type=["csv"])
    protocol_template_file = col4.file_uploader("Upload protocol template file", type=["py"])

    # Protocol generation section
    st.header("Protocol generation")
    if st.button("Process Data"):
        st.session_state.process_data = all([
            moclo_plate_map_file, customised_plate_map_file, combinations_file, protocol_template_file
        ])

    if st.session_state.process_data:
        try:
            # Read uploaded files into DataFrames
            fixed_plate_map_df = pd.read_csv(moclo_plate_map_file, header=None)
            customised_plate_map_df = pd.read_csv(customised_plate_map_file, header=None)
            combinations_df = pd.read_csv(combinations_file, header=None)

            # Process input data
            dna_plate_map_dict = generate_plate_maps(fixed_plate_map_df, customised_plate_map_df)
            combinations_to_make = generate_combinations(combinations_df)
            check_number_of_combinations(combinations_to_make)

            # Generate outputs
            output_plate_maps = generate_and_save_output_plate_maps(combinations_to_make)
            protocol_string = create_protocol(dna_plate_map_dict, combinations_to_make, protocol_template_file)

            # Display success message and download buttons
            st.success("Data processed successfully!")
            st.download_button("Download Plate Map CSV", data=output_plate_maps, file_name="plate_map.csv", mime="text/csv")
            st.download_button("Download Protocol", data=protocol_string, file_name="protocol.py")

        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
