# SPDX-License-Identifier: GPL-2.0-or-later
"""Guardrail tests for distinct 3.11 and unqualified 3.12 breakpoint profiles."""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from unittest import mock
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from z8_research_sites import C312_SHA, pc  # noqa: E402


class SiteProfileTests(unittest.TestCase):
    def test_original_311_boot_default_unmodified(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(pc(SimpleNamespace(), "battery_callback", 0x41181504), 0x41181504)
            self.assertEqual(pc(SimpleNamespace(), "lens_controller_reply", 0x4106E690), 0x4106E690)

    def test_explicit_opt_in_required(self):
        with mock.patch.dict(os.environ, {"Z8_C312_SITE_PROFILE": "no-such-profile.json"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "explicit"):
                pc(SimpleNamespace(), "battery_callback", 0x41181504)

    def test_resolves_separate_static_candidates_but_never_claims_qualified(self):
        src = ROOT / "research" / "3.12" / "profiles" / "3.12.json"
        profile = json.loads(src.read_text(encoding="utf-8"))
        self.assertFalse(profile["runtime_qualified"])
        self.assertEqual(profile["sites"]["battery_callback"], "0x4118156c")
        self.assertEqual(profile["sites"]["lens_controller_reply"], "0x4106e6f8")
        self.assertEqual(profile["sites"]["framebuffer_event"], "0x40faca24")
        with tempfile.TemporaryDirectory() as folder:
            fixture = Path(folder) / "synthetic"
            fixture.write_bytes(b"fake-engine")
            g = SimpleNamespace(firmware=fixture, data={})
            fake_digest = SimpleNamespace(hexdigest=lambda: C312_SHA)
            with mock.patch.dict(os.environ, {
                "Z8_C312_SITE_PROFILE": str(src),
                "Z8_C312_ALLOW_UNQUALIFIED_BOOT": "1"}, clear=True), \
                mock.patch("z8_research_sites.hashlib.file_digest", return_value=fake_digest):
                self.assertEqual(pc(g, "battery_callback", 0x41181504), 0x4118156c)
                self.assertEqual(pc(g, "lens_controller_reply", 0x4106e690), 0x4106e6f8)
                self.assertFalse(g.data["unqualified_c312_site_profile"]["runtime_qualified"])
                with self.assertRaisesRegex(RuntimeError, "mismatched"):
                    pc(g, "battery_callback", 0x41181508)

    def test_rejects_unverified_guest_digest(self):
        profile = ROOT / "research" / "3.12" / "profiles" / "3.12.json"
        with tempfile.TemporaryDirectory() as folder:
            fixture = Path(folder) / "synthetic"
            fixture.write_bytes(b"not-a-nikon-image")
            g = SimpleNamespace(firmware=fixture, data={})
            with mock.patch.dict(os.environ, {
                "Z8_C312_SITE_PROFILE": str(profile),
                "Z8_C312_ALLOW_UNQUALIFIED_BOOT": "1"}, clear=True):
                with self.assertRaisesRegex(ValueError, "not valid for this guest"):
                    pc(g, "adc_ready", 0x4033DB98)


if __name__ == "__main__":
    unittest.main()
