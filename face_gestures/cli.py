import argparse
from collections.abc import Sequence

from .control import GestureControl
from .output import DEFAULT_COMPAT_DETENT_UNITS
from .scroll import (
    DEFAULT_MAX_INTENT,
    DEFAULT_MAX_RATE,
    DEFAULT_MIN_RATE,
    DEFAULT_SPEED,
    DEFAULT_THRESHOLD,
    Scroll,
)
from .source import DEFAULT_UDP_PORT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Face gesture smooth scroll")
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_UDP_PORT,
        help=f"UDP port to listen on (default: {DEFAULT_UDP_PORT})",
    )
    parser.add_argument(
        "--up-signal",
        default="brows_up",
        help="Signal that scrolls up (default: brows_up)",
    )
    parser.add_argument(
        "--down-signal",
        default="brows_down",
        help="Signal that scrolls down (default: brows_down)",
    )
    parser.add_argument(
        "--scroll-threshold",
        type=float,
        default=DEFAULT_THRESHOLD,
        help=f"Signal dead zone threshold (default: {DEFAULT_THRESHOLD})",
    )
    parser.add_argument(
        "--scroll-speed",
        type=float,
        default=DEFAULT_SPEED,
        help=f"Scroll sensitivity multiplier (default: {DEFAULT_SPEED})",
    )
    parser.add_argument(
        "--max-intent",
        type=float,
        default=DEFAULT_MAX_INTENT,
        help=f"Maximum signed scroll intent (default: {DEFAULT_MAX_INTENT})",
    )
    parser.add_argument(
        "--min-scroll-rate",
        type=float,
        default=DEFAULT_MIN_RATE,
        help=(
            "Minimum wheel detents per second after the dead zone "
            f"(default: {DEFAULT_MIN_RATE})"
        ),
    )
    parser.add_argument(
        "--max-scroll-rate",
        type=float,
        default=DEFAULT_MAX_RATE,
        help=f"Maximum wheel detents per second (default: {DEFAULT_MAX_RATE})",
    )
    parser.add_argument(
        "--compat-detent-units",
        type=int,
        default=DEFAULT_COMPAT_DETENT_UNITS,
        help=(
            "Hi-res units per fallback wheel click on Linux "
            f"(default: {DEFAULT_COMPAT_DETENT_UNITS})"
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    last_name = None

    def report_frame(frame) -> None:
        nonlocal last_name
        if frame.name is None or frame.name == last_name:
            return
        print(f"Receiving tracking data from {frame.name!r}")
        last_name = frame.name

    scroll = Scroll.vertical(
        up=args.up_signal,
        down=args.down_signal,
        threshold=args.scroll_threshold,
        speed=args.scroll_speed,
        max_intent=args.max_intent,
        min_rate=args.min_scroll_rate,
        max_rate=args.max_scroll_rate,
    )

    try:
        print(f"Listening for face tracking UDP on port {args.port}")
        print("Move configured signals to scroll. Press Ctrl+C to stop.")
        GestureControl(
            port=args.port,
            compat_detent_units=args.compat_detent_units,
            on_frame=report_frame,
        ).scroll(scroll).run()
    except KeyboardInterrupt:
        print("\nStopping gesture scroll...")
    except (OSError, RuntimeError, ValueError) as exc:
        raise SystemExit(f"Error: {exc}") from exc
