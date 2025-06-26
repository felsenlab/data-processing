import os
import re
import sys
import code
import argparse
import logging
import contextlib
import pathlib as pl
from datetime import datetime
from pathlib import Path

from natsort import os_sorted

import numpy as np
from numpy import savetxt

import h5py

from tqdm import tqdm

def combine_LJ_data(homeFolder):
    """ Pilfered (with permission) from ONECore DAQ Synchronization project
        (https://optogeneticsandneuralengineeringcore.gitlab.io/ONECoreSite/projects/DAQSyncro/DAQSyncronization/)

    """
    header_present = True # Set to True if all .dat files have headers.
    headerdata_split = 10 # Row number where data separates from header.
    save_npy = True  # Set to True if you want to save the output as a .npy file
    save_csv = False  # Set to True if you want to save the output as a .csv file
    keep_header = False # Set to True if you want the header put back in the csv file

    lj_in_data_dir = os.path.join(homeFolder, 'labjack')
    lj_out_data_dir = lj_in_data_dir

    lj_mat = list()
    lj_array = np.empty(0)
    first_array = True
    
    file_name_list = os_sorted(os.listdir(lj_in_data_dir))
    
    #for file_name in file_name_list:
    for file_name in tqdm(file_name_list, desc='Processing LabJack files'):
        if file_name[-3:] == 'dat':      # Only run on .dat files output from the LJ
            file_name_list_dir = os.path.join(lj_in_data_dir, file_name)

            with open(file_name_list_dir, 'rb') as stream:
                all_rows = stream.readlines()

            # split into header and content
            if header_present:
                data_header = all_rows[:headerdata_split]
                data_body = all_rows[headerdata_split:]
            else:
                data_body = all_rows

            # extract data and convert to float datatype
            data_body_float = list()

            for index, data_body_row in enumerate(data_body):
                data_body_row_cleaned = data_body_row.decode().rstrip('\r\n').split('\t')
                data_body_row_cleaned = [float(data_pt) for data_pt in data_body_row_cleaned]
                data_body_float.append(data_body_row_cleaned)

            data_body_np = np.array(data_body_float)

            if save_npy:  # Add numpy arrays together prior to string transformation
                if first_array: # Replace lj_array w/ first instance of data_body_np
                    lj_array = data_body_np
                    first_array = False     # Don't do it again.
                    first_numpy_array = file_name
                else:
                    try:
                        # Combine later arrays to first file's array.
                        lj_array = np.concatenate((lj_array, data_body_np), axis=0)
                    except ValueError: # Error caused if arrays' column dimensions don't line up (wrong data type)
                        print("Data from ", file_name, " doesn't match dimensions of '",
                            first_numpy_array, "'. Please check files.")

            # Convert data into string format for clean .csv output
            for irow_body in range(data_body_np.shape[0]):
                data_list_form = data_body_np[irow_body,:].tolist()
                for index, data in enumerate(data_list_form):
                    data_list_form[index] = str(data)
                lj_mat.append(', '.join(data_list_form))

    ################################################################
    ### Print out final output and save to chosen file format(s) ###
    ################################################################

    time_now = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    out_file_name = "labjack_combined_"

    if save_npy:
        output_file = os.path.join(lj_out_data_dir, out_file_name + time_now)
        np.save(output_file, lj_array)
        print("File has been saved in .npy format here: ", output_file)

    if save_csv:
        if header_present and keep_header: # Clean up the header info for attachment to data
            data_header_cleaned = list()

            for data_header_row in data_header:
                data_header_row_cleaned = str(data_header_row.decode().rstrip('\r\n').strip("\[").split('\t'))
                data_header_row_cleaned_again = data_header_row_cleaned.strip("\[]''")
                data_header_cleaned.append(data_header_row_cleaned_again)

            # Attach header info to lj_mat data
            np.warnings.filterwarnings('ignore', category=np.VisibleDeprecationWarning) # Not cool. https://stackoverflow.com/questions/63097829/debugging-numpy-visibledeprecationwarning-ndarray-from-ragged-nested-sequences
            lj_mat_w_header = data_header_cleaned + lj_mat
            lj_mat_w_header_array = np.array(lj_mat_w_header)
        else:
            lj_mat_w_header = np.array(lj_mat)

        output_file = os.path.join(lj_out_data_dir, (out_file_name + time_now + '.csv'))
        savetxt(output_file, lj_mat_w_header, delimiter=',', fmt="%s")
        print("File has been saved in .csv format here: ", output_file)



# TODO : combine_LJ_data user input can be handled better
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('home', type=str, help = 'Home folder for the session')
    parser.add_argument('processing_path', type=int, help='0 - Session w/ labjack, ephys. 1 - Session w/ labjack, ephys, strai gauge. 2 - Crystals data, keep in frame clock')
    namespace = parser.parse_args()
    
    if namespace.processing_path != 2:
        combine_LJ_data(namespace.home)
    else:
        print('Skipping combine_LJ_data for crystals data')
