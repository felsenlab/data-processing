import os
import code
import argparse
import logging
import contextlib
import pathlib as pl

import numpy as np
import h5py

from data_processing import PrintSuppressor
try:
    with PrintSuppressor():
        import deeplabcut as dlc
except ImportError:
    dlc = None

from glob import glob

# TODO: Make this more intelligent/flexible
def locateDeeplabcutProject(
    ):
    """
    """

    return '/home/schollab-dion/Documents/DeepLabCut/sacnet3-felsenlab-2025-03-24/config.yaml'

def collectVideos(
    homeFolder,
    ):
    """
    """
    if type(homeFolder) != pl.Path:
        homeFolder = pl.Path(homeFolder)

    return [str(path) for path in homeFolder.rglob(f"{'[0-9]' * 8}*unit*session*.mp4")]

def analyzeVideosQuietly(*args, **kwargs):
    """
    Call DeepLabCut's analyze_videos function but suppress messaging
    """

    kwargs_ = {}
    kwargs_.update(kwargs)
    with PrintSuppressor():
        return dlc.analyze_videos(*args, **kwargs_)

    # Delete h5 and pickle files
    for video in kwargs_['videos']:
        video = pl.Path(video)
        parent = video.parent
        for file in parent.iterdir():
            if 'DLC' in file.name and (file.suffix == '.h5' or file.suffix == '.pickle'):
                file.unlink()

    return

def analyzeVideos(*args, **kwargs):
    """
    """

    kwargs_ = {}
    kwargs_.update(kwargs)
    dlc.analyze_videos(*args, **kwargs)

    return

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('home', type=str, help='Home folder for the session')
    namespace = parser.parse_args()
    
    config = locateDeeplabcutProject()
    videos = collectVideos(namespace.home)
    videos = [video for video in videos if 'labeled' not in video] # Exclude labeled videos
    if len(videos) == 0:
        print('No videos found to analyze')
        exit(-1)
    print('Found the following videos to analyze:')
    for video in videos:
        print(video)

    # If we don't want to analyze videos, we can skip this step
    # Analyze videos
    analyzeVideos(
        config,
        videos=videos,
        save_as_csv=True
    )
    # code.interact(local=dict(globals(), **locals())) 

    # Get the most recent results this way
    dlc_results = glob(os.path.join(namespace.home, 'videos', '*DLC*.csv'))
    recent_files = sorted(dlc_results, key=os.path.getmtime, reverse=True)
    # Get most recent for each camtype
    left_cam_dlc  = next((f for f in recent_files if 'leftCam' in f), None)
    right_cam_dlc = next((f for f in recent_files if 'rightCam' in f), None)

    if left_cam_dlc is None and right_cam_dlc is None:
        print('No DeepLabCut results found. Exiting.')
        exit(-1)
    # Can be None if no results are found for a camera
    files_to_insert = [left_cam_dlc, right_cam_dlc]

    # Append results to outfile
    outfile = h5py.File(os.path.join(namespace.home,'results.h5'), 'a')
    
    # Remove prev results if things have already run
    if 'pose' in outfile:
        del outfile['pose']
        outfile.flush() # Necessary before continuing

    for f in files_to_insert:
        if f is None:
            continue
        which_cam = 'left' if 'leftCam' in f else 'right'
        print(f'Inserting results for {which_cam} camera')

        # Read the csv file
        dlc_results = np.genfromtxt(f, delimiter=',', skip_header=3)
        dlc_results = dlc_results[:, 1:]
        # Check if the results are empty
        if dlc_results.size == 0:
            print(f'No results found for {which_cam} camera. Skipping.')
            continue
        
        # Check if the results have the expected number of columns
        # Current sacnet3 trackpoints are:
        # eye - nasal, temporal, dorsal, ventral
        # pupil - center, nasal, temporal, dorsal, ventral
        # ... and there's x, y and a confidence value for each point.
        # This means we expect 9 trackpoints * 3 (x, y, confidence) = 27 columns 
        expected_columns = 27
        if dlc_results.shape[1] < expected_columns:
            print(f'Unexpected number of columns found for {which_cam} camera. Skipping.')
            continue
        # Create a group for the camera
        pose_group = outfile.create_group('/pose/' + which_cam)
        pose_group.attrs['description'] = 'pose values from DeepLabCut'
        pose_group.attrs['camera'] = which_cam
        pose_group.attrs['video'] = f
        pose_group.attrs['config'] = config
        # Create a dataset for the pose values
        pose_dlc = pose_group.create_group('uncorrected')
        pose_dlc.create_dataset('eye_nasal_x', data=dlc_results[:, 0])
        pose_dlc.create_dataset('eye_nasal_y', data=dlc_results[:, 1])
        pose_dlc.create_dataset('eye_temporal_x', data=dlc_results[:, 3])
        pose_dlc.create_dataset('eye_temporal_y', data=dlc_results[:, 4])
        pose_dlc.create_dataset('eye_dorsal_x', data=dlc_results[:, 6])
        pose_dlc.create_dataset('eye_dorsal_y', data=dlc_results[:, 7])
        pose_dlc.create_dataset('eye_ventral_x', data=dlc_results[:, 9])
        pose_dlc.create_dataset('eye_ventral_y', data=dlc_results[:, 10])
        pose_dlc.create_dataset('pupil_center_x', data=dlc_results[:, 12])
        pose_dlc.create_dataset('pupil_center_y', data=dlc_results[:, 13])
        pose_dlc.create_dataset('pupil_nasal_x', data=dlc_results[:, 15])
        pose_dlc.create_dataset('pupil_nasal_y', data=dlc_results[:, 16])
        pose_dlc.create_dataset('pupil_temporal_x', data=dlc_results[:, 18])
        pose_dlc.create_dataset('pupil_temporal_y', data=dlc_results[:, 19])
        pose_dlc.create_dataset('pupil_dorsal_x', data=dlc_results[:, 21])
        pose_dlc.create_dataset('pupil_dorsal_y', data=dlc_results[:, 22])
        pose_dlc.create_dataset('pupil_ventral_x', data=dlc_results[:, 24])
        pose_dlc.create_dataset('pupil_ventral_y', data=dlc_results[:, 25])
        # Force the file to flush to disk
        outfile.flush()

    outfile.close()
    print('Pose extraction completed. Results saved to results.h5')
    
    #code.interact(local=dict(globals(), **locals()))


