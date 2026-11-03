"""Checks for the generated profile's loop and embedding contracts (stdlib only)."""
import bisect
import contextlib
import io
from pathlib import Path
import runpy
import sys
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NS = {"s": "http://www.w3.org/2000/svg"}

class ProfileTerminalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = ROOT / "scripts/generate_profile_terminal.py"
        with patch.object(sys, "argv", [str(source), "--check"]), contextlib.redirect_stdout(io.StringIO()):
            cls.model = runpy.run_path(str(source))
        cls.assets = list((ROOT / "assets").glob("profile-terminal-*.svg"))

    def test_wave_loop_closes_and_changes(self):
        rows = self.model["wave_rows"]
        self.assertEqual(rows(0), rows(1))
        first, later = "".join(rows(0)), "".join(rows(.25))
        self.assertGreater(sum(a != b for a, b in zip(first, later)), len(first) * .1)

    def test_single_visible_frame_without_gaps(self):
        for asset in self.assets:
            with self.subTest(asset=asset.name):
                root = ET.parse(asset)
                frames = root.findall('.//s:g[@class="wave-frame"]', NS)
                self.assertEqual(len(frames), 72)
                schedules = []
                boundaries = {0., 1.}
                for frame in frames:
                    animation = frame.find('s:animate', NS)
                    times = list(map(float, animation.get("keyTimes").split(";")))
                    values = animation.get("values").split(";")
                    boundaries.update(times)
                    schedules.append((times, values))
                ordered = sorted(boundaries)
                samples = ordered + [(a+b)/2 for a,b in zip(ordered, ordered[1:])]
                for phase in samples:
                    t = phase % 1
                    visible = sum(values[bisect.bisect_right(times,t)-1] == "visible" for times,values in schedules)
                    self.assertEqual(visible, 1, (asset.name,phase))

    def test_open_plane_sampling_and_shared_letter_geometry(self):
        sample = self.model["field_character"]
        for x, y in [(-10,27),(90,-10),(41,70)]:
            values = {sample(x,y,i/8) for i in range(8)}
            self.assertGreater(len(values), 1, (x,y))
            self.assertEqual(sample(x,y,0), sample(x,y,1))
        for asset in self.assets:
            root = ET.parse(asset)
            letters = root.find('.//s:g[@id="fixed-rock-letters"]/s:use', NS)
            clearance = root.find('.//s:mask[@id="fixed-letter-clearance"]/s:use', NS)
            self.assertEqual(letters.get("href"), "#rock-glyphs")
            self.assertEqual(clearance.get("href"), letters.get("href"))
            self.assertIsNotNone(root.find('.//s:radialGradient[@id="wave-feather"]', NS))

    def test_image_size_and_stationary_letter_contract(self):
        self.assertEqual(len(self.assets), 4)
        for asset in self.assets:
            with self.subTest(asset=asset.name):
                self.assertLess(asset.stat().st_size, 1_000_000)
                root = ET.parse(asset)
                letters = root.find('.//s:g[@id="fixed-rock-letters"]', NS)
                self.assertIsNotNone(letters)
                self.assertFalse(letters.findall('.//s:animate', NS))
                self.assertFalse(letters.findall('.//s:animateTransform', NS))
                self.assertFalse(root.findall('.//s:script', NS))
                self.assertFalse(root.findall('.//s:foreignObject', NS))
                self.assertIsNotNone(root.find('.//s:g[@class="still water-static"]', NS))

if __name__ == "__main__":
    unittest.main()
