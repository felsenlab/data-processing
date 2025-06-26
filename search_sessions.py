# Filter contents to be able to group together data and make comparisons
import os
import code
from pathlib import Path
import re
import h5py
import numpy as np
import matplotlib.pyplot as plt

from collections import Counter

import logging


###########################################################
# Define search terms for filtering the data
# Each search term must be a list, even if there's only one term.
search_terms = dict(
    name = ['pitx010', 'pitx012'],
    description = ['Dosage 0mg/kg'],
    weight = ['weight>20g'] # weight doesn't work yet, needs to be fixed.
)

path = '/media/schollab-dion/CM_drive/testing_GB_code'
path = Path(path)
date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
output_path = 'combined_analysis.h5'
###########################################################


def copy_hdf5_recursive(src_group, dst_group):
    """
    Recursively copy HDF5 group structure with full preservation
    """
    # Copy attributes of current group
    for attr_name in src_group.attrs:
        dst_group.attrs[attr_name] = src_group.attrs[attr_name]
    
    # Iterate through all items
    for key in src_group.keys():
        src_item = src_group[key]
        
        if isinstance(src_item, h5py.Group):
            # Create new group and recurse
            dst_subgroup = dst_group.create_group(key)
            copy_hdf5_recursive(src_item, dst_subgroup)
            
        elif isinstance(src_item, h5py.Dataset):
            # Copy dataset with all metadata
            dst_group.copy(src_item, key)



def combine_sessions(file_paths, output_path, session_naming=None):
    """
    Combine multiple HDF5 session files into one analysis file
    """
    with h5py.File(output_path, 'w') as analysis_file:
        for i, dir_path in enumerate(file_paths):
            results_path = os.path.join(dir_path, 'results.h5')
            
            if not os.path.exists(results_path):
                logging.warning(f"File not found: {results_path}")
                continue
                
            try:
                with h5py.File(results_path, 'r') as session_file:
                    # Create session group with meaningful name
                    date = dir_path.parent.name
                    session_num = dir_path.name
                    session_name = f"{date}_{session_num}"
                    
                    session_group = analysis_file.create_group(session_name)
                    
                    # Copy everything recursively
                    copy_hdf5_recursive(session_file, session_group)
                    
                    # Add metadata about source
                    session_group.attrs['source_path'] = dir_path
                    session_group.attrs['session_index'] = i
                    
            except Exception as e:
                logging.error(f"Error processing {results_path}: {e}")
                continue




doses = list()
names = list()
weights = list()
all_indexed_paths = list()
has_saccades = list()

date_dirs = [
    item for item in path.iterdir()
    if item.is_dir() and date_pattern.match(item.name)
]

for date_dir in date_dirs:
    session_dirs = [
        item for item in date_dir.iterdir()
        if item.is_dir() and item.name.startswith('session')
    ]
    for session_dir in session_dirs:
        files = os.listdir(session_dir)

        if 'results.h5' in files and os.path.getsize(os.path.join(session_dir, 'results.h5')) > 0:
            all_indexed_paths.append(session_dir)
            h5_file_path = os.path.join(session_dir, 'results.h5')

            with h5py.File(h5_file_path, 'r') as data:
                # Check if animal_info exists in the file
                if 'animal_info' in data:
                    animal_info = data['animal_info']

                    # Check for each search term
                    if 'description' in animal_info:
                        doses.append(animal_info['description'][:][0].decode('utf-8'))
                    else:
                        doses.append(None)
                    
                    if 'name' in animal_info:
                        names.append(animal_info['name'][:][0].decode('utf-8'))
                    else:
                        names.append(None)
                    
                    if 'weight' in animal_info:
                        #weights.append(float(animal_info['weight'][:][0].decode('utf-8'))[:-1])
                        weight_str = animal_info['weight'][:][0].decode('utf-8')
                        # Remove 'g' and convert to float
                        weights.append(float(re.sub(r'[^0-9.]', '', weight_str)))
                    else:
                        weights.append(None)
                if 'saccades' in data:
                    has_saccades.append(True)
                else:
                    has_saccades.append(False)

counts = Counter(zip(names, doses))

print("Counts of combinations of names and doses:")
for combination, count in counts.items():
    print(f"{combination} - {count} sessions")
print()


doses_filter = [dose in search_terms['description'] if dose else False for dose in doses]
names_filter = [name in search_terms['name'] if name else False for name in names]
# Weights does not work yet. Slightly more complicated because it's a different conditional.
#weights_filter = [weight is not None and weight > float(search_terms['weight'].split('>')[1][:-1]) for weight in weights]


final_filter = np.logical_and(doses_filter, names_filter)
matching_search_paths = np.array(all_indexed_paths)[final_filter]

for path in matching_search_paths:
    print(f"Matching path: {path}")

user_in = input("Do you want to combine these files? (y/n): ")
if user_in.lower() == 'y':
    # Load the data from all matching files and combine them
    #combine_sessions(matching_search_paths, 'combined_analysis.h5')
    with h5py.File(output_path, 'a') as dest:
        for dir_path in matching_search_paths:
            results_file = os.path.join(dir_path, 'results.h5')
            with h5py.File(results_file, 'r') as src:
                date = dir_path.parent.name
                session_num = dir_path.name
                session_name = f"{date}_{session_num}"
                session_group = dest.create_group(session_name)

                for key in src.keys():
                    src.copy(key, session_group)
                for attr_name, attr_value in src.attrs.items():
                    session_group.attrs[attr_name] = attr_value
            


elif user_in.lower() == 'n':
    user_in = input("Do you want to export the file list to a text file? (y/n): ")
    if user_in.lower() == 'y':
        with open("matching_sessions.txt", "w") as f:
            for path in matching_search_paths:
                f.write(f"{path}\n")
        print("File list exported successfully.")

code.interact(local=dict(globals(), **locals()))


# Cookbook - 
# 1. Point script to data directory
# 2. Find all h5 files for each session
# 3. Grab animal_info from each file
# 4. Check if animal_info contains the search terms
# 5. All files matching the search terms are added to a list
# 6. Show list of files matching to the user
# 7. Ask user if they want to load the data from these files
# 8. If yes, concatenate the data from all files into a single dataset
# 9. If no, exit the script to allow user to change search terms or directory


code.interact(local=dict(globals(), **locals()))