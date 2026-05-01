import sys

from scroll_pacer import PacerConfig
from scroll_runtime import PacedScroller
from uinput_hires_scroller import DEFAULT_COMPAT_DETENT_UNITS, create_uinput_scroller


def platform_output_kind(platform: str = sys.platform) -> str:
    if platform.startswith("linux"):
        return "linux-uinput"
    if platform == "win32":
        return "windows-wheel"
    if platform == "darwin":
        return "macos-quartz"
    raise RuntimeError(f"Unsupported platform: {platform}")


class WindowsWheelOutput:
    def __init__(self):
        try:
            import win32api
            import win32con
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "pywin32 is not installed. Run `pip install -r requirements.txt`."
            ) from exc

        self._win32api = win32api
        self._wheel_event = win32con.MOUSEEVENTF_WHEEL

    def scroll(self, units: int) -> None:
        units = int(units)
        if units == 0:
            return
        self._win32api.mouse_event(self._wheel_event, 0, 0, units, 0)


class MacOSScrollOutput:
    def __init__(self):
        try:
            import Quartz
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "pyobjc-framework-Quartz is not installed. "
                "Run `pip install -r requirements.txt`."
            ) from exc

        self._quartz = Quartz

    def scroll(self, units: int) -> None:
        units = int(units)
        if units == 0:
            return

        event = self._quartz.CGEventCreateScrollWheelEvent(
            None,
            self._quartz.kCGScrollEventUnitPixel,
            1,
            units,
        )
        self._quartz.CGEventPost(self._quartz.kCGHIDEventTap, event)


def create_platform_scroller(
    pacer_config: PacerConfig = PacerConfig(),
    compat_detent_units: int = DEFAULT_COMPAT_DETENT_UNITS,
    platform: str = sys.platform,
) -> PacedScroller:
    kind = platform_output_kind(platform)
    if kind == "linux-uinput":
        return create_uinput_scroller(
            pacer_config=pacer_config,
            compat_detent_units=compat_detent_units,
        )
    if kind == "windows-wheel":
        return PacedScroller(WindowsWheelOutput(), pacer_config)
    if kind == "macos-quartz":
        return PacedScroller(MacOSScrollOutput(), pacer_config)
    raise RuntimeError(f"Unsupported platform output: {kind}")
