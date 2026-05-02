import socket

from .signals import RAW_SIGNALS, SignalFrame


DEFAULT_UDP_PORT = 11111


def _load_livelinkface():
    try:
        from pylivelinkface import FaceBlendShape, PyLiveLinkFace
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "pylivelinkface is not installed. Run `pip install -r requirements.txt`."
        ) from exc

    return FaceBlendShape, PyLiveLinkFace


def _signal_to_livelink_attr(signal: str) -> str:
    return "".join(part.capitalize() for part in signal.split("_"))


class LiveLinkSource:
    def __init__(self, port: int = DEFAULT_UDP_PORT, bind_host: str = ""):
        self._face_blend_shape, self._decoder = _load_livelinkface()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((bind_host, port))

    def poll(self, timeout: float) -> SignalFrame | None:
        self._sock.settimeout(max(0.0, float(timeout)))
        try:
            data, _addr = self._sock.recvfrom(65535)
        except (BlockingIOError, socket.timeout):
            return None

        success, live_link_face = self._decoder.decode(data)
        if not success:
            return None

        return self._frame_from_live_link(live_link_face)

    def close(self) -> None:
        self._sock.close()

    def _frame_from_live_link(self, live_link_face) -> SignalFrame:
        values = {}
        get_blendshape = live_link_face.get_blendshape
        for signal in RAW_SIGNALS:
            attr = _signal_to_livelink_attr(signal)
            if hasattr(self._face_blend_shape, attr):
                values[signal] = get_blendshape(getattr(self._face_blend_shape, attr))
        return SignalFrame(values, name=getattr(live_link_face, "name", None))
