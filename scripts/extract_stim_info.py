# Extract stimulus information from the file
import os
import code
import h5py
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from glob import glob

def parse_drifting_grating_metadata(file_path):
    # Read the file content
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Extract the header metadata (first 4 lines)
    metadata = {}
    for i in range(4):
        key, value = lines[i].split(':', 1)
        # Extract the numeric value and remove any parentheses content
        value = value.split('(')[0].strip()
        metadata[key.strip()] = float(value)
    
    # Get the column descriptions from line 5
    columns_desc = lines[4].split(':', 1)[1].strip()
    
    # Parse the data rows starting from line 6
    data_rows = []
    for i in range(5, len(lines)):
        if lines[i].strip():  # Skip empty lines
            values = [float(val.strip()) for val in lines[i].split(',')]
            data_rows.append(values)
    
    # Create DataFrame with appropriate column names
    df = pd.DataFrame(data_rows, columns=['Event', 'Motion direction', 'Probe contrast', 'Probe phase', 'Timestamp'])
    
    # Convert event types from numeric codes to descriptive labels
    event_mapping = {1: 'Grating', 2: 'Motion', 3: 'Probe', 4: 'ITI'}
    df['Event_type'] = df['Event'].map(event_mapping)
    
    return metadata, df

f_loc = r'/home/schollab-dion/Documents/felsen_pipeline/anna_sessions/DREADD13/videos'
dg_files = sorted(glob(os.path.join(f_loc, 'driftingGratingMetadata*')))
fs_files = sorted(glob(os.path.join(f_loc, 'fictiveSaccadeMetadata*')))

#outfile = h5py.File('test_file.h5', 'w')
outfile = h5py.File('/home/schollab-dion/Documents/felsen_pipeline/anna_sessions/DREADD13/results.h5', 'a')

### Process drifting grating files ~~~~~~~~~~~~~~
# Check for existence of dg metadata before populating
if 'stim_data/drifting_gratings' in outfile:
    del outfile['stim_data/drifting_gratings']
    outfile.flush()
#code.interact(local=dict(globals(), **locals())) 
event_mapping = {'Grating': 1, 'Motion': 2 , 'Probe': 3, 'ITI': 4}
for iter in range(len(dg_files)):  
    print(iter)
    dg_file = dg_files[iter]
    metadata, data_df = parse_drifting_grating_metadata(dg_file)

    md_int = data_df['Motion direction'].to_numpy().astype('int')
    probe_contrast = data_df['Probe contrast'].to_numpy()
    probe_phase = data_df['Probe phase'].to_numpy()
    timestamps = data_df['Timestamp'].to_numpy()
    event_types = data_df['Event_type'].to_numpy()
    event_types_int = np.array([event_mapping[event] for event in event_types])
    
    new_stim_group = outfile.create_group('stim_data/drifting_gratings/dg_'+str(iter))
    new_stim_group.create_dataset('motion_dir', data=md_int)
    new_stim_group.create_dataset('probe_contrast',data=probe_contrast)
    new_stim_group.create_dataset('probe_phase', data=probe_phase)
    new_stim_group.create_dataset('ts', data=timestamps)
    new_stim_group.create_dataset('event_types_int', data=event_types_int)
    
    # need to store metadata dict of spatial freq, velocity, orientation, baseline contrast



### Process fictive saccade files ~~~~~~~~~~~~~~~
if 'stim_data/fictive_saccades' in outfile:
    del outfile['stim_data/fictive_saccades']
    outfile.flush()

fs_event_mapping = {'probe':1, 'saccade':2, 'combined':3}

for iter in range(len(fs_files)):
    fs_file = fs_files[iter]
    fs_data = np.load(fs_file, allow_pickle=True)

    n_trials = len(fs_data['trials'])

    direction  = np.empty(n_trials)
    trial_type = np.empty(n_trials)

    for trial_num in range(n_trials):
        tr = fs_data['trials'][trial_num]
        direction[trial_num] = tr[0]
        trial_type[trial_num] = fs_event_mapping[tr[2]]

    new_stim_group = outfile.create_group('stim_data/fictive_saccades/fs_'+str(iter))
    new_stim_group.create_dataset('directions', data=direction.astype('int'))
    new_stim_group.create_dataset('trial_types', data=trial_type.astype('int'))

outfile.flush()
outfile.close()
#code.interact(local=dict(globals(), **locals())) 
