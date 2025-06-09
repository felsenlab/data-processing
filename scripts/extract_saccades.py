import os
import code
import argparse
import pathlib as pl
from data_processing import PrintSuppressor
try:
    import saccade_extraction as se
except:
    se = None
import h5py
import numpy as np

from glob import glob

# TODO: Make this more intelligent/flexible
def locateSaccadeExtractionProject():
    """
    """

    return '/home/schollab-dion/Projects/sacnet3/config.yaml'

def collectFileSets(
    homeFolder
    ):
    """
    Needed to be modified such that only the most recent leftcam and rightcam
    pose estimates are collected. This is because the saccade extraction
    pipeline expects a single pose estimate file and a single timestamps file,
    but multiple pose estimates may be present in the home folder.
    """
    if type(homeFolder) != pl.Path:
        homeFolder = pl.Path(homeFolder)
    poseEstimates = list(homeFolder.rglob('*DLC*.csv'))
    fileSets = list()
    
    for poseEstimate in poseEstimates:
        fileSet = list()
        fileSet.append(poseEstimate)
        stem = poseEstimate.name.split('DLC')[0].rstrip('-0000')
        result = list(homeFolder.rglob(f'*{stem}*timestamps.txt'))
        if len(result) == 1:
            interframeIntervals = result.pop()
            fileSet.append(interframeIntervals)
        fileSet = tuple(fileSet)
        if len(fileSet) == 2:
            fileSets.append(fileSet)
        else:
            pass
    return fileSets

def extractSaccades(*args, **kwargs):
    """
    """

    kwargs_ = {}
    kwargs_.update(kwargs)
    kwargs_['modelIndex'] = -1
    se.extractRealSaccades(
        *args, **kwargs
    )

    return

# def characterizeSaccades(outfile_h5, hz=200):
#     ''' Basic characterization of saccades
#     '''
#     onset_inds = outfile_h5['saccades/onsets'][:].astype('int')
#     offset_inds = outfile_h5['saccades/offsets'][:].astype('int')
#     durs = (offset_inds) - onset_inds) * (1/hz)
    
#     return vels, amps, durs, freq

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('home', type=str, help='Home folder for the session')
    #parser.add_argument('is_crystal', type=int, help='0 - file has LJ for timestamping. 1 - Crystals data, keep in frame clock')
    namespace = parser.parse_args()
    fileSets = collectFileSets(namespace.home)
    config = locateSaccadeExtractionProject()
    
    # Only use the most recent pose estimates for left and right cameras
    # Slightly different from pose extraction since these are a list of tuples
    recent_files = sorted(fileSets, key=lambda x: x[0].stat().st_mtime, reverse=True)
    # Get most recent for each camtype
    left_cam_dlc  = next((f for f in recent_files if 'leftCam' in f[0].name), None)
    right_cam_dlc = next((f for f in recent_files if 'rightCam' in f[0].name), None)
    if left_cam_dlc is None and right_cam_dlc is None:
        print('No pose estimates found for left or right cameras.')
        exit(-1)
    fileSets = [left_cam_dlc, right_cam_dlc]
    fileSets = [fs for fs in fileSets if fs is not None]  # Filter out None values

    outfile = h5py.File(os.path.join(namespace.home, 'results.h5'), 'a')

    # Extract the cleaned up pose estimates from the fileSets.
    # This is done in saccade_extraction.pose.loadEyePosition
    for f in fileSets:
        processed, frameTimestamps = se.pose.loadEyePosition(
            f[0],
            f[1],
            likelihoodThreshold=0.00
        )
        #code.interact(local=dict(globals(), **locals()))
        # Check processed is valid
        if processed is None or frameTimestamps is None:
            print(f'Invalid pose estimates in {f}. Skipping.')
            continue
        # Save to correct group in outfile to match left or right camera
        if 'leftCam' in f[0].name:
            #pose_group = outfile.create_group('pose/left')
            pose_group = outfile['pose/left'] if 'pose/left' in outfile else outfile.create_group('pose/left')
        elif 'rightCam' in f[0].name:
            pose_group = outfile['pose/right'] if 'pose/right' in outfile else outfile.create_group('pose/right')
        else:
            pose_group = outfile['pose/unknown'] if 'pose/unknown' in outfile else outfile.create_group('pose/unknown')
        pose_group.create_dataset('projections', data=processed)
        pose_group.create_dataset('timestamps', data=frameTimestamps)
        outfile.flush()

    # Check for previous saccade extraction results
    prev_saccades = glob(os.path.join(namespace.home, 'videos','*saccades.hdf'))
    if len(prev_saccades) > 0:
        print('Previous saccade extraction results found. Overwriting these results.')
        for prev_saccade in prev_saccades:
            os.remove(prev_saccade)

    # Continue with saccade extraction
    #with PrintSuppressor():
    extractSaccades(config, fileSets)

    saccade_results = glob(os.path.join(namespace.home, 'videos', '*saccades.hdf'))
    
    # Remove previous result if present
    if 'saccades' in outfile:
        del outfile['saccades']
        outfile.flush()

    for saccade_result in saccade_results:
        saccade_data = h5py.File(saccade_result, 'r')
        # Check if the file has the expected structure
        if 'saccade_onset' not in saccade_data or 'saccade_offset' not in saccade_data:
            continue
        # Need to check if it comes from leftcam or rightcam.
        # Place in saccades/left or saccades/right
        if 'leftCam' in saccade_result:
            sacc_group = outfile.create_group('saccades/left')
        elif 'rightCam' in saccade_result:
            sacc_group = outfile.create_group('saccades/right')
        else:
            continue

        # # Get only the real ones
        true_saccades = np.logical_not(np.isnan(saccade_data['saccade_onset'][:]))

        sacc_group.create_dataset('labels', data=saccade_data['saccade_labels'][:])
        sacc_group.create_dataset('labels_coded', data=saccade_data['saccade_labels_coded'][:])
        sacc_group.create_dataset('onsets', data = saccade_data['saccade_onset'][:])
        sacc_group.create_dataset('offsets', data = saccade_data['saccade_offset'][:])
        sacc_group.create_dataset('waveforms', data= saccade_data['saccade_waveforms'][:])
        outfile.flush()

    # Answers are given without subframe precision (values calculated from nearest frame index)
    outfile.close()
    saccade_data.close()
    print('Saccade extraction completed. Results saved to results.h5.')