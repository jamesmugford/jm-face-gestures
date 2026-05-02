from .driver import ScrollDriver
from .output import DEFAULT_COMPAT_DETENT_UNITS, create_scroll_output
from .scroll import Scroll
from .source import DEFAULT_UDP_PORT, LiveLinkSource


class GestureControl:
    def __init__(
        self,
        *,
        port: int = DEFAULT_UDP_PORT,
        source=None,
        output=None,
        tick_hz: float = 120.0,
        input_timeout: float = 0.25,
        compat_detent_units: int = DEFAULT_COMPAT_DETENT_UNITS,
        on_frame=None,
    ):
        self._port = int(port)
        self._source = source
        self._output = output
        self._tick_hz = float(tick_hz)
        self._input_timeout = float(input_timeout)
        self._compat_detent_units = int(compat_detent_units)
        self._on_frame = on_frame
        self._scrolls = []

    def scroll(self, mapping: Scroll) -> "GestureControl":
        if not isinstance(mapping, Scroll):
            raise TypeError("scroll() expects a Scroll mapping")
        self._scrolls.append(mapping)
        return self

    def run(self) -> None:
        if not self._scrolls:
            raise RuntimeError("No scroll mapping configured. Call .scroll(...).")

        source = self._source or LiveLinkSource(port=self._port)
        try:
            output = self._output or create_scroll_output(
                compat_detent_units=self._compat_detent_units
            )
        except Exception:
            self._close_if_created(source, self._source is None)
            raise

        ScrollDriver(
            source=source,
            output=output,
            scrolls=self._scrolls,
            tick_hz=self._tick_hz,
            input_timeout=self._input_timeout,
            on_frame=self._on_frame,
        ).run()

    def _close_if_created(self, value, created: bool) -> None:
        if not created:
            return
        close = getattr(value, "close", None)
        if close is not None:
            close()
