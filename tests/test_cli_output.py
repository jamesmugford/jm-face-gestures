import unittest

from face_gestures.cli import build_parser
from face_gestures.output import DEFAULT_COMPAT_DETENT_UNITS, platform_output_kind
from face_gestures.source import DEFAULT_UDP_PORT


class CliAndOutputTests(unittest.TestCase):
    def test_cli_defaults_match_public_brow_scroll_example(self):
        args = build_parser().parse_args([])

        self.assertEqual(args.port, DEFAULT_UDP_PORT)
        self.assertEqual(args.up_signal, "brows_up")
        self.assertEqual(args.down_signal, "brows_down")
        self.assertEqual(args.scroll_threshold, 0.08)
        self.assertEqual(args.scroll_speed, 1.0)
        self.assertEqual(args.max_intent, 1.0)
        self.assertEqual(args.min_scroll_rate, 0.03)
        self.assertEqual(args.max_scroll_rate, 18.0)
        self.assertEqual(args.compat_detent_units, DEFAULT_COMPAT_DETENT_UNITS)

    def test_cli_accepts_generic_signal_mapping(self):
        args = build_parser().parse_args(
            [
                "--up-signal",
                "mouth_smile",
                "--down-signal",
                "jaw_open",
                "--scroll-threshold",
                "0.2",
            ]
        )

        self.assertEqual(args.up_signal, "mouth_smile")
        self.assertEqual(args.down_signal, "jaw_open")
        self.assertEqual(args.scroll_threshold, 0.2)

    def test_platform_output_kind_uses_current_supported_outputs(self):
        self.assertEqual(platform_output_kind("linux"), "linux-uinput")
        self.assertEqual(platform_output_kind("linux2"), "linux-uinput")
        self.assertEqual(platform_output_kind("win32"), "windows-wheel")
        self.assertEqual(platform_output_kind("darwin"), "macos-quartz")

    def test_platform_output_kind_rejects_unknown_platforms(self):
        with self.assertRaises(RuntimeError):
            platform_output_kind("plan9")


if __name__ == "__main__":
    unittest.main()
