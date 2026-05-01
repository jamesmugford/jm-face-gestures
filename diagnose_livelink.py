#!/usr/bin/env python3
import argparse
import socket
import time


DEFAULT_UDP_PORT = 11111


def _load_livelinkface():
    try:
        from pylivelinkface import FaceBlendShape, PyLiveLinkFace
    except ModuleNotFoundError:
        return None, None

    return FaceBlendShape, PyLiveLinkFace


def _primary_local_ip() -> str | None:
    probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        probe.connect(("1.1.1.1", 80))
        return probe.getsockname()[0]
    except OSError:
        return None
    finally:
        probe.close()


def _format_brows(live_link_face, face_blend_shape) -> str:
    get_blendshape = live_link_face.get_blendshape
    brow_down_left = get_blendshape(face_blend_shape.BrowDownLeft)
    brow_down_right = get_blendshape(face_blend_shape.BrowDownRight)
    brow_inner_up = get_blendshape(face_blend_shape.BrowInnerUp)
    brow_outer_up_left = get_blendshape(face_blend_shape.BrowOuterUpLeft)
    brow_outer_up_right = get_blendshape(face_blend_shape.BrowOuterUpRight)

    brow_up = (brow_inner_up + brow_outer_up_left + brow_outer_up_right) / 3.0
    brow_down = (brow_down_left + brow_down_right) / 2.0
    return f"brow_up={brow_up:.3f} brow_down={brow_down:.3f}"


def listen(port: int, seconds: float, bind_host: str) -> int:
    face_blend_shape, py_live_link_face = _load_livelinkface()
    can_decode = py_live_link_face is not None

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((bind_host, port))
    sock.settimeout(0.5)

    local_ip = _primary_local_ip()
    if local_ip:
        print(f"Likely local IP for iPhone target: {local_ip}")
    print(f"Listening on UDP {bind_host or '0.0.0.0'}:{port} for {seconds:.1f}s")
    if not can_decode:
        print("pylivelinkface is not installed; only raw packet arrival will be shown.")
    print("Start Live Link Face and set its target to this machine and port.")

    start = time.monotonic()
    packets = 0
    decoded = 0
    try:
        while time.monotonic() - start < seconds:
            try:
                data, addr = sock.recvfrom(65535)
            except socket.timeout:
                continue

            packets += 1
            prefix = f"#{packets} from {addr[0]}:{addr[1]} {len(data)} bytes"
            if not can_decode:
                print(prefix)
                continue

            success, live_link_face = py_live_link_face.decode(data)
            if not success:
                print(f"{prefix} decode=failed")
                continue

            decoded += 1
            brows = _format_brows(live_link_face, face_blend_shape)
            print(f"{prefix} decode=ok name={live_link_face.name!r} {brows}")
    finally:
        sock.close()

    print(f"Summary: packets={packets} decoded={decoded}")
    return 0 if packets else 1


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check whether Live Link Face UDP data is reaching this machine"
    )
    parser.add_argument("--port", type=int, default=DEFAULT_UDP_PORT)
    parser.add_argument("--seconds", type=float, default=30.0)
    parser.add_argument(
        "--bind-host",
        default="",
        help="Address to bind, default all interfaces",
    )
    args = parser.parse_args()

    raise SystemExit(listen(args.port, args.seconds, args.bind_host))


if __name__ == "__main__":
    main()
