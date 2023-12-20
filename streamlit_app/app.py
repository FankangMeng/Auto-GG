import streamlit as st
import pandas as pd
import json
import csv
import io
import os
import time



# Script's functions
def process_plate_map_df(df):
    plate_map = []
    for index, row in df.iterrows():
        # Assuming the first column contains the key data
        if pd.notna(row[0]):
            plate_map.append(row.tolist())
    return plate_map


def generate_plate_maps(df1, df2):
    plate_maps = {}

    # Process each DataFrame using the new function
    plate_map1 = process_plate_map_df(df1)
    plate_name1 = "PlateMap1"  # Replace with a suitable name or a derived name
    plate_maps[plate_name1] = plate_map1

    plate_map2 = process_plate_map_df(df2)
    plate_name2 = "PlateMap2"  # Replace with a suitable name or a derived name
    plate_maps[plate_name2] = plate_map2

    return plate_maps


def generate_combinations(df):
    combinations_to_make = []
    for index, row in df.iterrows():
        # Assuming the first column ('name') and subsequent columns ('parts') are relevant
        if pd.notna(row[0]):  # Check if the 'name' field is not NaN
            combination = {
                "name": row[0],
                "parts": [x for x in row[1:] if pd.notna(x)]  # Include non-NaN 'parts'
            }
            combinations_to_make.append(combination)
    return combinations_to_make


def check_number_of_combinations(combinations_to_make):
    number_of_combinations = len(combinations_to_make)
    if number_of_combinations > 96:
        raise ValueError(
            'Too many combinations ({0}) requested. Max for single combinations is 96.'.format(
                number_of_combinations))


# Functions for creating output files
def generate_and_save_output_plate_maps(combinations_to_make):
    # Split combinations_to_make into 8x6 plate maps.
    output_plate_map_flipped = []
    for i, combo in enumerate(combinations_to_make):
        name = combo["name"]
        if i % 2 == 0:
            # new column
            output_plate_map_flipped.append([name])
        else:
            output_plate_map_flipped[-1].append(name)

    # Correct row/column flip.
    output_plate_map = []
    for i, row in enumerate(output_plate_map_flipped):
        for j, element in enumerate(row):
            if j >= len(output_plate_map):
                output_plate_map.append([element])
            else:
                output_plate_map[j].append(element)

    # Generate CSV content in memory
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    for row in output_plate_map:
        writer.writerow(row)

    # Return CSV content as a string
    return csv_buffer.getvalue()


def create_protocol(dna_plate_map_dict, combinations_to_make, protocol_template_file):
    # Read the contents of the uploaded template file
    template_string = protocol_template_file.getvalue().decode("utf-8")

    # Create the protocol string by concatenating new data at the beginning
    protocol_string = 'dna_plate_map_dict = ' + json.dumps(dna_plate_map_dict) + '\n\n'
    protocol_string += 'combinations_to_make = ' + json.dumps(combinations_to_make) + '\n\n'
    protocol_string += template_string  # Append the existing content of the template

    return protocol_string

def reset_state():
    st.session_state.process_data = False

# from your_script import generate_plate_maps, generate_combinations,
# check_number_of_combinations, generate_and_save_output_plate_maps, create_protocol
# Clear the cache each time the app is re-run

def main():
    st.image("Slowpoke.jpg", width=500)
    st.title("Opentrons protocol generator for MoClo assembly and transformation")

    if 'process_data' not in st.session_state:
        st.session_state.process_data = False

    # Sidebar for user inputs
    with st.sidebar:
        st.header("Input Files")
        dna_fixed_plate_map_file = st.file_uploader("Upload Fixed DNA Plate Map", type=["csv"])
        dna_customised_plate_map_file = st.file_uploader("Upload Customised DNA Plate Map", type=["csv"])
        combinations_file = st.file_uploader("Upload Combinations File", type=["csv"])
        protocol_template_file = st.file_uploader("Upload Protocol Template File", type=["py"])

    # Main page for processing and output
    if st.button("Process Data"):
        st.session_state.process_data = dna_fixed_plate_map_file and dna_customised_plate_map_file and combinations_file
    if st.session_state.process_data:
        try:
            try:
            # Process files
                fixed_plate_map_df = pd.read_csv(dna_fixed_plate_map_file, header=None)
                customised_plate_map_df = pd.read_csv(dna_customised_plate_map_file, header=None)
                combinations_df = pd.read_csv(combinations_file, header=None)
            except Exception as e:
                st.error(f"An error occurred at process files: {e}")
            try:
                # Load in CSV files as a dict containing lists of lists.
                dna_plate_map_dict = generate_plate_maps(fixed_plate_map_df, customised_plate_map_df)
            except Exception as e:
                st.error(f"An error occurred at dna_plate_map_dicts: {e}")

            combinations_to_make = generate_combinations(combinations_df)
            check_number_of_combinations(combinations_to_make)


            try:
            # Generate and save output plate maps.
                output_plate_maps = generate_and_save_output_plate_maps(combinations_to_make)
            except Exception as e:
                st.error(f"An error occurred at save plate maps: {e}")

            try:
            # Create a protocol file.
                protocol_string = create_protocol(dna_plate_map_dict, combinations_to_make, protocol_template_file)
            except Exception as e:
                st.error(f"An error occurred at creating protocol: {e}")

            # Displaying Results - adapt as necessary
            st.success("Data processed successfully!")
            #st.subheader("Output Plate Maps")
            #st.write(output_plate_maps)
            #st.subheader("Protocol")
            #st.write(protocol_string)

            # Option to display or download the output
            st.download_button(label="Download Plate Map CSV",
                               data=output_plate_maps,
                               file_name="plate_map.csv",
                               mime="text/csv")

            st.download_button(label="Download Protocol",
                               data=protocol_string,
                               file_name="protocol.py")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    #else:
        #st.error("Please upload all required files.")


if __name__ == "__main__":
    main()
