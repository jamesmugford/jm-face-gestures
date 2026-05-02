import re
from collections.abc import Mapping
from dataclasses import dataclass
from difflib import get_close_matches
from types import MappingProxyType


RAW_SIGNALS = (
    "brow_down_left",
    "brow_down_right",
    "brow_inner_up",
    "brow_outer_up_left",
    "brow_outer_up_right",
    "cheek_puff",
    "cheek_squint_left",
    "cheek_squint_right",
    "eye_blink_left",
    "eye_blink_right",
    "eye_look_down_left",
    "eye_look_down_right",
    "eye_look_in_left",
    "eye_look_in_right",
    "eye_look_out_left",
    "eye_look_out_right",
    "eye_look_up_left",
    "eye_look_up_right",
    "eye_squint_left",
    "eye_squint_right",
    "eye_wide_left",
    "eye_wide_right",
    "jaw_forward",
    "jaw_left",
    "jaw_open",
    "jaw_right",
    "mouth_close",
    "mouth_dimple_left",
    "mouth_dimple_right",
    "mouth_frown_left",
    "mouth_frown_right",
    "mouth_funnel",
    "mouth_left",
    "mouth_lower_down_left",
    "mouth_lower_down_right",
    "mouth_press_left",
    "mouth_press_right",
    "mouth_pucker",
    "mouth_right",
    "mouth_roll_lower",
    "mouth_roll_upper",
    "mouth_shrug_lower",
    "mouth_shrug_upper",
    "mouth_smile_left",
    "mouth_smile_right",
    "mouth_stretch_left",
    "mouth_stretch_right",
    "mouth_upper_up_left",
    "mouth_upper_up_right",
    "nose_sneer_left",
    "nose_sneer_right",
    "tongue_out",
)


ALIASES = {
    "brows_down": ("brow_down_left", "brow_down_right"),
    "brows_up": ("brow_inner_up", "brow_outer_up_left", "brow_outer_up_right"),
    "cheek_squint": ("cheek_squint_left", "cheek_squint_right"),
    "cheeks_squint": ("cheek_squint_left", "cheek_squint_right"),
    "eyes_blink": ("eye_blink_left", "eye_blink_right"),
    "eyes_squint": ("eye_squint_left", "eye_squint_right"),
    "eyes_wide": ("eye_wide_left", "eye_wide_right"),
    "mouth_dimple": ("mouth_dimple_left", "mouth_dimple_right"),
    "mouth_frown": ("mouth_frown_left", "mouth_frown_right"),
    "mouth_lower_down": ("mouth_lower_down_left", "mouth_lower_down_right"),
    "mouth_press": ("mouth_press_left", "mouth_press_right"),
    "mouth_smile": ("mouth_smile_left", "mouth_smile_right"),
    "mouth_stretch": ("mouth_stretch_left", "mouth_stretch_right"),
    "mouth_upper_up": ("mouth_upper_up_left", "mouth_upper_up_right"),
    "nose_sneer": ("nose_sneer_left", "nose_sneer_right"),
}


class UnknownSignalError(ValueError):
    pass


def normalize_signal_name(name: str) -> str:
    normalized = str(name).strip().replace("-", "_").replace(" ", "_")
    normalized = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", normalized)
    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", normalized)
    normalized = re.sub(r"_+", "_", normalized)
    return normalized.strip("_").lower()


def aliases() -> tuple[str, ...]:
    return tuple(sorted(ALIASES))


def known() -> tuple[str, ...]:
    return tuple(sorted(set(RAW_SIGNALS) | set(ALIASES)))


@dataclass(frozen=True)
class SignalFrame:
    values: Mapping[str, float]
    name: str | None = None

    def __post_init__(self) -> None:
        normalized = {
            normalize_signal_name(name): float(value)
            for name, value in self.values.items()
        }
        object.__setattr__(self, "values", MappingProxyType(normalized))

    def value(self, name: str) -> float:
        signal = normalize_signal_name(name)
        if signal in self.values:
            return self.values[signal]
        if signal in ALIASES:
            parts = ALIASES[signal]
            return sum(self.value(part) for part in parts) / len(parts)
        if signal in RAW_SIGNALS:
            raise UnknownSignalError(
                f"Signal {name!r} is known but not present in this frame."
            )
        self._raise_unknown_signal(name, signal)

    def _raise_unknown_signal(self, original: str, normalized: str) -> None:
        candidates = sorted(set(self.values) | set(ALIASES) | set(RAW_SIGNALS))
        matches = get_close_matches(normalized, candidates, n=1)
        suggestion = f" Did you mean {matches[0]!r}?" if matches else ""
        known_aliases = ", ".join(aliases())
        raise UnknownSignalError(
            f"Unknown signal {original!r}.{suggestion} Known aliases: {known_aliases}."
        )
