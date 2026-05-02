from dataclasses import dataclass

from .scroll import Scroll


@dataclass(frozen=True)
class PacerState:
    accumulator: float = 0.0
    direction: int = 0


def rate_for_intent(intent: float, scroll: Scroll) -> float:
    intent = float(intent)
    if abs(intent) < scroll.hysteresis:
        return 0.0

    magnitude = min(1.0, abs(intent) / scroll.max_intent)
    eased = magnitude**scroll.ease_power
    detents_per_second = scroll.min_rate + (scroll.max_rate - scroll.min_rate) * eased
    return detents_per_second * scroll.units_per_detent


def step_pacer(
    state: PacerState,
    intent: float,
    dt: float,
    scroll: Scroll,
) -> tuple[PacerState, int]:
    dt = float(dt)
    if dt <= 0.0:
        return state, 0

    rate = rate_for_intent(intent, scroll)
    if rate <= 0.0:
        return PacerState(), 0

    direction = 1 if intent > 0 else -1
    accumulator = state.accumulator if state.direction == direction else 0.0
    accumulator += rate * dt

    units = int(accumulator)
    if units <= 0:
        return PacerState(accumulator=accumulator, direction=direction), 0

    max_units = max(1, int(scroll.max_units_per_step))
    emitted = min(units, max_units)
    remaining = accumulator - (units if units > max_units else emitted)
    return PacerState(accumulator=remaining, direction=direction), direction * emitted
