# Barcode extraction
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
from scipy.signal import find_peaks


def extract_barcodes(homeFolder, which_signal):

    """ Main logic pilfered (with permission) from ONECore DAQ Synchronization project
        (https://optogeneticsandneuralengineeringcore.gitlab.io/ONECoreSite/projects/DAQSyncro/DAQSyncronization/)
        
        which_signal=0 for LabJack
        which_signal=1 for NeuroPixels probe
    """
    global_tolerance = 0.20
    save_npy = True
    save_csv = True
    
    nbits = 32
    inter_barcode_interval = 5000 # ms
    ind_wrap_duration = 10 # ms
    ind_bar_duration = 30  # ms

    if which_signal == 0: # LJ
        barcodes_name = 'labjack_barcodes'
        raw_data_format = True
        signals_column = 5
        expected_sample_rate = 2000 # Hz
        barcodes_dir = os.path.join(homeFolder, 'labjack')
        signals_file_maybe = glob(os.path.join(barcodes_dir, 'labjack_combined_*.npy'))
        # If multiple are present, select the most recent.
        #code.interact(local=dict(globals(), **locals())) 
        assert len(signals_file_maybe) > 0, "No consolidated labjack file found for barcode extraction."
        signals_file = max(signals_file_maybe, key=os.path.getmtime)
    elif which_signal == 1: # NPX
        barcodes_name = 'neuropixels_barcodes'
        raw_data_format = False
        signals_column = 0
        expected_sample_rate = 30000 # Hz
        barcodes_dir = os.path.join(homeFolder, 'ephys', 'events', 'Neuropix-PXI-100.0', 'TTL_1')
        signals_file = os.path.join(barcodes_dir, 'timestamps.npy')
    else:
        # TODO Better error raising here
        assert False, " Terminating barcode extraction. \n Value beyond 0 or 1 given for signal source."

    # Global variables and tolerances
    wrap_duration = 3 * ind_wrap_duration # Off-On-Off
    total_barcode_duration = nbits * ind_bar_duration + 2 * wrap_duration

    # Tolerance conversions
    min_wrap_duration = ind_wrap_duration - ind_wrap_duration * global_tolerance
    max_wrap_duration = ind_wrap_duration + ind_wrap_duration * global_tolerance
    min_bar_duration = ind_bar_duration - ind_bar_duration * global_tolerance
    max_bar_duration = ind_bar_duration + ind_bar_duration * global_tolerance
    sample_conversion = 1000 / expected_sample_rate # Convert sampling rate to msec

        
    try:
        signals_numpy_data = np.load(signals_file)
        signals_located = True
    except:
        signals_numpy_data = ''
        print("Signals .npy file not located; please check your filepath")
        signals_located = False

    # Check whether signals_numpy_data exists; if not, end script with sys.exit().
    if signals_located:
        #LJ = If data is in raw format and has not been sorted by "peaks"
        if raw_data_format:

            # Extract the signals_column from the raw data
            barcode_column = signals_numpy_data[:, signals_column]
            barcode_array = barcode_column.transpose()
            # Extract the indices of all events when TTL pulse changed value.
            event_index, _ = find_peaks(np.abs(np.diff(barcode_array)), height=0.9)
            # Convert the event_index to indexed_times to align with later code.
            indexed_times = event_index # Just take the index values of the raw data

        # NP = Collect the pre-extracted indices from the signals_column.
        else:
            indexed_times = signals_numpy_data

        # Find time difference between index values (ms), and extract barcode wrappers.
        events_time_diff = np.diff(indexed_times) * sample_conversion # convert to ms
        wrapper_array = indexed_times[np.where(
                        np.logical_and(min_wrap_duration < events_time_diff,
                                    events_time_diff  < max_wrap_duration))[0]]

        # Isolate the wrapper_array to wrappers with ON values, to avoid any
        # "OFF wrappers" created by first binary value.
        false_wrapper_check = np.diff(wrapper_array) * sample_conversion # Convert to ms
        # Locate indices where two wrappers are next to each other.
        false_wrappers = np.where(
                        false_wrapper_check < max_wrap_duration)[0]
        # Delete the "second" wrapper (it's an OFF wrapper going into an ON bar)
        wrapper_array = np.delete(wrapper_array, false_wrappers+1)

        # Find the barcode "start" wrappers, set these to wrapper_start_times, then
        # save the "real" barcode start times to signals_barcode_start_times, which
        # will be combined with barcode values for the output .npy file.
        wrapper_time_diff = np.diff(wrapper_array) * sample_conversion # convert to ms
        barcode_index = np.where(wrapper_time_diff < total_barcode_duration)[0]
        wrapper_start_times = wrapper_array[barcode_index]
        signals_barcode_start_times = wrapper_start_times - ind_wrap_duration / sample_conversion
        # Actual barcode start is 10 ms before first 10 ms ON value.
        
        # Using the wrapper_start_times, collect the rest of the indexed_times events
        # into on_times and off_times for barcode value extraction.
        on_times = []
        off_times = []
        for idx, ts in enumerate(indexed_times):    # Go through indexed_times
            # Find where ts = first wrapper start time
            if ts == wrapper_start_times[0]:
                # All on_times include current ts and every second value after ts.
                on_times = indexed_times[idx::2]
                off_times = indexed_times[idx+1::2] # Everything else is off_times

        # Convert wrapper_start_times, on_times, and off_times to ms
        wrapper_start_times = wrapper_start_times * sample_conversion
        on_times = on_times * sample_conversion
        off_times = off_times * sample_conversion

        signals_barcodes = []
        for start_time in wrapper_start_times:
            oncode = on_times[
                np.where(
                    np.logical_and(on_times > start_time,
                                on_times < start_time + total_barcode_duration)
                )[0]
            ]
            offcode = off_times[
                np.where(
                    np.logical_and(off_times > start_time,
                                off_times < start_time + total_barcode_duration)
                )[0]
            ]
            curr_time = offcode[0] + ind_wrap_duration # Jumps ahead to start of barcode
            bits = np.zeros((nbits,))
            interbit_ON = False # Changes to "True" during multiple ON bars

            for bit in range(0, nbits):
                next_on = np.where(oncode >= (curr_time - ind_bar_duration * global_tolerance))[0]
                next_off = np.where(offcode >= (curr_time - ind_bar_duration * global_tolerance))[0]

                if next_on.size > 1:    # Don't include the ending wrapper
                    next_on = oncode[next_on[0]]
                else:
                    next_on = start_time + inter_barcode_interval

                if next_off.size > 1:    # Don't include the ending wrapper
                    next_off = offcode[next_off[0]]
                else:
                    next_off = start_time + inter_barcode_interval

                # Recalculate min/max bar duration around curr_time
                min_bar_duration = curr_time - ind_bar_duration * global_tolerance
                max_bar_duration = curr_time + ind_bar_duration * global_tolerance

                if min_bar_duration <= next_on <= max_bar_duration:
                    bits[bit] = 1
                    interbit_ON = True
                elif min_bar_duration <= next_off <= max_bar_duration:
                    interbit_ON = False
                elif interbit_ON == True:
                    bits[bit] = 1

                curr_time += ind_bar_duration

            barcode = 0

            for bit in range(0, nbits):             # least sig left
                barcode += bits[bit] * pow(2, bit)

            signals_barcodes.append(barcode)

    else: # If signals_located = False
        sys.exit("Data not found. Program has stopped.")

    ################################################################
    ### Print out final output and save to chosen file format(s) ###
    ################################################################

    # Create merged array with timestamps stacked above their barcode values
    signals_time_and_bars_array = np.vstack((signals_barcode_start_times,
                                            np.array(signals_barcodes)))
    print("Final Ouput: ", signals_time_and_bars_array)

    time_now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")

    if save_npy:
        output_file = os.path.join(barcodes_dir, (barcodes_name + time_now))
        np.save(output_file, signals_time_and_bars_array)

    if save_csv:
        output_file = os.path.join(barcodes_dir, (barcodes_name + time_now + ".csv"))
        np.savetxt(output_file, signals_time_and_bars_array,
                delimiter=',', fmt="%s")





if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('home', type=str, help='Home folder for the session')
    parser.add_argument('sig_source', type=int, help='0 for LabJack, 1 for Neuropixels')
    parser.add_argument('processing_path', type=int, help='0 - Session w/ labjack, ephys. 1 - Session w/ labjack, ephys, strai gauge. 2 - Crystals data, keep in frame clock')
    namespace = parser.parse_args()

    if namespace.processing_path != 2:
        # If processing_path is not 2, we can proceed with barcode extraction
        if namespace.sig_source not in [0, 1]:
            print("Invalid signal source. Use 0 for LabJack or 1 for Neuropixels.")
            sys.exit(-1)
        extract_barcodes(namespace.home, namespace.sig_source)
    else:
        print("Skipping barcode extraction for crystals data.")