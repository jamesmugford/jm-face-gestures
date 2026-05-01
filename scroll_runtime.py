import threading
import time

from scroll_pacer import PacerConfig, PacerState, step_pacer


class PacedScroller:
    def __init__(self, output, config: PacerConfig, flush_hz: float = 120.0):
        self._output = output
        self._config = config
        self._state = PacerState()
        self._flush_dt = 1.0 / float(flush_hz)
        self._amount = 0.0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def set_amount(self, amount: float) -> None:
        with self._lock:
            self._amount = float(amount)

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1.0)
        close = getattr(self._output, "close", None)
        if close is not None:
            close()

    def _loop(self) -> None:
        last = time.monotonic()
        while not self._stop.is_set():
            now = time.monotonic()
            dt = now - last
            if dt < self._flush_dt:
                time.sleep(self._flush_dt - dt)
                continue

            last = now
            with self._lock:
                amount = self._amount

            self._state, units = step_pacer(self._state, amount, dt, self._config)
            if units:
                self._output.scroll(units)
