from dataclasses import dataclass


@dataclass(frozen=True)
class WheelPacerConfig:
    min_rate: float = 4.0
    max_rate: float = 40.0
    ease_power: float = 2.2
    hysteresis: float = 0.01
    max_ticks_per_step: int = 6
    max_input: float = 1.0


class WheelPacer:
    def __init__(self, config: WheelPacerConfig = WheelPacerConfig()):
        self.config = config
        self._accum = 0.0
        self._direction = 0

    def reset(self) -> None:
        self._accum = 0.0
        self._direction = 0

    def rate_for_amount(self, amount: float) -> float:
        amount = float(amount)
        if abs(amount) < self.config.hysteresis:
            return 0.0

        magnitude = min(1.0, abs(amount) / self.config.max_input)
        eased = magnitude ** self.config.ease_power
        return self.config.min_rate + (
            self.config.max_rate - self.config.min_rate
        ) * eased

    def step(self, amount: float, dt: float) -> int:
        dt = float(dt)
        if dt <= 0.0:
            return 0

        rate = self.rate_for_amount(amount)
        if rate <= 0.0:
            self.reset()
            return 0

        direction = 1 if amount > 0 else -1
        if direction != self._direction:
            self._accum = 0.0
            self._direction = direction

        self._accum += rate * dt
        ticks = int(self._accum)
        if ticks <= 0:
            return 0

        emitted = min(ticks, max(1, int(self.config.max_ticks_per_step)))
        self._accum -= emitted
        return direction * emitted
