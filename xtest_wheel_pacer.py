from Xlib import X, display, error as xerror
from Xlib.ext import xtest

from paced_scroller import PacedScroller
from scroll_pacer import WheelPacer, WheelPacerConfig


class XTestWheelOutput:
    def __init__(self):
        self._display = display.Display()
        if not self._display.query_extension("XTEST").present:
            raise RuntimeError("XTEST extension not available on this X server")
        self._x = X

    def scroll(self, ticks: int) -> None:
        ticks = int(ticks)
        if ticks == 0:
            return

        button = 4 if ticks > 0 else 5
        for _ in range(abs(ticks)):
            xtest.fake_input(self._display, self._x.ButtonPress, button)
            xtest.fake_input(self._display, self._x.ButtonRelease, button)
        self._display.sync()

    def close(self) -> None:
        try:
            self._display.close()
        except xerror.ConnectionClosedError:
            pass


class XTestWheelPacer:
    """
    Convert a continuous signed amount into paced X11 wheel ticks.
    """

    def __init__(
        self,
        min_rate=4.0,
        max_rate=40.0,
        ease_power=2.2,
        hysteresis=0.02,
        max_ticks_per_flush=6,
        flush_hz=50,
        max_input=1.0,
    ):
        config = WheelPacerConfig(
            min_rate=float(min_rate),
            max_rate=float(max_rate),
            ease_power=float(ease_power),
            hysteresis=float(hysteresis),
            max_ticks_per_step=int(max_ticks_per_flush),
            max_input=float(max_input),
        )
        self._runner = PacedScroller(
            XTestWheelOutput(),
            WheelPacer(config),
            flush_hz=float(flush_hz),
        )

    def set_amount(self, amount: float) -> None:
        self._runner.set_amount(amount)

    def stop(self) -> None:
        self._runner.stop()
