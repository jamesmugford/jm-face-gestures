@echo off
setlocal

cd /d "%~dp0"

echo Setting up Face Gesture Scroll...

if not exist ".venv" (
    echo Creating virtual environment...
    py -3 -m venv .venv || exit /b 1
)

call .venv\Scripts\activate.bat || exit /b 1

echo Installing requirements...
python -m pip install -r requirements.txt || exit /b 1

echo Starting Face Gesture Scroll...
python -u jm_eyebrow_scroll.py %*
