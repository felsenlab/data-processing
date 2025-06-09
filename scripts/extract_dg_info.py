# Get information out of drifting gratings
import os
import code
import argparse
import pathlib as pl
from data_processing import PrintSuppressor

import h5py


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('home', type=str, help='Home folder for the session')
    #parser.add_argument('is_crystal', type=int, help='0 - file has LJ for timestamping. 1 - Crystals data, keep in frame clock')
    namespace = parser.parse_args()

    outfile = h5py.File(os.path.join(namespace.home, 'results.h5'), 'a')
    
    