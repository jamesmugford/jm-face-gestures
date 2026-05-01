import os
import time

from scroll_pacer import PacerConfig
from scroll_runtime import PacedScroller


DEFAULT_COMPAT_DETENT_UNITS = 48000


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


class UInputHiResWheelOutput:
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


def create_uinput_scroller(
    pacer_config: PacerConfig = PacerConfig(),
    compat_detent_units: int = DEFAULT_COMPAT_DETENT_UNITS,
    flush_hz: float = 120.0,
) -> PacedScroller:
    return PacedScroller(
        UInputHiResWheelOutput(compat_detent_units=compat_detent_units),
        pacer_config,
        flush_hz=flush_hz,
    )
