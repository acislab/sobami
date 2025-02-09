#!/bin/bash

# Print Python version
echo "Python version:"
python --version

# Print pip version
echo -e "\nPip version:"
pip --version

# List all installed pip packages
echo -e "\nInstalled pip packages:"
pip list

# Add a separator for clarity
echo -e "\nStarting Ray Serve application...\n"

# Run the original command
serve run ml_serve:entrypoint
