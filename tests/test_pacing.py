import unittest

from face_gestures import Scroll
from face_gestures.pacing import PacerState, rate_for_intent, step_pacer


class PacingTests(unittest.TestCase):
    def fixed_scroll(self, max_units_per_step=100):
        return Scroll(
            up="jaw_open",
            threshold=0.0,
            min_rate=10.0,
            max_rate=10.0,
            units_per_detent=1,
            ease_power=1.0,
            hysteresis=0.01,
            max_units_per_step=max_units_per_step,
        )

    def test_rate_for_intent_scales_by_units_per_detent(self):
        scroll = self.fixed_scroll()

        self.assertEqual(rate_for_intent(1.0, scroll), 10.0)
        self.assertEqual(rate_for_intent(0.0, scroll), 0.0)

    def test_hysteresis_returns_zero_and_resets_accumulator(self):
        scroll = self.fixed_scroll()
        state = PacerState()

        state, units = step_pacer(state, 1.0, 0.09, scroll)
        self.assertEqual(units, 0)
        state, units = step_pacer(state, 0.0, 0.1, scroll)
        self.assertEqual(state, PacerState())
        self.assertEqual(units, 0)
        state, units = step_pacer(state, 1.0, 0.02, scroll)
        self.assertEqual(units, 0)

    def test_accumulates_fractional_units(self):
        scroll = self.fixed_scroll()
        state = PacerState()

        state, units = step_pacer(state, 1.0, 0.05, scroll)
        self.assertEqual(units, 0)
        state, units = step_pacer(state, 1.0, 0.05, scroll)
        self.assertEqual(units, 1)

    def test_negative_intent_emits_negative_units(self):
        scroll = self.fixed_scroll()

        _state, units = step_pacer(PacerState(), -1.0, 0.1, scroll)
        self.assertEqual(units, -1)

    def test_direction_change_discards_opposite_direction_accumulator(self):
        scroll = self.fixed_scroll()
        state = PacerState()

        state, units = step_pacer(state, 1.0, 0.09, scroll)
        self.assertEqual(units, 0)
        state, units = step_pacer(state, -1.0, 0.02, scroll)
        self.assertEqual(units, 0)
        _state, units = step_pacer(state, -1.0, 0.08, scroll)
        self.assertEqual(units, -1)

    def test_cap_discards_backlog_but_keeps_fractional_accumulator(self):
        scroll = self.fixed_scroll(max_units_per_step=3)

        state, units = step_pacer(PacerState(), 1.0, 1.05, scroll)

        self.assertEqual(units, 3)
        self.assertAlmostEqual(state.accumulator, 0.5)


if __name__ == "__main__":
    unittest.main()
