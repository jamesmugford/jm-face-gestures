#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "Setting up Face Gestures..."

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    if ! python3 -m venv .venv; then
        echo "Failed to create .venv."
        echo "On Debian/Ubuntu, install python3-venv and try again:"
        echo "  sudo apt install python3-venv"
        exit 1
    fi
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing requirements..."
python -m pip install -r requirements.txt

echo "Starting Face Gestures..."
python -u -m face_gestures "$@"
