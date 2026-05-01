from dataclasses import dataclass


@dataclass(frozen=True)
class ScrollConfig:
    threshold: float = 0.08
    speed: float = 1.0
    max_scroll: float = 20.0


@dataclass(frozen=True)
class BrowSignals:
    brow_down_left: float
    brow_down_right: float
    brow_inner_up: float
    brow_outer_up_left: float
    brow_outer_up_right: float


@dataclass(frozen=True)
class BrowMovement:
    up: float
    down: float


def combine_brow_movement(signals: BrowSignals) -> BrowMovement:
    return BrowMovement(
        up=(
            signals.brow_inner_up
            + signals.brow_outer_up_left
            + signals.brow_outer_up_right
        )
        / 3.0,
        down=(signals.brow_down_left + signals.brow_down_right) / 2.0,
    )


def scroll_amount_from_movement(
    movement: BrowMovement,
    config: ScrollConfig = ScrollConfig(),
) -> float:
    if movement.up > config.threshold:
        return min(
            config.speed * (movement.up - config.threshold),
            config.max_scroll,
        )

    if movement.down > config.threshold:
        return -min(
            config.speed * (movement.down - config.threshold),
            config.max_scroll,
        )

    return 0.0


def scroll_amount_from_brows(
    signals: BrowSignals,
    config: ScrollConfig = ScrollConfig(),
) -> float:
    return scroll_amount_from_movement(combine_brow_movement(signals), config)
