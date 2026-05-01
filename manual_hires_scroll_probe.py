#!/usr/bin/env python3
import argparse
import time

from uinput_hires_scroller import UInputHiResWheelOutput


def run_single_probe(output: UInputHiResWheelOutput, pause: float) -> None:
    print("Single high-resolution unit probe")
    print("A normal wheel click is 120 units; these values are below one click.")
    for units in (1, 2, 4, 8, 16, 32, 60, 120, -1, -2, -4, -8, -16, -32, -60, -120):
        print(f"Sending REL_WHEEL_HI_RES {units:+d}")
        output.scroll_units(units)
        time.sleep(pause)


def run_ramp_probe(
    output: UInputHiResWheelOutput,
    duration: float,
    interval: float,
) -> None:
    print("Sustained high-resolution ramp probe")
    print("Watch for continuous crawl at low values, not wheel-click jumps.")
    phases = (
        (1, duration),
        (2, duration),
        (4, duration),
        (8, duration),
        (16, duration),
        (0, 0.5),
        (-1, duration),
        (-2, duration),
        (-4, duration),
        (-8, duration),
        (-16, duration),
    )

    for units, phase_duration in phases:
        print(f"{units:+d} hi-res units/frame for {phase_duration:.1f}s")
        end = time.monotonic() + phase_duration
        while time.monotonic() < end:
            output.scroll_units(units)
            time.sleep(interval)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manual Linux REL_WHEEL_HI_RES smooth scroll probe"
    )
    parser.add_argument(
        "--case",
        choices=("all", "single", "ramp"),
        default="all",
        help="Probe case to run",
    )
    parser.add_argument(
        "--compat-detents",
        action="store_true",
        help="Also emit throttled fallback REL_WHEEL clicks",
    )
    parser.add_argument(
        "--compat-detent-units",
        type=int,
        default=48000,
        help="Hi-res units per fallback REL_WHEEL click (default: 48000)",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=1.5,
        help="Seconds per ramp phase",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1 / 120,
        help="Ramp frame interval",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=0.7,
        help="Pause between single probes",
    )
    parser.add_argument(
        "--focus-delay",
        type=float,
        default=3.0,
        help="Time to focus a scrollable window",
    )
    args = parser.parse_args()

    print("Focus a scrollable Wayland window now.")
    print("Default mode emits REL_WHEEL_HI_RES only, with no fallback wheel clicks.")
    if not args.compat_detents:
        print("If nothing moves, rerun with --compat-detents.")
    time.sleep(args.focus_delay)

    output = UInputHiResWheelOutput(
        compat_detents=args.compat_detents,
        compat_detent_units=args.compat_detent_units,
    )
    try:
        if args.case in ("all", "single"):
            run_single_probe(output, args.pause)
        if args.case in ("all", "ramp"):
            run_ramp_probe(output, args.duration, args.interval)
    finally:
        output.close()


if __name__ == "__main__":
    main()
