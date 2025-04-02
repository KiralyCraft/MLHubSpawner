#!/bin/bash

# Check if the script is being sourced
(return 0 2>/dev/null)
if [[ $? -ne 0 ]]; then
    echo "This script must be sourced, not executed."
    echo "Use: run=true source $0"
    exit 1
fi

# Check for the 'run' flag
if [[ "$run" != "true" ]]; then
    echo "To execute the installation, run the following command:"
    echo "run=true source $BASH_SOURCE"
    return
fi

# Define target venv path
VENV_PATH="$HOME/venv"

# Create virtual environment if it doesn't exist
if [[ ! -d "$VENV_PATH" ]]; then
    echo "Creating virtual environment at $VENV_PATH..."
    python3 -m venv --system-site-packages "$VENV_PATH"
else
    echo "Virtual environment already exists at $VENV_PATH"
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Set pip cache location
export XDG_CACHE_HOME="$CACHE_PATH"
mkdir -p "$XDG_CACHE_HOME"

# Register IPython kernel
python -m ipykernel install --user --name venv

echo "Setup complete. Virtual environment is at $VENV_PATH"
