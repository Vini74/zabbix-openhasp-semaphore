#!/bin/bash
# Wrapper script for running semafor.py with environment variables
# Make this script executable: chmod +x run_semafor.sh

# Set the working directory to the script's directory
cd "$(dirname "$0")"

# Load environment variables from .env file
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi

# Run the Python script
python3 semafor.py