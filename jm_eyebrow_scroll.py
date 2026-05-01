import argparse
import importlib.util
import os
import socket
import sys
import time
from dataclasses import dataclass

from scroll_core import (
    BrowSignals,
    ScrollConfig,
    combine_brow_movement,
    scroll_amount_from_movement,
)

DEFAULT_UDP_PORT = 11111
DEFAULT_SCROLL_CONFIG = ScrollConfig()
SCROLL_THRESHOLD = DEFAULT_SCROLL_CONFIG.threshold
SCROLL_SPEED = DEFAULT_SCROLL_CONFIG.speed
MAX_SCROLL = DEFAULT_SCROLL_CONFIG.max_scroll

_linux_scroller = None
_linux_scroller_backend = None


class NullScroller:
    def set_amount(self, amount: float) -> None:
        pass

    def stop(self) -> None:
        pass


@dataclass(frozen=True)
class LinuxScrollConfig:
    min_detents_per_second: float = 0.03
    max_detents_per_second: float = 18.0
    compat_detent_units: int = 48000


DEFAULT_LINUX_SCROLL_CONFIG = LinuxScrollConfig()


def _is_wayland_session() -> bool:
    return (
        os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        or "WAYLAND_DISPLAY" in os.environ
    )


def _python_module_available(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def _can_use_uinput_hires() -> bool:
    return _python_module_available("evdev") and os.access("/dev/uinput", os.W_OK)


def _select_linux_backend(preferred_backend: str) -> str:
    if preferred_backend != "auto":
        return preferred_backend

    if _is_wayland_session():
        if _can_use_uinput_hires():
            return "uinput-hires"
        raise RuntimeError(
            "Wayland smooth scrolling requires python-evdev and write access "
            "to /dev/uinput. Run `pip install -r requirements.txt` and check "
            "your uinput permissions."
        )

    if os.environ.get("DISPLAY"):
        return "xtest"

    if _can_use_uinput_hires():
        return "uinput-hires"

    raise RuntimeError(
        "No Linux scroll backend available. "
        "Install uinput dependencies for Wayland or use X11/XTest."
    )


def _create_linux_scroller(
    backend: str,
    config: LinuxScrollConfig = DEFAULT_LINUX_SCROLL_CONFIG,
):
    if backend == "uinput-hires":
        from uinput_hires_scroller import create_uinput_hires_scroller

        return create_uinput_hires_scroller(
            compat_detents=True,
            compat_detent_units=config.compat_detent_units,
            min_detents_per_second=config.min_detents_per_second,
            max_detents_per_second=config.max_detents_per_second,
        )

    if backend == "xtest":
        from xtest_wheel_pacer import XTestWheelPacer

        return XTestWheelPacer(
            min_rate=4.0,
            max_rate=40.0,
            ease_power=2.2,
            hysteresis=0.01,
            max_ticks_per_flush=6,
            flush_hz=50,
            max_input=1.0,
        )

    if backend == "none":
        return NullScroller()

    raise RuntimeError(f"Unknown Linux scroll backend: {backend}")


def _get_linux_scroller(
    preferred_backend: str = "auto",
    config: LinuxScrollConfig = DEFAULT_LINUX_SCROLL_CONFIG,
):
    global _linux_scroller, _linux_scroller_backend

    backend = _select_linux_backend(preferred_backend)
    if _linux_scroller is None:
        _linux_scroller = _create_linux_scroller(backend, config)
        _linux_scroller_backend = backend
        print(f"Using Linux scroll backend: {backend}")
    elif preferred_backend != "auto" and backend != _linux_scroller_backend:
        raise RuntimeError(
            "Linux scroll backend is already "
            f"{_linux_scroller_backend!r}, not {backend!r}"
        )

    return _linux_scroller


def _stop_linux_scroller() -> None:
    global _linux_scroller, _linux_scroller_backend

    if _linux_scroller is None:
        return

    _linux_scroller.stop()
    _linux_scroller = None
    _linux_scroller_backend = None


def smooth_scroll(
    amount: float,
    backend: str = "auto",
    backend_config: LinuxScrollConfig = DEFAULT_LINUX_SCROLL_CONFIG,
) -> None:
    """
    Platform-specific scroll implementation.

    Linux backends are paced in a background thread, so zero amounts are passed
    through after scrolling starts to stop any previously buffered movement.
    """
    amount = float(amount)

    if sys.platform == "win32":
        if amount != 0.0:
            import win32api
            import win32con

            win32api.mouse_event(
                win32con.MOUSEEVENTF_WHEEL,
                0,
                0,
                int(amount * 120),
                0,
            )
    elif sys.platform == "darwin":
        if amount != 0.0:
            import Quartz

            scroll_unit = amount * 5
            event = Quartz.CGEventCreateScrollWheelEvent(
                None, Quartz.kCGScrollEventUnitLine, 1, int(scroll_unit)
            )
            Quartz.CGEventPost(Quartz.kCGHIDEventTap, event)
    else:
        if amount == 0.0 and _linux_scroller is None:
            return
        scroller = _get_linux_scroller(backend, backend_config)
        scroller.set_amount(amount)


def _load_livelinkface():
    try:
        from pylivelinkface import FaceBlendShape, PyLiveLinkFace
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "pylivelinkface is not installed. Run `pip install -r requirements.txt`."
        ) from exc

    return FaceBlendShape, PyLiveLinkFace


def _brow_signals_from_live_link(live_link_face, face_blend_shape) -> BrowSignals:
    get_blendshape = live_link_face.get_blendshape
    return BrowSignals(
        brow_down_left=get_blendshape(face_blend_shape.BrowDownLeft),
        brow_down_right=get_blendshape(face_blend_shape.BrowDownRight),
        brow_inner_up=get_blendshape(face_blend_shape.BrowInnerUp),
        brow_outer_up_left=get_blendshape(face_blend_shape.BrowOuterUpLeft),
        brow_outer_up_right=get_blendshape(face_blend_shape.BrowOuterUpRight),
    )


def start_face_tracking(
    port: int = DEFAULT_UDP_PORT,
    scroll_backend: str = "auto",
    scroll_config: ScrollConfig = DEFAULT_SCROLL_CONFIG,
    linux_scroll_config: LinuxScrollConfig = DEFAULT_LINUX_SCROLL_CONFIG,
) -> None:
    print("Starting face tracking. Press Ctrl+C to stop.")
    face_blend_shape, py_live_link_face = _load_livelinkface()

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        print(f"Starting face tracking on UDP port {port}")
        s.bind(("", port))
        while True:
            data, _addr = s.recvfrom(1024)
            success, live_link_face = py_live_link_face.decode(data)
            if success:
                signals = _brow_signals_from_live_link(
                    live_link_face,
                    face_blend_shape,
                )
                movement = combine_brow_movement(signals)
                scroll_amount = scroll_amount_from_movement(movement, scroll_config)

                smooth_scroll(scroll_amount, scroll_backend, linux_scroll_config)
                if scroll_amount != 0.0:
                    time.sleep(1 / 120)

                print(f"Name: {live_link_face.name}")
                print(
                    "Combined Brow Movement - "
                    f"Up: {movement.up:.2f}, Down: {movement.down:.2f}"
                )
                print(f"Scroll amount: {scroll_amount}")
                print("-" * 40)
    except KeyboardInterrupt:
        print("Stopping face tracking...")
    finally:
        _stop_linux_scroller()
        s.close()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Eyebrow-controlled scroll using face tracking"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_UDP_PORT,
        help=f"UDP port to listen on (default: {DEFAULT_UDP_PORT})",
    )
    parser.add_argument(
        "--scroll-backend",
        choices=(
            "auto",
            "uinput-hires",
            "xtest",
            "none",
        ),
        default="auto",
        help="Linux scroll backend (default: auto)",
    )
    parser.add_argument(
        "--scroll-threshold",
        type=float,
        default=DEFAULT_SCROLL_CONFIG.threshold,
        help=(
            "Eyebrow dead zone threshold "
            f"(default: {DEFAULT_SCROLL_CONFIG.threshold})"
        ),
    )
    parser.add_argument(
        "--scroll-speed",
        type=float,
        default=DEFAULT_SCROLL_CONFIG.speed,
        help=f"Scroll sensitivity multiplier (default: {DEFAULT_SCROLL_CONFIG.speed})",
    )
    parser.add_argument(
        "--max-scroll",
        type=float,
        default=DEFAULT_SCROLL_CONFIG.max_scroll,
        help=(
            "Maximum scroll amount before pacing "
            f"(default: {DEFAULT_SCROLL_CONFIG.max_scroll})"
        ),
    )
    parser.add_argument(
        "--min-scroll-rate",
        type=float,
        default=None,
        help=(
            "Minimum Linux wheel detents per second after the dead zone "
            "(default: backend-specific)"
        ),
    )
    parser.add_argument(
        "--max-scroll-rate",
        type=float,
        default=None,
        help=(
            "Maximum Linux wheel detents per second (default: backend-specific)"
        ),
    )
    parser.add_argument(
        "--compat-detent-units",
        type=int,
        default=None,
        help=(
            "Hi-res units per fallback wheel click "
            f"(default: {DEFAULT_LINUX_SCROLL_CONFIG.compat_detent_units})"
        ),
    )
    args = parser.parse_args()

    min_scroll_rate = args.min_scroll_rate
    if min_scroll_rate is None:
        min_scroll_rate = DEFAULT_LINUX_SCROLL_CONFIG.min_detents_per_second

    max_scroll_rate = args.max_scroll_rate
    if max_scroll_rate is None:
        max_scroll_rate = DEFAULT_LINUX_SCROLL_CONFIG.max_detents_per_second

    compat_detent_units = args.compat_detent_units
    if compat_detent_units is None:
        compat_detent_units = DEFAULT_LINUX_SCROLL_CONFIG.compat_detent_units

    scroll_config = ScrollConfig(
        threshold=args.scroll_threshold,
        speed=args.scroll_speed,
        max_scroll=args.max_scroll,
    )
    linux_scroll_config = LinuxScrollConfig(
        min_detents_per_second=min_scroll_rate,
        max_detents_per_second=max_scroll_rate,
        compat_detent_units=compat_detent_units,
    )

    try:
        start_face_tracking(
            args.port,
            scroll_backend=args.scroll_backend,
            scroll_config=scroll_config,
            linux_scroll_config=linux_scroll_config,
        )
    except KeyboardInterrupt:
        print("\nStopping face tracking...")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
