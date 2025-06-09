# Aligning camera frames and pose information to LJ
import os
import sys
import code
import argparse
import logging
import contextlib
import pathlib as pl
from datetime import datetime
from pathlib import Path

from glob import glob
import numpy as np
import h5py

from scipy.signal import find_peaks

def align_frames_to_LJ(homeFolder):
    """
    """
    outfile_name = os.path.join(homeFolder, 'results.h5')
    assert os.path.exists(outfile_name), 'Outfile for results not found for this session!'
    outfile = h5py.File(outfile_name, 'a')

    lj_dir = os.path.join(homeFolder, 'labjack')
    lj_file_maybe = glob(os.path.join(lj_dir, 'labjack_combined*.npy'))
    assert len(lj_file_maybe) > 0, "No secondary labjack file found, aborting."

    lj_file = max(lj_file_maybe, key=os.path.getmtime)
    lj_data = np.load(lj_file)
    frame_signal = lj_data[:,7]

    # Synchronization for frames
    # np.diff reduces array size by one, so need to include offset  \/
    frame_edge_inds = find_peaks(np.abs(np.diff(frame_signal)))[0] + 1
    frame_times = lj_data[frame_edge_inds,0].astype(int)
    
    # Placing within outfile
    code.interact(local=dict(globals(), **locals()))
    pose_group = outfile['pose/right']
    dataset_name = 'frametimes_clock'
    if dataset_name in pose_group:
        print(f"Warning: Dataset '{dataset_name}' already exists. Overwriting...")
        del pose_group[dataset_name]  # Delete existing dataset
            
    # Create the new dataset in the pose_dlc group
    pose_group.create_dataset(dataset_name, data=frame_times)

    # Synchronizing saccade onsets and offsets to nearest frame
    # Check if saccade information is present first
    # saccade_results_maybe = glob(os.path.join(homeFolder, 'videos', '*saccades.hdf'))
    
    
    # if len(saccade_results_maybe) > 0:
    #     saccade_results = max(saccade_results_maybe, key=os.path.getmtime)
    #     saccade_results = h5py.File(saccade_results, 'r')
    #     sacc_onsets = saccade_results['saccade_onset'][:].astype('int')
    #     sacc_offsets = saccade_results['saccade_offset'][:].astype('')

        # Align to the nearest frame, keep fractional value precision.
        #   End user can round if desired
        frame_numbers = np.arange(len(frame_edge_inds))
        sacc_onset_indices  = np.interp(sacc_onsets,  frame_numbers, frame_edge_inds)
        sacc_offset_indices = np.interp(sacc_offsets, frame_numbers, frame_edge_inds)

        pose_group.create_dataset('saccade_onsets_fractional_frames',  data=sacc_onset_indices)
        pose_group.create_dataset('saccade_offsets_fractional_frames', data=sacc_offset_indices)

        # Saccade amplitude
        # abs(onset - offset)

        # Saccade duration
        # sacc_offset_indices - sacc_onset_indices

        # Saccade frequency
        # Bin, number of saccades per binned second.

        # Saccde velocity
        # amplitude / time per saccade

    else:
        # Should verify that this goes to the processing log
        print('No saccade extraction results detected for this session')

    # If Crystal's data, 

    #outfile.close()
    code.interact(local=dict(globals(), **locals()))
    return

def align_saccades_to_frames(homeFolder):
    ''' Putting all pose information into seconds, plus
        calculating needed information for Crystal's data.
    '''
    outfile_name = os.path.join(homeFolder, 'results.h5')
    assert os.path.exists(outfile_name), 'Outfile for results not found for this session!'
    outfile = h5py.File(outfile_name, 'a')
    code.interact(local=dict(globals(), **locals()))



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('home', type=str, help='Home folder for the session')
    parser.add_argument('is_crystal', type=int, help='0 for LabJack alignment, 1 for Frame alignment with pseudo-LJ clock')
    namespace = parser.parse_args()
    if namespace.is_crystal == 0:
        align_frames_to_LJ(namespace.home)
    elif namespace.is_crystal == 1:
        align_saccades_to_frames(namespace.home)