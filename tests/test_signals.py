import unittest

from face_gestures.signals import (
    SignalFrame,
    UnknownSignalError,
    aliases,
    known,
    normalize_signal_name,
)
from face_gestures import signals


class SignalFrameTests(unittest.TestCase):
    def test_normalizes_livelink_and_user_signal_names(self):
        frame = SignalFrame({"BrowInnerUp": 0.4, "jaw open": 0.7})

        self.assertEqual(normalize_signal_name("BrowInnerUp"), "brow_inner_up")
        self.assertEqual(frame.value("brow_inner_up"), 0.4)
        self.assertEqual(frame.value("jaw_open"), 0.7)

    def test_brows_up_alias_averages_raw_brow_signals(self):
        frame = SignalFrame(
            {
                "brow_inner_up": 0.3,
                "brow_outer_up_left": 0.6,
                "brow_outer_up_right": 0.9,
            }
        )

        self.assertAlmostEqual(frame.value("brows_up"), 0.6)

    def test_brows_down_alias_averages_raw_brow_signals(self):
        frame = SignalFrame({"brow_down_left": 0.2, "brow_down_right": 0.4})

        self.assertAlmostEqual(frame.value("brows_down"), 0.3)

    def test_unknown_signal_error_includes_suggestion(self):
        frame = SignalFrame({"brow_inner_up": 0.4})

        with self.assertRaises(UnknownSignalError) as context:
            frame.value("brow_up")

        self.assertIn("brows_up", str(context.exception))

    def test_signal_discovery_exposes_aliases_and_raw_signals(self):
        self.assertIn("brows_up", aliases())
        self.assertIn("brows_down", aliases())
        self.assertIn("jaw_open", known())
        self.assertIn("jaw_open", signals.known())

    def test_known_but_missing_signal_error_is_specific(self):
        frame = SignalFrame({})

        with self.assertRaises(UnknownSignalError) as context:
            frame.value("jaw_open")

        self.assertIn("known but not present", str(context.exception))


if __name__ == "__main__":
    unittest.main()
