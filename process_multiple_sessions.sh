#!/bin/bash

# Check if correct number of arguments provided
if [ $# -ne 2 ]; then
    echo "Usage: $0 <text_file> <integer_flag>"
    echo "Example: $0 file_paths.txt 1"
    exit 1
fi

TEXT_FILE="$1"
INTEGER_FLAG="$2"

# Check if text file exists
if [ ! -f "$TEXT_FILE" ]; then
    echo "Error: File '$TEXT_FILE' not found!"
    exit 1
fi

# Check if integer flag is actually an integer
if ! [[ "$INTEGER_FLAG" =~ ^-?[0-9]+$ ]]; then
    echo "Error: Second argument '$INTEGER_FLAG' is not an integer!"
    exit 1
fi

# Check if process_session.sh exists and is executable
if [ ! -x "./process_session.sh" ]; then
    echo "Error: './process_session.sh' not found or not executable!"
    echo "Make sure process_session.sh is in the current directory and has execute permissions."
    exit 1
fi

echo "Processing file: $TEXT_FILE"
echo "Integer flag: $INTEGER_FLAG"
echo "Starting batch processing..."
echo

# Read each line from the text file
line_count=0
while IFS= read -r file_path || [ -n "$file_path" ]; do
    # Skip empty lines
    if [ -z "$file_path" ]; then
        continue
    fi
    
    line_count=$((line_count + 1))
    echo "[$line_count] Processing: $file_path"
    
    # Call process_session.sh with file_path as first arg, integer as second arg
    ./process_session.sh "$file_path" "$INTEGER_FLAG"
    
    # Check if the process_session.sh command succeeded
    if [ $? -eq 0 ]; then
        echo "[$line_count] Success: $file_path"
    else
        echo "[$line_count] Failed: $file_path (exit code: $?)"
    fi
    
    echo # Empty line for readability
    
done < "$TEXT_FILE"

echo "Batch processing completed. Processed $line_count lines."