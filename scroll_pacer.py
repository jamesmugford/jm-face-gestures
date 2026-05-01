from dataclasses import dataclass


@dataclass(frozen=True)
class PacerConfig:
    min_detents_per_second: float = 0.03
    max_detents_per_second: float = 18.0
    units_per_detent: int = 120
    ease_power: float = 2.2
    hysteresis: float = 0.01
    max_units_per_step: int = 48
    max_input: float = 1.0


@dataclass(frozen=True)
class PacerState:
    accumulator: float = 0.0
    direction: int = 0


def rate_for_amount(amount: float, config: PacerConfig = PacerConfig()) -> float:
    amount = float(amount)
    if abs(amount) < config.hysteresis:
        return 0.0

    magnitude = min(1.0, abs(amount) / config.max_input)
    eased = magnitude**config.ease_power
    detents_per_second = config.min_detents_per_second + (
        config.max_detents_per_second - config.min_detents_per_second
    ) * eased
    return detents_per_second * config.units_per_detent


def step_pacer(
    state: PacerState,
    amount: float,
    dt: float,
    config: PacerConfig = PacerConfig(),
) -> tuple[PacerState, int]:
    dt = float(dt)
    if dt <= 0.0:
        return state, 0

    rate = rate_for_amount(amount, config)
    if rate <= 0.0:
        return PacerState(), 0

    direction = 1 if amount > 0 else -1
    accumulator = state.accumulator if state.direction == direction else 0.0
    accumulator += rate * dt

    units = int(accumulator)
    if units <= 0:
        return PacerState(accumulator=accumulator, direction=direction), 0

    max_units = max(1, int(config.max_units_per_step))
    emitted = min(units, max_units)
    remaining = accumulator - (units if units > max_units else emitted)
    next_state = PacerState(
        accumulator=remaining,
        direction=direction,
    )
    return next_state, direction * emitted
