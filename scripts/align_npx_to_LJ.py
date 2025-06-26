import os
import code
import argparse
import logging
import contextlib
import pathlib as pl
from datetime import datetime

import numpy as np
import matplotlib.pyplot as plt

from glob import glob

from scipy import interpolate
import h5py

# Key parts of the solution to two problems:
# 1. Non-linear drift between clocks - using interpolation instead of linear conversion
# 2. Aligning to secondary device instead of main device
def align_barcodes(homeFolder):
    """ Main logic pilfered (with permission) from ONECore DAQ Synchronization project
        (https://optogeneticsandneuralengineeringcore.gitlab.io/ONECoreSite/projects/DAQSyncro/DAQSyncronization/)
    """

    # Input variables
    main_sample_rate = 30000 # Expected sample rate of main data, in Hz
    secondary_sample_rate = 2000 # Expected sample rate of secondary data, in Hz
    convert_timestamp_column = 0 # Column that timestamps are located in secondary data

    # Output variables
    alignment_name = 'barcode_alignment_done_to_lj' # Name of output file.
    save_npy = True   # Save output file as a .npy file
    save_csv = True    # Save output file as a .csv file

    ### Select Files for Barcode Alignment 
    # First, outfile to make sure we're gtg from previously
    outfile_name = os.path.join(homeFolder, 'results.h5')
    assert os.path.exists(outfile_name), 'Outfile for results not found for this session!'
    outfile = h5py.File(outfile_name, 'a')

    main_dir= os.path.join(homeFolder, 'ephys', 'events', 'Neuropix-PXI-100.0', 'TTL_1')
    main_file_maybe = glob(os.path.join(main_dir, 'neuropixels_barcodes*.npy'))
    assert len(main_file_maybe) > 0, "No main ephys barcodes file found, aborting." 
    main_file = max(main_file_maybe, key=os.path.getmtime) # get most recent

    secondary_dir = os.path.join(homeFolder, 'labjack')
    secondary_file_maybe = glob(os.path.join(secondary_dir, 'labjack_barcodes*.npy'))
    assert len(secondary_file_maybe) > 0, "No secondary labjack barcodes file found, aborting."
    secondary_file = max(secondary_file_maybe, key=os.path.getmtime)

    # Try to load the selected files; if they fail, inform the user.
    try:
        main_numpy_data = np.load(main_file)
    except:
        main_numpy_data = ''
        print("Main .npy file not located/failed to load; please check the filepath")

    try:
        secondary_numpy_data = np.load(secondary_file)
    except:
        secondary_numpy_data = ''
        print("Secondary .npy file not located/failed to load; please check the filepath")

    ### Extract Barcodes and Index Values, then Calculate Linear Variables 
    barcodes_row = 1
    barcode_timestamps_row = 0


    main_numpy_barcode = main_numpy_data[barcodes_row, :]
    secondary_numpy_barcode = secondary_numpy_data[barcodes_row, :]

    main_numpy_timestamp = main_numpy_data[barcode_timestamps_row, :]
    secondary_numpy_timestamp = secondary_numpy_data[barcode_timestamps_row, :]

    # Find shared barcodes between both recording systems
    shared_barcodes, main_indices, secondary_indices = np.intersect1d(
        main_numpy_barcode, secondary_numpy_barcode, return_indices=True
    )

    # Use main_index and second_index arrays to extract related timestamps
    main_shared_barcode_times = main_numpy_timestamp[main_indices]
    secondary_shared_barcode_times = secondary_numpy_timestamp[secondary_indices]


    # Extract timestamps of shared barcodes in both systems
    main_shared_timestamps = main_numpy_timestamp[main_indices]
    secondary_shared_timestamps = secondary_numpy_timestamp[secondary_indices]
    
    # Create non-linear interpolation function to better account for clock drift
    # This maps from main device time → secondary device time
    main_to_secondary_time = interpolate.interp1d(
        main_shared_timestamps,
        secondary_shared_timestamps,
        kind='linear',        # Can use 'cubic' for smoother interpolation
        bounds_error=False,   # Return NaN for points outside the interpolation range
        fill_value="extrapolate"  # Allow extrapolation for points outside range
    )

    # Because the 'secondary' labjack is the primary clock, we're not interested
    #   in changing these values. Rather, we're interested in preserving the timing of everything else.
    #code.interact(local=dict(globals(), **locals()))
    npx_auto_sort_dir = os.path.join(homeFolder, 'ephys', 'sorting', 'auto')
    spike_times = np.load(os.path.join(npx_auto_sort_dir, 'spike_times.npy'))
    
    spike_times_in_lj = main_to_secondary_time(spike_times).astype('int')
    spike_group = outfile.create_group('/ephys/spikes')
    spike_group.create_dataset('spikes_in_lj_time',data=spike_times_in_lj)
    spike_group.attrs['description']='Times for spikes in this format'
    outfile.close()
    # Save results into outfile
    #code.interact(local=dict(globals(), **locals()))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('home', type=str, help='Home folder for the session')
    parser.add_argument('processing_path', type=int, help='0 - Session w/ labjack, ephys. 1 - Session w/ labjack, ephys, strai gauge. 2 - Crystals data, keep in frame clock')
    namespace = parser.parse_args()

    if namespace.processing_path != 2:
        align_barcodes(namespace.home)
    else:
        print("No need to align barcodes for crystals data, exiting.")
    