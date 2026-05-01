# Face Gestures

Eyebrow-controlled smooth scrolling using an iPhone running Live Link Face.

Linux Wayland is the primary target and uses `/dev/uinput` high-resolution wheel events. Windows and macOS use standard OS wheel/scroll APIs through optional dependencies.

## Requirements

- Python 3.11 or newer
- Live Link Face sending UDP packets to this machine
- Linux: `/dev/uinput` access for the current user
- Windows: `pywin32`, installed by `requirements.txt`
- macOS: Quartz from PyObjC, installed by `requirements.txt`

## Setup

Install dependencies and start the app:

```bash
./run_eyebrow_scroll.sh
```

The script creates `.venv` if needed, installs `requirements.txt`, and runs `jm_eyebrow_scroll.py` inside the virtualenv.

On Windows, run:

```bat
run_eyebrow_scroll.bat
```

If `/dev/uinput` is not writable, configure your distro's uinput permissions or add your user to the appropriate input/uinput group, then log out and back in.

## Live Link

Set Live Link Face to send to this machine's IP address on UDP port `11111`.

Check packet arrival before testing scrolling:

```bash
./.venv/bin/python diagnose_livelink.py --seconds 30
```

Use a custom port if needed:

```bash
./run_eyebrow_scroll.sh --port 12345
```

## Tuning

Raise eyebrows to scroll up. Lower eyebrows to scroll down. Larger brow movement scrolls faster.

Lower the dead zone for smaller eyebrow movements:

```bash
./run_eyebrow_scroll.sh --scroll-threshold 0.06
```

Increase or reduce sensitivity:

```bash
./run_eyebrow_scroll.sh --scroll-speed 1.5
./run_eyebrow_scroll.sh --max-scroll-rate 4
```

The default slow crawl starts at `0.03` wheel detents per second and tops out at `18.0` detents per second.

Some terminals multiply wheel input into several text rows. Tune that in the terminal rather than changing this app's input method. For Ghostty:

```ini
mouse-scroll-multiplier = precision:0.01,discrete:0.333333
```

## Development

Run tests:

```bash
python -m unittest discover
```

Run the CLI help:

```bash
python jm_eyebrow_scroll.py --help
```

## License

GPL
