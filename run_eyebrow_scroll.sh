#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Setting up Eyebrow Scroll..."

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    if ! python3 -m venv .venv; then
        echo "Failed to create .venv."
        echo "On Debian/Ubuntu, install python3-venv and try again:"
        echo "  sudo apt install python3-venv"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Install requirements
echo "Installing requirements..."
python -m pip install -r requirements.txt

# Start the application
echo "Starting Eyebrow Scroll..."
python -u jm_eyebrow_scroll.py "$@"
