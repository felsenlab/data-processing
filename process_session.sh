#!/bin/bash

# Check if a positional argument is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <argument>"
    exit 1
fi

# Store the first positional argument
home_folder=$1

#
cd /home/polegpolskylab/Code/data-processing

# Extract pose estimates
conda activate rtdlc
python ./scripts/extract_pose.py home_folder
conda deactivate

# Extract real saccades
conda activate se
python ./scripts/extract_saccades.py home_folder
conda deactivate