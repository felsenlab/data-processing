#!/bin/bash

# Check if a positional argument is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <argument>"
    exit 1
fi

# Assign the home folder to a variable
home_folder=$1

# Define logging function
log_file="${home_folder%/}/log.txt"
log() {
    local level=$1
    shift
    local message="[$(date '+%Y-%m-%d, %H:%M:%S')] $level: $*"
    echo "$message" | tee -a "$log_file"
}

# Initialize conda
source /home/polegpolskylab/anaconda3/etc/profile.d/conda.sh

#
cd /home/polegpolskylab/Code/data-processing

# Extract pose estimates
log "INFO" "Extracting pose estimates"
conda activate rtdlc
python ./scripts/extract_pose.py "$home_folder"
conda deactivate

# Extract real saccades
log "INFO" "Extracting real saccades"
conda activate se
python ./scripts/extract_saccades.py "$home_folder"
conda deactivate