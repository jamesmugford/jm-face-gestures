import unittest

from scroll_core import (
    BrowMovement,
    BrowSignals,
    ScrollConfig,
    combine_brow_movement,
    scroll_amount_from_brows,
    scroll_amount_from_movement,
)
from scroll_pacer import WheelPacer, WheelPacerConfig


class ScrollCoreTests(unittest.TestCase):
    def test_default_threshold_is_low_enough_for_small_brow_movement(self):
        amount = scroll_amount_from_movement(BrowMovement(up=0.1, down=0.0))

        self.assertGreater(amount, 0.0)

    def test_combines_brow_signals(self):
        movement = combine_brow_movement(
            BrowSignals(
                brow_down_left=0.2,
                brow_down_right=0.4,
                brow_inner_up=0.3,
                brow_outer_up_left=0.6,
                brow_outer_up_right=0.9,
            )
        )

        self.assertAlmostEqual(movement.up, 0.6)
        self.assertAlmostEqual(movement.down, 0.3)

    def test_below_threshold_returns_zero_scroll(self):
        amount = scroll_amount_from_movement(
            BrowMovement(up=0.14, down=0.14), ScrollConfig(threshold=0.15)
        )

        self.assertEqual(amount, 0.0)

    def test_brow_up_returns_positive_scroll(self):
        amount = scroll_amount_from_movement(
            BrowMovement(up=0.35, down=0.0),
            ScrollConfig(threshold=0.15, speed=2.0),
        )

        self.assertAlmostEqual(amount, 0.4)

    def test_brow_down_returns_negative_scroll(self):
        amount = scroll_amount_from_movement(
            BrowMovement(up=0.0, down=0.4),
            ScrollConfig(threshold=0.15, speed=2.0),
        )

        self.assertAlmostEqual(amount, -0.5)

    def test_scroll_amount_clamps(self):
        amount = scroll_amount_from_movement(
            BrowMovement(up=10.0, down=0.0),
            ScrollConfig(threshold=0.15, speed=10.0, max_scroll=3.0),
        )

        self.assertEqual(amount, 3.0)

    def test_scroll_amount_from_brows_uses_combined_values(self):
        amount = scroll_amount_from_brows(
            BrowSignals(
                brow_down_left=0.0,
                brow_down_right=0.0,
                brow_inner_up=0.3,
                brow_outer_up_left=0.3,
                brow_outer_up_right=0.3,
            ),
            ScrollConfig(threshold=0.1, speed=1.0),
        )

        self.assertAlmostEqual(amount, 0.2)


class WheelPacerTests(unittest.TestCase):
    def fixed_pacer(self, max_ticks_per_step=100):
        return WheelPacer(
            WheelPacerConfig(
                min_rate=10.0,
                max_rate=10.0,
                ease_power=1.0,
                hysteresis=0.01,
                max_ticks_per_step=max_ticks_per_step,
                max_input=1.0,
            )
        )

    def test_hysteresis_returns_zero_and_resets_accumulator(self):
        pacer = self.fixed_pacer()

        self.assertEqual(pacer.step(1.0, 0.09), 0)
        self.assertEqual(pacer.step(0.0, 0.1), 0)
        self.assertEqual(pacer.step(1.0, 0.02), 0)

    def test_accumulates_fractional_ticks(self):
        pacer = self.fixed_pacer()

        self.assertEqual(pacer.step(1.0, 0.05), 0)
        self.assertEqual(pacer.step(1.0, 0.05), 1)

    def test_negative_amount_emits_negative_ticks(self):
        pacer = self.fixed_pacer()

        self.assertEqual(pacer.step(-1.0, 0.1), -1)

    def test_direction_change_discards_opposite_direction_accumulator(self):
        pacer = self.fixed_pacer()

        self.assertEqual(pacer.step(1.0, 0.09), 0)
        self.assertEqual(pacer.step(-1.0, 0.02), 0)
        self.assertEqual(pacer.step(-1.0, 0.08), -1)

    def test_caps_ticks_per_step(self):
        pacer = self.fixed_pacer(max_ticks_per_step=3)

        self.assertEqual(pacer.step(1.0, 1.0), 3)


if __name__ == "__main__":
    unittest.main()
