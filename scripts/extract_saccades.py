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

def compute_frame_timestamps_for_crystals_sessions(
    home_folder,
    side='right',
    lag=-4.37
    ):
    """
    """

    home_folder = pl.Path(home_folder)
    timestamp_files = list(home_folder.joinpath('videos').rglob('*_timestamps.txt'))
    frameTimestamps = None
    for f in timestamp_files:
        if side in f.name.lower():

            # Load inter-frame intervals for the target camera
            ifi = np.loadtxt(f)
            frameTimestamps = np.concatenate([
                np.array([0]),
                np.cumsum(ifi[1:]) / 1000000000
            ])

            # Identify the first visual stimulus timestamp
            t0 = None
            for f in home_folder.joinpath('videos').iterdir():
                if f.stem.lower() == 'driftinggratingmetadata':
                    with open(f, 'r') as stream:
                        lines = stream.readlines()[5:]
                    a, b, c, d, e = lines[0].rstrip('\n').split(', ')
                    t0 = float(e)
            if t0 is None:
                raise Exception('Could not identify timestamp for the first visual event')
            
            # Add the timestamp of the first visual event + the constant lag
            frameTimestamps = frameTimestamps + t0 + lag

    #
    if frameTimestamps is None:
        raise Exception('Could not compute frame timestamps')

    return frameTimestamps

def align_saccades_to_LJ(homeFolder, outfile, lj_combined_file, namespace):
    """
    Align saccades to the LabJack timestamps.
    This is done by finding the nearest frame timestamp to each saccade onset and offset.
    """

    if namespace.processing_path == 0 or namespace.processing_path == 1:
        lj_data = np.load(lj_combined_file)
        frame_signal = lj_data[:,7]

        # Synchronization for frames
        frame_edge_inds = np.where(np.diff(frame_signal) != 0)[0] + 1
        frame_times = lj_data[frame_edge_inds,0]
        # Convert to seconds since 
    else:
        # namespace.processing_path = 2, so this is a Crystal session
        frame_times = compute_frame_timestamps_for_crystals_sessions(homeFolder)

    # Placing within outfile
    pose_group = outfile['pose/right']
    dataset_name = 'frametimes_clock'
    if dataset_name in pose_group:
        print(f"Warning: Dataset '{dataset_name}' already exists. Overwriting...")
        del pose_group[dataset_name]  # Delete existing dataset

    # Create the new dataset in the pose_dlc group
    pose_group.create_dataset(dataset_name, data=frame_times)

    # Align saccades to nearest frame
    if 'saccades' in outfile:
        saccades_group = outfile['saccades/right'] if 'right' in outfile['saccades'] else outfile['saccades/left']
        sacc_onsets = saccades_group['onsets'][:].astype('int')
        sacc_offsets = saccades_group['offsets'][:].astype('int')

        # sacc_onsets are the indices of the saccade onsets in the frame time.
        # Align each frame index to the nearest frame time (found in frame_times)
        frame_numbers = np.arange(len(frame_times))
        if namespace.processing_path in [0, 1]:
            sacc_onset_indices  = np.interp(sacc_onsets,  frame_numbers, frame_edge_inds).astype('int')
            sacc_offset_indices = np.interp(sacc_offsets, frame_numbers, frame_edge_inds).astype('int')
            sacc_onset_seconds = frame_times[sacc_onset_indices]
            sacc_offset_seconds = frame_times[sacc_offset_indices]
        else:
            sacc_onset_seconds = np.interp(sacc_onsets, frame_numbers, frame_times)
            sacc_offset_seconds = np.interp(sacc_offsets, frame_numbers, frame_times)

        # Sve the aligned saccade onsets and offsets
        saccades_group.create_dataset('saccade_onsets_seconds',  data=sacc_onset_seconds)
        saccades_group.create_dataset('saccade_offsets_seconds', data=sacc_offset_seconds)
    
        outfile.flush()
    else:
        print('No saccades found in outfile to align to LabJack timestamps. Skipping alignment.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('home', type=str, help='Home folder for the session')
    parser.add_argument('processing_path', type=int, help='0 - Session w/ labjack, ephys. 1 - Session w/ labjack, ephys, strai gauge. 2 - Crystals data, keep in frame clock')
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
            #code.interact(local=dict(globals(), **locals()))
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

        # Align saccades to LabJack timestamps if LJ exists
        lj_dir = os.path.join(namespace.home, 'labjack')
        lj_file_maybe = glob(os.path.join(lj_dir, 'labjack_combined*.npy'))
        if namespace.processing_path in [0, 1]:
            lj_combined_file = max(lj_file_maybe, key=os.path.getmtime)
        else:
            lj_combined_file = None
        align_saccades_to_LJ(namespace.home, outfile, lj_combined_file, namespace)



    # Answers are given without subframe precision (values calculated from nearest frame index)
    outfile.close()
    saccade_data.close()
    print('Saccade extraction completed. Results saved to results.h5.')