import time
from collections.abc import Callable, Sequence

from .pacing import PacerState, step_pacer
from .scroll import Scroll
from .signals import SignalFrame


class ScrollDriver:
    def __init__(
        self,
        *,
        source,
        output,
        scrolls: Sequence[Scroll],
        tick_hz: float = 120.0,
        input_timeout: float = 0.25,
        on_frame: Callable[[SignalFrame], None] | None = None,
    ):
        if not scrolls:
            raise ValueError("at least one scroll mapping is required")
        if tick_hz <= 0.0:
            raise ValueError("tick_hz must be greater than zero")
        if input_timeout <= 0.0:
            raise ValueError("input_timeout must be greater than zero")

        self._source = source
        self._output = output
        self._scrolls = tuple(scrolls)
        self._tick_dt = 1.0 / float(tick_hz)
        self._input_timeout = float(input_timeout)
        self._on_frame = on_frame
        self._states = [PacerState() for _scroll in self._scrolls]

    def run(self) -> None:
        current_frame = None
        last_frame_at = None
        last_tick = time.monotonic()
        next_tick = last_tick + self._tick_dt

        try:
            while True:
                now = time.monotonic()
                frame = self._source.poll(max(0.0, next_tick - now))
                now = time.monotonic()
                if frame is not None:
                    current_frame = frame
                    last_frame_at = now
                    if self._on_frame is not None:
                        self._on_frame(frame)

                if now < next_tick:
                    continue

                dt = now - last_tick
                last_tick = now
                next_tick = now + self._tick_dt

                active_frame = None
                if last_frame_at is not None and now - last_frame_at <= self._input_timeout:
                    active_frame = current_frame

                units = self._step(active_frame, dt)
                if units:
                    self._output.scroll(units)
        finally:
            try:
                self._close(self._output)
            finally:
                self._close(self._source)

    def _step(self, frame: SignalFrame | None, dt: float) -> int:
        units = 0
        for index, scroll in enumerate(self._scrolls):
            intent = scroll.intent(frame) if frame is not None else 0.0
            self._states[index], emitted = step_pacer(
                self._states[index],
                intent,
                dt,
                scroll,
            )
            units += emitted
        return units

    def _close(self, value) -> None:
        close = getattr(value, "close", None)
        if close is not None:
            close()
