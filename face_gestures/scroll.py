from dataclasses import dataclass

from .signals import SignalFrame, normalize_signal_name


DEFAULT_THRESHOLD = 0.08
DEFAULT_SPEED = 2.0
DEFAULT_MAX_INTENT = 1.0
DEFAULT_MIN_RATE = 0.03
DEFAULT_MAX_RATE = 18.0
DEFAULT_UNITS_PER_DETENT = 120
DEFAULT_EASE_POWER = 2.2
DEFAULT_HYSTERESIS = 0.01
DEFAULT_MAX_UNITS_PER_STEP = 48


@dataclass(frozen=True)
class Scroll:
    up: str | None = None
    down: str | None = None
    threshold: float = DEFAULT_THRESHOLD
    speed: float = DEFAULT_SPEED
    max_intent: float = DEFAULT_MAX_INTENT
    min_rate: float = DEFAULT_MIN_RATE
    max_rate: float = DEFAULT_MAX_RATE
    units_per_detent: int = DEFAULT_UNITS_PER_DETENT
    ease_power: float = DEFAULT_EASE_POWER
    hysteresis: float = DEFAULT_HYSTERESIS
    max_units_per_step: int = DEFAULT_MAX_UNITS_PER_STEP

    def __post_init__(self) -> None:
        if self.up is None and self.down is None:
            raise ValueError("Scroll.vertical requires at least one signal")
        if self.threshold < 0.0:
            raise ValueError("threshold must be zero or greater")
        if self.speed <= 0.0:
            raise ValueError("speed must be greater than zero")
        if self.max_intent <= 0.0:
            raise ValueError("max_intent must be greater than zero")
        if self.min_rate < 0.0:
            raise ValueError("min_rate must be zero or greater")
        if self.max_rate < self.min_rate:
            raise ValueError("max_rate must be greater than or equal to min_rate")
        if self.units_per_detent <= 0:
            raise ValueError("units_per_detent must be greater than zero")
        if self.ease_power <= 0.0:
            raise ValueError("ease_power must be greater than zero")
        if self.hysteresis < 0.0:
            raise ValueError("hysteresis must be zero or greater")
        if self.max_units_per_step <= 0:
            raise ValueError("max_units_per_step must be greater than zero")

        if self.up is not None:
            object.__setattr__(self, "up", normalize_signal_name(self.up))
        if self.down is not None:
            object.__setattr__(self, "down", normalize_signal_name(self.down))

    @classmethod
    def vertical(
        cls,
        *,
        up: str | None = None,
        down: str | None = None,
        threshold: float = DEFAULT_THRESHOLD,
        speed: float = DEFAULT_SPEED,
        max_intent: float = DEFAULT_MAX_INTENT,
        min_rate: float = DEFAULT_MIN_RATE,
        max_rate: float = DEFAULT_MAX_RATE,
    ) -> "Scroll":
        return cls(
            up=up,
            down=down,
            threshold=threshold,
            speed=speed,
            max_intent=max_intent,
            min_rate=min_rate,
            max_rate=max_rate,
        )

    def intent(self, frame: SignalFrame) -> float:
        amount = self.speed * (
            self._active_amount(frame, self.up) - self._active_amount(frame, self.down)
        )
        return max(-self.max_intent, min(self.max_intent, amount))

    def _active_amount(self, frame: SignalFrame, signal: str | None) -> float:
        if signal is None:
            return 0.0
        return max(0.0, frame.value(signal) - self.threshold)
