import unittest

from face_gestures import Scroll, SignalFrame


class ScrollTests(unittest.TestCase):
    def test_vertical_scroll_uses_logical_brow_aliases(self):
        scroll = Scroll.vertical(
            up="brows_up",
            down="brows_down",
            threshold=0.1,
            speed=1.0,
        )
        frame = SignalFrame(
            {
                "brow_inner_up": 0.3,
                "brow_outer_up_left": 0.6,
                "brow_outer_up_right": 0.9,
                "brow_down_left": 0.0,
                "brow_down_right": 0.0,
            }
        )

        self.assertAlmostEqual(scroll.intent(frame), 0.5)

    def test_vertical_scroll_supports_generic_raw_signals(self):
        scroll = Scroll.vertical(down="jaw_open", threshold=0.2, speed=2.0)
        frame = SignalFrame({"jaw_open": 0.45})

        self.assertAlmostEqual(scroll.intent(frame), -0.5)

    def test_vertical_scroll_subtracts_opposing_signals(self):
        scroll = Scroll.vertical(
            up="mouth_smile",
            down="jaw_open",
            threshold=0.1,
            speed=1.0,
        )
        frame = SignalFrame(
            {
                "mouth_smile_left": 0.4,
                "mouth_smile_right": 0.4,
                "jaw_open": 0.2,
            }
        )

        self.assertAlmostEqual(scroll.intent(frame), 0.2)

    def test_vertical_scroll_clamps_intent(self):
        scroll = Scroll.vertical(up="jaw_open", threshold=0.1, speed=10.0)
        frame = SignalFrame({"jaw_open": 1.0})

        self.assertEqual(scroll.intent(frame), 1.0)

    def test_vertical_scroll_requires_at_least_one_signal(self):
        with self.assertRaises(ValueError):
            Scroll.vertical()


if __name__ == "__main__":
    unittest.main()
