import argparse
import socket
from collections.abc import Sequence
from dataclasses import dataclass

from scroll_core import (
    BrowMovement,
    BrowSignals,
    ScrollConfig,
    combine_brow_movement,
    scroll_amount_from_movement,
)
from scroll_pacer import PacerConfig
from platform_scroller import DEFAULT_COMPAT_DETENT_UNITS, create_platform_scroller


DEFAULT_UDP_PORT = 11111
INPUT_TIMEOUT_SECONDS = 0.25


@dataclass(frozen=True)
class AppConfig:
    port: int
    scroll: ScrollConfig
    pacer: PacerConfig
    compat_detent_units: int


@dataclass(frozen=True)
class ScrollFrame:
    name: str
    movement: BrowMovement
    amount: float


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


def _scroll_frame_from_packet(
    data: bytes,
    decoder,
    face_blend_shape,
    scroll_config: ScrollConfig,
) -> ScrollFrame | None:
    success, live_link_face = decoder.decode(data)
    if not success:
        return None

    signals = _brow_signals_from_live_link(live_link_face, face_blend_shape)
    movement = combine_brow_movement(signals)
    return ScrollFrame(
        name=live_link_face.name,
        movement=movement,
        amount=scroll_amount_from_movement(movement, scroll_config),
    )


def _build_parser() -> argparse.ArgumentParser:
    default_scroll = ScrollConfig()
    default_pacer = PacerConfig()
    parser = argparse.ArgumentParser(
        description="Eyebrow-controlled smooth scroll"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_UDP_PORT,
        help=f"UDP port to listen on (default: {DEFAULT_UDP_PORT})",
    )
    parser.add_argument(
        "--scroll-threshold",
        type=float,
        default=default_scroll.threshold,
        help=f"Eyebrow dead zone threshold (default: {default_scroll.threshold})",
    )
    parser.add_argument(
        "--scroll-speed",
        type=float,
        default=default_scroll.speed,
        help=f"Scroll sensitivity multiplier (default: {default_scroll.speed})",
    )
    parser.add_argument(
        "--max-scroll",
        type=float,
        default=default_scroll.max_scroll,
        help=f"Maximum mapped scroll amount (default: {default_scroll.max_scroll})",
    )
    parser.add_argument(
        "--min-scroll-rate",
        type=float,
        default=default_pacer.min_detents_per_second,
        help=(
            "Minimum wheel detents per second after the dead zone "
            f"(default: {default_pacer.min_detents_per_second})"
        ),
    )
    parser.add_argument(
        "--max-scroll-rate",
        type=float,
        default=default_pacer.max_detents_per_second,
        help=(
            "Maximum wheel detents per second "
            f"(default: {default_pacer.max_detents_per_second})"
        ),
    )
    parser.add_argument(
        "--compat-detent-units",
        type=int,
        default=DEFAULT_COMPAT_DETENT_UNITS,
        help=(
            "Hi-res units per fallback wheel click "
            f"on Linux (default: {DEFAULT_COMPAT_DETENT_UNITS})"
        ),
    )
    return parser


def parse_config(argv: Sequence[str] | None = None) -> AppConfig:
    args = _build_parser().parse_args(argv)
    return AppConfig(
        port=args.port,
        scroll=ScrollConfig(
            threshold=args.scroll_threshold,
            speed=args.scroll_speed,
            max_scroll=args.max_scroll,
        ),
        pacer=PacerConfig(
            min_detents_per_second=args.min_scroll_rate,
            max_detents_per_second=args.max_scroll_rate,
        ),
        compat_detent_units=args.compat_detent_units,
    )


def run(config: AppConfig) -> None:
    face_blend_shape, decoder = _load_livelinkface()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.settimeout(INPUT_TIMEOUT_SECONDS)
    scroller = None

    try:
        sock.bind(("", config.port))
        scroller = create_platform_scroller(
            pacer_config=config.pacer,
            compat_detent_units=config.compat_detent_units,
        )
        print(f"Listening for Live Link Face UDP on port {config.port}")
        print("Move brows to scroll. Press Ctrl+C to stop.")
        last_name = None

        while True:
            try:
                data, _addr = sock.recvfrom(65535)
            except socket.timeout:
                scroller.set_amount(0.0)
                continue

            frame = _scroll_frame_from_packet(
                data,
                decoder,
                face_blend_shape,
                config.scroll,
            )
            if frame is None:
                scroller.set_amount(0.0)
                continue

            if frame.name != last_name:
                print(f"Receiving tracking data from {frame.name!r}")
                last_name = frame.name
            scroller.set_amount(frame.amount)
    finally:
        if scroller is not None:
            scroller.stop()
        sock.close()


def main(argv: Sequence[str] | None = None) -> None:
    try:
        run(parse_config(argv))
    except KeyboardInterrupt:
        print("\nStopping eyebrow scroll...")
    except (OSError, RuntimeError) as exc:
        raise SystemExit(f"Error: {exc}") from exc


if __name__ == "__main__":
    main()
