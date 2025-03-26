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
conda init

#
RETURN_DIRECTORY=$(pwd)
cd /home/$USER/Code/data-processing

# Extract pose estimates
log "INFO" "Extracting pose estimates"
conda activate deeplabcut
python ./scripts/extract_pose.py "$HOME_FOLDER"
conda deactivate

# Extract real saccades
log "INFO" "Extracting real saccades"
conda activate se
python ./scripts/extract_saccades.py "$HOME_FOLDER"
conda deactivate

#
cd $RETURN_DIRECTORY
exit 0