# Face Gestures

Control your computer (Windows, Mac and Linux) with face gestures. 

Currently uses iPhone with Face ID for the sensing technology, but Android devices may be added soon.

First usecase supported: scrolling with your eyebrows. 

Uses LiveLink Face tracking to enable hands-free scrolling through eyebrow movements.

## Quick Start

### Windows Users
1. Download this repository
2. Double-click `run_eyebrow_scroll.bat`

### Linux Users
1. Download this repository
2. Open terminal in the repository folder
3. Make the script executable:
   ```bash
   chmod +x run_eyebrow_scroll.sh
   ```
4. Run the script:
   ```bash
   ./run_eyebrow_scroll.sh
   ```
   This creates a virtualenv and installs dependencies (including python-xlib).

## Usage

1. Start your LiveLink Face tracking app (e.g., on iPhone)
2. Run the tool via Python:
```bash
python jm_eyebrow_scroll.py
```

Or with a custom UDP port:
```bash
python jm_eyebrow_scroll.py --port 12345
```

## How it Works

- Raise eyebrows to scroll up
- Lower eyebrows to scroll down
- The more you move your eyebrows, the faster it scrolls

## Requirements

- Python 3.6 or higher
- LiveLink Face tracking app
- Platform-specific notes:
  - Windows: uses Win32 mouse wheel events (pywin32)
  - macOS: uses Quartz scroll events (pyobjc)
  - Linux (X11): uses python-xlib to emit wheel events (installed via pip)

## License

GPL
