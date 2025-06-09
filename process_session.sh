#!/bin/bash

# Check if a positional argument is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <argument>"
    exit 1
fi

# Assign the home folder to a variable
HOME_FOLDER=$1

# Define logging function
LOG_FILE="${HOME_FOLDER%/}/log.txt"
log() {
    local LEVEL=$1
    shift
    local MESSAGE="[$(date '+%Y-%m-%d, %H:%M:%S')] $LEVEL: $*"
    echo "$MESSAGE" | tee -a "$LOG_FILE"
}

# Initialize conda
source /home/$USER/miniconda3/etc/profile.d/conda.sh

#
RETURN_DIRECTORY=$(pwd)
#cd /home/$USER/Code/data-processing
cd /home/schollab-dion/Documents/felsen_pipeline/data-processing

# Initialize outfile for session
log "INFO" "Initializing output .hdf5 file"
conda activate genwork
python ./scripts/init_outfile.py "$HOME_FOLDER"
conda deactivate

# #####
# Extract pose estimates
log "INFO" "Extracting pose estimates"
#conda activate deeplabcut
conda activate deeplabcut
python ./scripts/extract_pose.py "$HOME_FOLDER"
conda deactivate

# Extract real saccades
log "INFO" "Extracting real saccades"
conda activate se
python ./scripts/extract_saccades.py "$HOME_FOLDER"
conda deactivate

# Extract and consolidate LabJack .dat files
log "INFO" "Consolidating LabJack data"
conda activate genwork
python ./scripts/combine_LJ_data.py "$HOME_FOLDER"
conda deactivate

# Extract barcodes from LabJack
log "INFO" "Extracting barcodes from LabJack"
conda activate genwork
python ./scripts/extract_barcodes.py "$HOME_FOLDER" 0
conda deactivate

# Extract barcodes from NeuroPixel, 
log "INFO" "Extracting barcodes from NeuroPixel device"
conda activate genwork
python ./scripts/extract_barcodes.py "$HOME_FOLDER" 1
conda deactivate

# Align NPX clock and spikes to LabJack time
log "INFO" "Aligning NeuroPixel events to LabJack time"
conda activate genwork
python ./scripts/align_npx_to_LJ.py "$HOME_FOLDER"
conda deactivate

# # Timestamp frames and saccade onsets-offsets from eye camera
# # 0 - data has labjack
# # 1 - Crystal's data, keep things in frametimes
# log "INFO" "Aligning pose frametimes and saccade onsets/offsets to nearest LJ time index"
# conda activate genwork
# python ./scripts/align_frames.py "$HOME_FOLDER" 1
# conda deactivate

# ## Not yet implemented
# # # Timestamp stimulus information
# # log "INFO" "Timestamping stimulus information"
# # conda activate genwork
# # python ./scripts/extract_stimulus_timing.py "$HOME_FOLDER"
# # conda deactivate

#
cd $RETURN_DIRECTORY
exit 0