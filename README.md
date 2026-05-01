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
3. On Wayland, the default backend uses Python `evdev` and `/dev/uinput` for high-resolution scrolling.
4. Make the scripts executable if your checkout did not preserve permissions:
   ```bash
   chmod +x run_eyebrow_scroll.sh manual_hires_scroll_probe.py diagnose_livelink.py
   ```
   This is only needed once per checkout, not every time you run the tool. If you run via `python script.py`, executable permissions are not required.
5. Check `/dev/uinput` permissions on Wayland:
   ```bash
   test -w /dev/uinput && echo "uinput writable"
   ```
   If this does not print `uinput writable`, allow your user to access uinput according to your distro's udev/input group instructions, then log out and back in or reboot.
6. Run the script:
   ```bash
   ./run_eyebrow_scroll.sh
   ```
   This creates `.venv` if needed, installs Python dependencies into it, and starts the app. The virtualenv is reused on later runs; dependency installation is safe to repeat.

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

To tune the eyebrow dead zone and sensitivity:
```bash
./run_eyebrow_scroll.sh --scroll-threshold 0.06 --scroll-speed 1.5
```

Lower `--scroll-threshold` makes scrolling start with smaller eyebrow movement. Higher `--scroll-speed` makes the same movement scroll faster. Defaults are intentionally moderate: `--scroll-threshold 0.08 --scroll-speed 1.0`.

To make the slowest possible scroll creep more gently on Linux/Wayland:
```bash
./run_eyebrow_scroll.sh --min-scroll-rate 0.02
```

`--min-scroll-rate` is measured in wheel detents per second and defaults to `0.03` for the Wayland backend. Set it lower for a slower crawl after crossing the dead zone. Set `--max-scroll-rate` lower if strong eyebrow movement is too fast. The default maximum is `18.0`.

On Linux, backend selection is automatic. On Wayland, `auto` uses the single `uinput-hires` backend. You can also choose explicitly:
```bash
python jm_eyebrow_scroll.py --scroll-backend uinput-hires
python jm_eyebrow_scroll.py --scroll-backend xtest
```

For high-resolution Linux wheel checks, first make sure dependencies are installed:
```bash
./run_eyebrow_scroll.sh --help
```

Then focus a scrollable Wayland window and run:
```bash
./.venv/bin/python manual_hires_scroll_probe.py
```

The high-resolution probe sends `REL_WHEEL_HI_RES` values smaller than one normal wheel click. If the default probe does not move anything, try:
```bash
./.venv/bin/python manual_hires_scroll_probe.py --compat-detents
```

If `--compat-detents` moves but the default probe does not, the compositor/app is falling back to ordinary wheel clicks and is not using true high-resolution scrolling from this virtual device.

Some apps, especially terminals, may use the fallback `REL_WHEEL` clicks instead of the high-resolution values. That can feel fast or chunky even when editors like Sublime Text scroll smoothly. The default fallback is throttled to one legacy click per `48000` high-resolution units.

The app intentionally has one Wayland profile now. Tune it with rates instead of switching profiles:
```bash
./run_eyebrow_scroll.sh --max-scroll-rate 2
./run_eyebrow_scroll.sh --max-scroll-rate 1 --scroll-speed 0.5
```

On Wayland this is the default when `/dev/uinput` is writable, so normally this is enough:
```bash
./run_eyebrow_scroll.sh
```

If terminal scrollback still jumps multiple rows per wheel event, reduce the terminal emulator's wheel scroll multiplier or scrollback multiplier. For Ghostty, create or edit `~/.config/ghostty/config` and try:
```ini
mouse-scroll-multiplier = precision:0.01,discrete:0.333333
```

Restart Ghostty after changing the config. `discrete:0.333333` compensates for terminals that still receive about three wheel events per input pulse. `precision:0.01` slows high-resolution/trackpad-like input. This keeps the app using standard wheel/high-resolution scroll input while letting the terminal decide how many text rows one scroll step should mean.

Automated core tests:
```bash
python -m unittest discover
```

To check whether Live Link Face data is reaching this machine before testing scrolling:
```bash
./.venv/bin/python diagnose_livelink.py --seconds 30
```

The iPhone should target this machine's IP address and UDP port `11111` unless you pass a different `--port`.

## How it Works

- Raise eyebrows to scroll up
- Lower eyebrows to scroll down
- The more you move your eyebrows, the faster it scrolls

## Requirements

- Python 3.11 or higher
- LiveLink Face tracking app
- Windows: uses Win32 mouse wheel events (pywin32)
- macOS: uses Quartz scroll events (pyobjc)
- Linux X11: uses python-xlib/XTest wheel events
- Linux Wayland: uses uinput high-resolution wheel events

## License

GPL
