# Face Gestures

Generic face-signal controls for smooth scrolling. The default input source is Live Link Face over UDP, but the public API works in terms of named signals and scroll mappings.

```python
from face_gestures import GestureControl, Scroll

GestureControl().scroll(
    Scroll.vertical(
        up="brows_up",
        down="brows_down",
        threshold=0.13,
        speed=2.0,
    )
).run()
```

`brows_up` and `brows_down` are logical aliases over the raw ARKit/Live Link brow blendshapes. Raw signal names like `jaw_open`, `mouth_smile_left`, and `eye_blink_right` are also available.

## Requirements

- Python 3.11 or newer
- Live Link Face sending UDP packets to this machine
- Linux: `/dev/uinput` access for the current user
- Windows: `pywin32`, installed by `requirements.txt`
- macOS: Quartz from PyObjC, installed by `requirements.txt`

Linux Wayland is the primary target and uses `/dev/uinput` high-resolution wheel events. Windows and macOS use standard OS scroll APIs through optional dependencies.

## Linux Setup

The Linux output uses `python-evdev`, which opens `/dev/uinput` read-write. Make sure your user is in the `input` group:

```bash
sudo usermod -aG input "$USER"
```

Log out and back in after changing groups.

Some systems ship a `/dev/uinput` rule with group write-only permissions, such as `0620`. That is not enough for `python-evdev`. Add a local udev rule that grants read-write access to the `input` group:

```bash
sudo tee /etc/udev/rules.d/99-uinput-evdev.rules >/dev/null <<'EOF'
KERNEL=="uinput", GROUP="input", MODE="0660", OPTIONS+="static_node=uinput"
EOF

sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=misc --sysname-match=uinput
```

Verify access:

```bash
stat -c '%n %a %U %G %A' /dev/uinput
id
```

`/dev/uinput` should show group `input` with read-write permissions, for example `660 root input crw-rw----`.

## Firewall

Live Link Face sends tracking data over UDP port `11111`. Allow that port through the local firewall.

With UFW:

```bash
sudo ufw allow 11111/udp
```

With firewalld:

```bash
sudo firewall-cmd --permanent --add-port=11111/udp
sudo firewall-cmd --reload
```

## Run

Install dependencies and start the default brow scroll mapping:

```bash
./run_face_gestures.sh
```

On Windows:

```bat
run_face_gestures.bat
```

The scripts create `.venv` if needed, install `requirements.txt`, and run `python -m face_gestures` inside the virtualenv.

You can also run the module directly:

```bash
python -m face_gestures scroll
```

After installing the package, the console command is available too:

```bash
face-gestures scroll
```

Set Live Link Face to send to this machine's IP address on UDP port `11111`.

Check packet arrival before testing scrolling:

```bash
./.venv/bin/python diagnose_livelink.py --seconds 30
```

## CLI Tuning

Use another signal mapping without writing Python:

```bash
./run_face_gestures.sh scroll --up-signal mouth_smile --down-signal jaw_open
```

Adjust dead zone and sensitivity:

```bash
./run_face_gestures.sh scroll --scroll-threshold 0.06 --scroll-speed 2.5
```

Adjust pacing:

```bash
./run_face_gestures.sh scroll --min-scroll-rate 0.02 --max-scroll-rate 4
```

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
python -m face_gestures scroll --help
```

## License

GPL
