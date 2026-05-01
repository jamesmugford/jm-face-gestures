import os
import unittest
from unittest.mock import patch

import jm_eyebrow_scroll


class BackendSelectionTests(unittest.TestCase):
    def test_explicit_backend_is_used(self):
        self.assertEqual(
            jm_eyebrow_scroll._select_linux_backend("uinput-hires"),
            "uinput-hires",
        )

    def test_wayland_auto_prefers_uinput_hires(self):
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=True):
            with patch.object(
                jm_eyebrow_scroll,
                "_can_use_uinput_hires",
                return_value=True,
            ):
                self.assertEqual(
                    jm_eyebrow_scroll._select_linux_backend("auto"),
                    "uinput-hires",
                )

    def test_wayland_auto_requires_uinput_hires(self):
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}, clear=True):
            with patch.object(
                jm_eyebrow_scroll,
                "_can_use_uinput_hires",
                return_value=False,
            ):
                with self.assertRaises(RuntimeError):
                    jm_eyebrow_scroll._select_linux_backend("auto")

    def test_x11_auto_uses_xtest(self):
        with patch.dict(os.environ, {"DISPLAY": ":0"}, clear=True):
            with patch.object(
                jm_eyebrow_scroll,
                "_can_use_uinput_hires",
                return_value=True,
            ):
                self.assertEqual(
                    jm_eyebrow_scroll._select_linux_backend("auto"),
                    "xtest",
                )

    def test_single_wayland_backend_defaults_are_conservative(self):
        config = jm_eyebrow_scroll.DEFAULT_LINUX_SCROLL_CONFIG

        self.assertEqual(config.min_detents_per_second, 0.03)
        self.assertEqual(config.max_detents_per_second, 18.0)
        self.assertEqual(config.compat_detent_units, 48000)


if __name__ == "__main__":
    unittest.main()
