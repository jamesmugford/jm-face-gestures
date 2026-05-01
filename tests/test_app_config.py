import unittest

from jm_eyebrow_scroll import DEFAULT_UDP_PORT, parse_config
from platform_scroller import platform_output_kind
from uinput_hires_scroller import DEFAULT_COMPAT_DETENT_UNITS


class AppConfigTests(unittest.TestCase):
    def test_default_config_matches_current_wayland_profile(self):
        config = parse_config([])

        self.assertEqual(config.port, DEFAULT_UDP_PORT)
        self.assertEqual(config.scroll.threshold, 0.08)
        self.assertEqual(config.scroll.speed, 1.0)
        self.assertEqual(config.scroll.max_scroll, 20.0)
        self.assertEqual(config.pacer.min_detents_per_second, 0.03)
        self.assertEqual(config.pacer.max_detents_per_second, 18.0)
        self.assertEqual(config.compat_detent_units, DEFAULT_COMPAT_DETENT_UNITS)

    def test_custom_config_values(self):
        config = parse_config(
            [
                "--port",
                "12345",
                "--scroll-threshold",
                "0.06",
                "--scroll-speed",
                "1.5",
                "--max-scroll",
                "10",
                "--min-scroll-rate",
                "0.02",
                "--max-scroll-rate",
                "4",
                "--compat-detent-units",
                "24000",
            ]
        )

        self.assertEqual(config.port, 12345)
        self.assertEqual(config.scroll.threshold, 0.06)
        self.assertEqual(config.scroll.speed, 1.5)
        self.assertEqual(config.scroll.max_scroll, 10.0)
        self.assertEqual(config.pacer.min_detents_per_second, 0.02)
        self.assertEqual(config.pacer.max_detents_per_second, 4.0)
        self.assertEqual(config.compat_detent_units, 24000)

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
