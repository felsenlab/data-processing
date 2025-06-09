# Code for initializing an h5 file to contain our results
# as each module completes.
import os
import code
import h5py
import argparse
import logging
import contextlib
import pathlib as pl

# This should go in a helper script file
def parse_experiment_file(file_path):
    """
    Parse an experiment file into:
    1. A dictionary with metadata
    2. A NumPy array with numerical data
    """
    # Initialize containers
    metadata = {}
    data_lines = []
    column_info = ""
    
    # Read the file
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    # Process lines
    reading_metadata = True
    found_columns = False
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
            
        if reading_metadata:
            if "Columns:" in line:
                found_columns = True
                column_info = line
                reading_metadata = False
                continue
                
            # Parse metadata lines (Key: Value format)
            if ":" in line:
                parts = line.split(':', 1)
                key = parts[0].strip()
                value = parts[1].strip()
                metadata[key] = value
        else:
            # Once we're past the metadata, collect data lines
            # Check if line has commas (CSV data)
            if ',' in line:
                data_lines.append(line)
    
    # Extract column names from the column info
    if found_columns:
        column_desc = column_info.split(':', 1)[1].strip()
        metadata['Columns'] = column_desc
    
    # Convert data lines to numpy array
    data_array = np.array([list(map(float, line.split(','))) for line in data_lines])
    
    return metadata, data_array



# This should go in a helper script file
def parse_txt_to_dict(file_path):
    """
    Used with 'metadata.txt'

    Parse a text file with key-value pairs into a Python dictionary.
    Each line should have format "Key: Value"
    """
    result_dict = {}
    
    with open(file_path, 'r') as file:
        for line in file:
            # Skip empty lines
            if line.strip() == '':
                continue
                
            # Split each line at the first colon
            parts = line.strip().split(':', 1)
            
            # Ensure the line has the expected format
            if len(parts) == 2:
                key = parts[0].strip()
                value = parts[1].strip()
                result_dict[key] = value
    
    return result_dict



# This should go in a helper script file
def store_string_dict_to_hdf5(file_path, data_dict, group_name):
    """Stores a dictionary of strings to an HDF5 file under a specified group,
     handling cases where the file is already open.
     
     Args:
     file_path (str): Path to the HDF5 file.
     data_dict (dict): Dictionary of strings to store.
     group_name (str): Name of the group to store the dictionary under.
     """
    try:
        # Attempt to open the file in read/write mode; create if it doesn't exist
        with h5py.File(file_path, 'a') as hf:
            # Create the group if it doesn't exist
            if group_name not in hf:
                grp = hf.create_group(group_name)
            else:
                grp = hf[group_name]
                
            # Delete existing datasets in the group to avoid conflicts
            for key in list(grp.keys()):
                del grp[key]
                
            # Store each key-value pair in the dictionary as a dataset
            for key, value in data_dict.items():
                grp.create_dataset(key, data=value, shape=1, dtype=h5py.string_dtype())
                
            # The file will be automatically flushed and closed at the end of the 'with' block
            print(f"Data stored successfully in group '{group_name}'.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
    


def init_and_populate_outfile(homeFolder):
    """ Creates new session-level output file.
        Populates new file with session-level metadata.
    """
    outfile = h5py.File(os.path.join(homeFolder, 'results.h5'), 'w')

    meta = parse_txt_to_dict(os.path.join(homeFolder, 'metadata.txt'))
    store_string_dict_to_hdf5(os.path.join(homeFolder, 'results.h5'), meta, '/animal_info')
    outfile.close()
    
    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('home', type=str, help='Home folder for the session')
    namespace = parser.parse_args()
    init_and_populate_outfile(namespace.home)


