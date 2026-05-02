import os
import sys
import time


DEFAULT_COMPAT_DETENT_UNITS = 48000


def platform_output_kind(platform: str = sys.platform) -> str:
    if platform.startswith("linux"):
        return "linux-uinput"
    if platform == "win32":
        return "windows-wheel"
    if platform == "darwin":
        return "macos-quartz"
    raise RuntimeError(f"Unsupported platform: {platform}")


def _load_evdev():
    try:
        from evdev import UInput, ecodes
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "python-evdev is not installed. Run `pip install -r requirements.txt`."
        ) from exc

    if not hasattr(ecodes, "REL_WHEEL_HI_RES"):
        raise RuntimeError("python-evdev/kernel headers do not expose REL_WHEEL_HI_RES")

    return UInput, ecodes


def _check_uinput_access() -> None:
    if not os.path.exists("/dev/uinput"):
        raise RuntimeError("/dev/uinput does not exist; load the uinput kernel module")
    if os.access("/dev/uinput", os.W_OK):
        return
    raise RuntimeError(
        "No write access to /dev/uinput. Add your user to the input group "
        "or configure udev permissions, then log out and back in."
    )


class LinuxUInputScrollOutput:
    def __init__(
        self,
        compat_detent_units: int = DEFAULT_COMPAT_DETENT_UNITS,
        name: str = "jm-face-gestures-hires-wheel",
        device_ready_delay: float = 0.3,
    ):
        if compat_detent_units <= 0:
            raise ValueError("compat_detent_units must be greater than zero")

        _check_uinput_access()
        UInput, ecodes = _load_evdev()
        self._ecodes = ecodes
        self._ui = UInput(
            {ecodes.EV_REL: [ecodes.REL_WHEEL_HI_RES, ecodes.REL_WHEEL]},
            name=name,
            bustype=ecodes.BUS_USB,
        )
        self._compat_detent_units = int(compat_detent_units)
        self._compat_accumulator = 0
        time.sleep(device_ready_delay)

    def scroll(self, units: int) -> None:
        units = int(units)
        if units == 0:
            return

        self._ui.write(self._ecodes.EV_REL, self._ecodes.REL_WHEEL_HI_RES, units)
        self._compat_accumulator += units
        detents = int(self._compat_accumulator / self._compat_detent_units)
        if detents:
            self._ui.write(self._ecodes.EV_REL, self._ecodes.REL_WHEEL, detents)
            self._compat_accumulator -= detents * self._compat_detent_units
        self._ui.syn()

    def close(self) -> None:
        self._ui.close()


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


def create_scroll_output(
    compat_detent_units: int = DEFAULT_COMPAT_DETENT_UNITS,
    platform: str = sys.platform,
):
    kind = platform_output_kind(platform)
    if kind == "linux-uinput":
        return LinuxUInputScrollOutput(compat_detent_units=compat_detent_units)
    if kind == "windows-wheel":
        return WindowsWheelOutput()
    if kind == "macos-quartz":
        return MacOSScrollOutput()
    raise RuntimeError(f"Unsupported platform output: {kind}")
