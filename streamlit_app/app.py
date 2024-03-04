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


def create_download_button(file_path, label, file_name):
    with open(file_path, 'rb') as file:
        st.download_button(
            label=label,
            data=file,
            file_name=file_name,
            mime="text/plain"
        )


def reset_state():
    st.session_state.process_data = False


# from your_script import generate_plate_maps, generate_combinations,
# check_number_of_combinations, generate_and_save_output_plate_maps, create_protocol
# Clear the cache each time the app is re-run


def main():
    #image1, image2, image3 = st.columns((2, 1.5, 2))
    #with image2:
        #st.image("Slowpoke.png", use_column_width="always")
    #st.title("Slowpoke")

    st.header("Slowpoke: Opentrons protocol generator for MoClo assembly and transformation", divider='rainbow')

    if 'process_data' not in st.session_state:
        st.session_state.process_data = False

    # Sidebar for user inputs
    with st.sidebar:
        image1, image2, image3 = st.columns((1, 3, 1))
        with image2:
            st.image("Slowpoke.png", use_column_width="always")
            # st.title("Slowpoke")
        st.markdown('''
            :red[Slowpoke] :orange[is] :green[easy] :blue[to] :violet[use]
            :gray[by] :rainbow[everyone].''')
        st.markdown("Authored by Fankang Meng & Koray Malci from Imperial College London,"
                    "it's designed for Opentrons protocol generation "
                    "for MoClo YTK/STK/KTK Golden Gate assembly, transformation and plating. ")
        link1, link2 = st.columns((1,1))
        with link1:
            st.link_button(":blue[Github]", "https://github.com/FankangMeng/Slowpoke/tree/main")
        with link2:
            st.link_button(":blue[Ellis lab]", "https://www.tomellislab.com/")

        st.subheader('Download template files', divider='rainbow')

        files_to_download = [
            ('template_files/fixed_input_dna_map.csv', "moclo_plate_template", "fixed_input_dna_map.csv"),
            ('template_files/customised_input_dna_map.csv', "customised_plate_template",
             "customised_input_dna_map_template.csv"),
            ('template_files/combination-to-make.csv', "combinations_template",
             "combination-to-make.csv"),
            ('template_files/template_BsmbI_moclo_protocol_EP_tubes.py', "opentrons_protocol_template",
             "template_BsmbI_moclo_protocol_EP_tubes.py"),
        ]
        # Iterate and create download buttons
        for file_path, label, file_name in files_to_download:
            create_download_button(file_path, label, file_name)

        st.image("CSynB_Logo_text.png")
        st.image("Imperial.png")

        # st.header("Input Files")
        # moclo_plate_map_file = st.file_uploader(label="Upload Moclo parts map:dna:", type=["csv"])
        # customised_plate_map_file = st.file_uploader("Upload customised parts map:dna:", type=["csv"])
        # combinations_file = st.file_uploader("Upload assembly-info file", type=["csv"])
        # protocol_template_file = st.file_uploader("Upload protocol template file", type=["py"])

    # columns for user inputs
    st.header("Input Files")
    col1, col2 = st.columns(2)
    with col1:
        # st.header("A cat")
        moclo_plate_map_file = st.file_uploader(label="Upload Moclo parts map:dna:", type=["csv"])

    with col2:
        # st.header("A dog")
        customised_plate_map_file = st.file_uploader("Upload customised parts map:dna:", type=["csv"])

    col3, col4 = st.columns(2)
    with col3:
        # st.header("An owl")
        combinations_file = st.file_uploader("Upload assembly-info file", type=["csv"])

    with col4:
        # st.header("An owl")
        protocol_template_file = st.file_uploader("Upload protocol template file", type=["py"])

    # Main page for processing and output
    st.header("Protocol generation")
    if st.button("Process Data"):
        st.session_state.process_data = moclo_plate_map_file and customised_plate_map_file and combinations_file
    if st.session_state.process_data:
        try:
            try:
                # Process files
                fixed_plate_map_df = pd.read_csv(moclo_plate_map_file, header=None)
                customised_plate_map_df = pd.read_csv(customised_plate_map_file, header=None)
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
            # st.subheader("Output Plate Maps")
            # st.write(output_plate_maps)
            # st.subheader("Protocol")
            # st.write(protocol_string)

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
    # else:
    # st.error("Please upload all required files.")


if __name__ == "__main__":
    main()
