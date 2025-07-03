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
    #name = ['pitx010', 'pitx012'],
    name = [],
    #description = ['Dosage 0mg/kg'],
    description = [],
    weight = ['weight>20g'] # weight doesn't work yet, needs to be fixed.
)

path = '/media/schollab-dion/CM_drive/testing_GB_code'
path = Path(path)
date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
output_path = 'combined_analysis.h5'
###########################################################

doses = list()
names = list()
weights = list()
# Has a session-level h5 file and contains at least some data.
paths_with_h5_info = list()
all_paths = list()
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
        all_paths.append(session_dir)
        if 'results.h5' in files and os.path.getsize(os.path.join(session_dir, 'results.h5')) > 0:
            paths_with_h5_info.append(session_dir)
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



if search_terms['description'] == []:
    doses_filter = [True] * len(paths_with_h5_info)
else:
    doses_filter = [dose in search_terms['description'] if dose else False for dose in doses]

if search_terms['name'] == []:
    names_filter = [True] * len(paths_with_h5_info)
else:    
    names_filter = [name in search_terms['name'] if name else False for name in names]
# Weights does not work yet. Slightly more complicated because it's a different conditional.
#weights_filter = [weight is not None and weight > float(search_terms['weight'].split('>')[1][:-1]) for weight in weights]


final_filter = np.logical_and(doses_filter, names_filter)
matching_search_paths = np.array(paths_with_h5_info)[final_filter]


# Text menu :
#   1. Show all paths matching search criteria
#   2. Export all paths, regardless of search criteria, to a text file
#   3. Combine all matching paths into a single h5 file
#   (This gives you all sessions so you can initialize everything, process, then combine)
#   4. Exit


for path in matching_search_paths:
    print(f"Matching path: {path}")

user_in = input("Do you want to combine these files? (y/n): ")
if user_in.lower() == 'y':
    # Load the data from all matching files and combine them
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

