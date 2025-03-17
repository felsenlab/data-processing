#!/bin/bash

# Check if a positional argument is provided
if [ $# -lt 1 ]; then
    echo "Usage: $0 <argument>"
    exit 1
fi

# Store the first positional argument
home_folder=$1

# Extract pose estimates
conda activate rtdlc
python -m extract_pose home_folder
conda deactivate

# Extract real saccades
conda actiate se
python -m extract_saccades home_folder
conda deactiate