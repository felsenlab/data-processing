#!/bin/bash

# Check if a positional argument is provided
if [ $# -lt 2 ]; then
    echo "Usage: $0 <argument> <numerical_flag>"
    exit 1
fi

# Assign the home folder to a variable
HOME_FOLDER=$1
PROCESSING_PATH=$2

# Validate that second argument is numerical
if ! [[ "$PROCESSING_PATH" =~ ^[0-2]+$ ]]; then
    echo "Error: Second arg options : 0 - asdf, 1 - asdf, 2 - asdf"
    exit 1
fi

# Define logging function
LOG_FILE="${HOME_FOLDER%/}/log.txt"
log() {
    local LEVEL=$1
    shift
    local MESSAGE="[$(date '+%Y-%m-%d, %H:%M:%S')] $LEVEL: $*"
    echo "$MESSAGE" | tee -a "$LOG_FILE"
}

# Initialize conda
#source /home/schollab-dion/miniconda3/condabin/conda.sh
# source /home/schollab-dion/miniconda3/bin/conda.sh

source /home/schollab-dion/miniconda3/etc/profile.d/conda.sh

#
RETURN_DIRECTORY=$(pwd)
cd /home/$USER/Code/data-processing
# cd /home/schollab-dion/Documents/felsen_pipeline/data-processing

# Initialize outfile for session
log "INFO" "Initializing output .hdf5 file"
conda activate genwork
python ./scripts/init_outfile.py "$HOME_FOLDER"
conda deactivate

# #####
# # Extract pose estimates
log "INFO" "Extracting pose estimates"
conda activate deeplabcut
python ./scripts/extract_pose.py "$HOME_FOLDER" "$PROCESSING_PATH" 
conda deactivate

# Extract real saccades
log "INFO" "Extracting real saccades"
conda activate se
python ./scripts/extract_saccades.py "$HOME_FOLDER" "$PROCESSING_PATH"
conda deactivate

# Extract and consolidate LabJack .dat files
log "INFO" "Consolidating LabJack data"
conda activate genwork
python ./scripts/combine_LJ_data.py "$HOME_FOLDER" "$PROCESSING_PATH"
conda deactivate

# Extract barcodes from LabJack
log "INFO" "Extracting barcodes from LabJack"
conda activate genwork
python ./scripts/extract_barcodes.py "$HOME_FOLDER" 0 "$PROCESSING_PATH"
conda deactivate

# Extract barcodes from NeuroPixel, 
log "INFO" "Extracting barcodes from NeuroPixel device"
conda activate genwork
python ./scripts/extract_barcodes.py "$HOME_FOLDER" 1 "$PROCESSING_PATH"
conda deactivate

# Align NPX clock and spikes to LabJack time
log "INFO" "Aligning NeuroPixel events to LabJack time"
conda activate genwork
python ./scripts/align_npx_to_LJ.py "$HOME_FOLDER" "$PROCESSING_PATH"
conda deactivate



# # Not yet implemented
# # Timestamp stimulus information
# log "INFO" "Timestamping stimulus information"
# conda activate genwork
# python ./scripts/extract_stimulus_timing.py "$HOME_FOLDER"
# conda deactivate

#
cd $RETURN_DIRECTORY
exit 0
