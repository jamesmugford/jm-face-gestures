import os
import time

from paced_scroller import PacedScroller
from scroll_pacer import WheelPacer, WheelPacerConfig


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
    if not os.access("/dev/uinput", os.W_OK):
        raise RuntimeError(
            "No write access to /dev/uinput. Add your user to the input group "
            "or configure udev permissions, then log out and back in."
        )


class UInputHiResWheelOutput:
    """
    Emit Linux high-resolution wheel units through uinput.

    A traditional wheel detent is 120 high-resolution units. Sending smaller
    values lets compositors that support REL_WHEEL_HI_RES produce smooth axis
    events instead of whole wheel-click steps.
    """

    def __init__(
        self,
        name: str = "jm-face-gestures-hires-wheel",
        compat_detents: bool = False,
        compat_detent_units: int = 48000,
        device_ready_delay: float = 0.3,
    ):
        if compat_detent_units <= 0:
            raise ValueError("compat_detent_units must be greater than zero")

        _check_uinput_access()
        UInput, ecodes = _load_evdev()
        rel_events = [ecodes.REL_WHEEL_HI_RES]
        if compat_detents:
            rel_events.append(ecodes.REL_WHEEL)

        self._ecodes = ecodes
        self._ui = UInput(
            {ecodes.EV_REL: rel_events},
            name=name,
            bustype=ecodes.BUS_USB,
        )
        self._compat_detents = bool(compat_detents)
        self._compat_detent_units = int(compat_detent_units)
        self._compat_accum = 0
        time.sleep(device_ready_delay)

    def scroll(self, units: int) -> None:
        self.scroll_units(units)

    def scroll_units(self, units: int) -> None:
        units = int(units)
        if units == 0:
            return

        self._ui.write(
            self._ecodes.EV_REL,
            self._ecodes.REL_WHEEL_HI_RES,
            units,
        )
        if self._compat_detents:
            self._compat_accum += units
            detents = int(self._compat_accum / self._compat_detent_units)
            if detents:
                self._ui.write(self._ecodes.EV_REL, self._ecodes.REL_WHEEL, detents)
                self._compat_accum -= detents * self._compat_detent_units
        self._ui.syn()

    def close(self) -> None:
        self._ui.close()


def create_uinput_hires_scroller(
    compat_detents: bool = False,
    compat_detent_units: int = 48000,
    min_detents_per_second: float = 0.03,
    max_detents_per_second: float = 18.0,
    ease_power: float = 2.2,
    hysteresis: float = 0.01,
    flush_hz: float = 120.0,
    max_units_per_flush: int = 48,
    max_input: float = 1.0,
) -> PacedScroller:
    config = WheelPacerConfig(
        min_rate=float(min_detents_per_second) * 120.0,
        max_rate=float(max_detents_per_second) * 120.0,
        ease_power=float(ease_power),
        hysteresis=float(hysteresis),
        max_ticks_per_step=int(max_units_per_flush),
        max_input=float(max_input),
    )
    return PacedScroller(
        UInputHiResWheelOutput(
            compat_detents=compat_detents,
            compat_detent_units=compat_detent_units,
        ),
        WheelPacer(config),
        flush_hz=float(flush_hz),
    )
