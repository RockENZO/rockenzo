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
        cls.assets = [p for p in (ROOT / "assets").glob("profile-terminal-*.svg") if "-static" not in p.stem]

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
            self.assertEqual(letters.get("href"), "#rock-glyphs")
            self.assertIsNotNone(root.find('.//s:radialGradient[@id="wave-feather"]', NS))

    def test_animated_water_uses_no_live_masks(self):
        for asset in self.assets:
            with self.subTest(asset=asset.name):
                root = ET.parse(asset)
                water = root.find('.//s:g[@class="motion water-background"]', NS)
                self.assertIsNotNone(water)
                self.assertNotIn("mask", water.attrib)
                self.assertIsNone(root.find('.//s:mask[@id="fixed-letter-clearance"]', NS))
                # No ancestor of the animated water may be masked either.
                parents = {child: parent for parent in root.iter() for child in parent}
                node = water
                while node in parents:
                    node = parents[node]
                    self.assertNotIn("mask", node.attrib)
                self.assertIsNotNone(root.find('.//s:rect[@id="wave-aperture-veil"]', NS))
                self.assertIsNotNone(root.find('.//s:radialGradient[@id="wave-veil"]', NS))
                clearance = root.find('.//s:g[@id="letter-clearance"]', NS)
                self.assertEqual(clearance.get("fill"), clearance.get("stroke"))

    def test_split_flap_rows_and_static_fill(self):
        for pair in self.model['FLAP_STATES']:
            self.assertTrue(all(text.isascii() and len(text) == 6 for text in pair))
        starts = []
        for row in range(self.model['FLAP_ROWS']):
            times, scales, changes, states = self.model['flap_schedule'](row)
            self.assertEqual(times, sorted(set(times)))
            self.assertEqual(changes, sorted(set(changes)))
            self.assertEqual((scales[0], scales[-1]), (1., 1.))
            self.assertEqual((states[0], states[-1]), (0, 0))
            self.assertEqual(len(times), len(scales))
            self.assertEqual(len(changes), len(states))
            self.assertTrue(all(.08 <= value <= 1 for value in scales))
            self.assertTrue(all(0 <= value < len(self.model['FLAP_STATES']) for value in states))
            self.assertLess(times[-2], 5)
            starts.append(times[1])
        self.assertEqual(len(set(starts)), self.model['FLAP_ROWS'])
        upper_end = self.model['flap_schedule'](self.model['FLAP_GROUP_ROWS'] - 1)[0][-2]
        lower_start = self.model['flap_schedule'](self.model['FLAP_GROUP_ROWS'])[0][1]
        self.assertGreater(lower_start, upper_end)
        self.assertLess(lower_start - upper_end, .05)
        self.assertEqual([self.model['flap_band_y'](row) for row in range(14)],
                         [0,12,24,36,48,60,72]*2)
        for asset in self.assets:
            root = ET.parse(asset)
            fill = root.find('.//s:pattern[@id="rock-ascii-fill"]', NS)
            self.assertEqual(fill.get('height'), '84')
            lower = root.find('.//s:pattern[@id="rock-ascii-fill-lower"]', NS)
            self.assertEqual(lower.get('height'), '84')
            for letter in 'ROCK':
                use = root.find(f'.//s:g[@id="fore-{letter}"]//s:use', NS)
                if letter in 'CK':
                    self.assertEqual(use.get('fill'), 'url(#rock-ascii-fill-lower)')
                else:
                    self.assertIsNone(use.get('fill'))
            self.assertEqual(len(fill.findall('./s:g', NS)) + len(lower.findall('./s:g', NS)), self.model['FLAP_ROWS'])
            self.assertEqual(len(fill.findall('.//s:animate', NS)) + len(lower.findall('.//s:animate', NS)), self.model['FLAP_ROWS'])
            self.assertEqual(len(fill.findall('.//s:animateTransform', NS)) + len(lower.findall('.//s:animateTransform', NS)), self.model['FLAP_ROWS'])
            still = root.find('.//s:pattern[@id="rock-ascii-fill-static"]', NS)
            self.assertEqual([text.text for text in still.findall('.//s:text', NS)], list(self.model['FLAP_STATES'][0]))
            letters = root.find('.//s:g[@id="fixed-rock-letters"]/s:use', NS)
            self.assertEqual(letters.get('fill'), 'url(#rock-ascii-fill-static)')

    def test_suspension_is_bounded_closed_and_independent(self):
        tracks = self.model["TRACKS"]
        configs = self.model["SUSPENSION"]
        self.assertEqual(len({track["period"] for track in tracks.values()}), 4)
        for letter, track in tracks.items():
            self.assertNotEqual(track["period"], self.model["WAVE_SECONDS"])
            for axis, limit in [("x",configs[letter]["x"]),("y",configs[letter]["y"]),("tilt",configs[letter]["tilt"])]:
                self.assertEqual(track[axis][0], track[axis][-1])
                self.assertGreater(max(track[axis])-min(track[axis]), .1)
                self.assertLessEqual(max(map(abs,track[axis])), limit+.00001)
        for asset in self.assets:
            root = ET.parse(asset)
            for letter in tracks:
                fore = root.find(f'.//s:g[@id="fore-{letter}"]', NS)
                mask = root.find(f'.//s:g[@id="mask-{letter}"]', NS)
                self.assertIsNotNone(fore)
                self.assertIsNotNone(mask)
                for front, clearance in zip(fore.findall('.//s:animateTransform',NS), mask.findall('.//s:animateTransform',NS)):
                    self.assertEqual(front.attrib, clearance.attrib)
                    self.assertNotIn("begin", front.attrib)
                self.assertEqual(len(fore.findall('.//s:animateTransform', NS)),2)
                self.assertEqual(fore.find('.//s:use',NS).get("href"), f"#glyph-{letter}")
                self.assertEqual(mask.find('.//s:use',NS).get("href"), f"#glyph-{letter}")

    def test_explicit_static_picture_fallback(self):
        assets = list((ROOT / "assets").glob("profile-terminal-*-static.svg"))
        self.assertEqual(len(assets),4)
        readme = (ROOT / "README.md").read_text()
        # Four reduced-motion sources each for the profile and education pictures.
        self.assertEqual(readme.count("prefers-reduced-motion: reduce"),8)
        for asset in assets:
            self.assertIn("assets/"+asset.name,readme)
            root=ET.parse(asset)
            self.assertFalse(root.findall('.//s:animate',NS))
            self.assertFalse(root.findall('.//s:animateTransform',NS))
            self.assertFalse(root.findall('.//s:g[@class="wave-frame"]',NS))
            self.assertIsNotNone(root.find('.//s:g[@id="fixed-rock-letters"]',NS))
            self.assertLess(asset.stat().st_size,50_000)

    def test_education_pulse_has_static_fallback(self):
        statics = list((ROOT / "assets").glob("education-terminal-*-static.svg"))
        self.assertEqual(len(statics),4)
        readme = (ROOT / "README.md").read_text()
        for asset in statics:
            self.assertIn("assets/"+asset.name,readme)
            self.assertFalse(ET.parse(asset).findall('.//s:animate',NS))
            animated = ROOT / "assets" / asset.name.replace("-static","")
            # Only the in-progress meter pulses: twelve lit dots, one animation each.
            self.assertEqual(len(ET.parse(animated).findall('.//s:animate',NS)),12)

    def test_headline_types_holds_deletes_and_closes(self):
        words = self.model['HEADLINE_WORDS']
        self.assertEqual(words, ['Praxis.', 'Palimpsest.', 'Autopoiesis.'])
        events, duration = self.model['headline_timeline']()
        self.assertEqual(events[0][1:], events[-1][1:])
        self.assertEqual(events[-1][0], duration)
        self.assertEqual([t for t,_,_ in events], sorted(set(t for t,_,_ in events)))
        for active, word in enumerate(words):
            samples = [(t,count) for t,current,count in events if current == active]
            full_index = next(i for i,(_,current,count) in enumerate(events) if current == active and count == len(word))
            self.assertAlmostEqual(events[full_index+1][0]-events[full_index][0], 2.05)
            self.assertTrue(all(0 <= count <= len(word) for _,count in samples))
            self.assertTrue(any(count == 0 for _,count in samples))
        for asset in self.assets:
            root = ET.parse(asset)
            headline = root.find('.//s:g[@id="profile-headline"]', NS)
            self.assertIsNotNone(headline)
            for text in headline.findall('.//s:text', NS):
                right = float(text.get('x')) + len(text.text)*float(text.get('font-size'))*.603
                self.assertLess(right+float(text.get('font-size'))*.603, float(root.getroot().get('width'))-12)
            self.assertNotIn('Make it tangible.', asset.read_text())
        for asset in (ROOT/'assets').glob('profile-terminal-*-static.svg'):
            headline = ET.parse(asset).find('.//s:g[@id="profile-headline"]', NS)
            self.assertEqual([text.text for text in headline.findall('.//s:text', NS)], ['Praxis.'])

    def test_decorative_macos_window_controls(self):
        for asset in self.assets + list((ROOT/'assets').glob('profile-terminal-*-static.svg')):
            controls = ET.parse(asset).find('.//s:g[@id="window-controls"]', NS)
            self.assertEqual(controls.get('aria-hidden'), 'true')
            dots = controls.findall('s:circle', NS)
            self.assertEqual([dot.get('fill') for dot in dots], ['#FF5F57','#FEBC2E','#28C840'])
            self.assertNotIn('ROCK / FIELD NOTES', asset.read_text())

    def test_terminal_titlebar_differs_from_body_and_has_window_title(self):
        for asset in self.assets + list((ROOT/'assets').glob('profile-terminal-*-static.svg')):
            with self.subTest(asset=asset.name):
                root = ET.parse(asset)
                background = root.find('s:rect', NS)
                titlebar = root.find('.//s:rect[@id="titlebar"]', NS)
                self.assertIsNotNone(background)
                self.assertIsNotNone(titlebar)
                self.assertNotEqual(background.get('fill'), titlebar.get('fill'))
                self.assertEqual(titlebar.get('clip-path'), 'url(#window-clip)')
                self.assertEqual(float(titlebar.get('height')), 28)
                title = root.find('.//s:text[@id="window-title"]', NS)
                self.assertIsNotNone(title)
                # Desktop label is cols×rows: size in pixels over a 7.5 x 17 px cell.
                size = f"{round(float(root.getroot().get('width')) / 7.5)}×{round((float(root.getroot().get('height')) - 28) / 17)}"
                expected = 'Profile' if '-mobile' in asset.stem else f'Profile — {size}'
                self.assertEqual(title.text, expected)
                self.assertEqual(title.get('text-anchor'), 'middle')
                controls = root.find('.//s:g[@id="window-controls"]', NS)
                dots = controls.findall('s:circle', NS)
                self.assertEqual([dot.get('cy') for dot in dots], ['14.5'] * 3)
                self.assertEqual([dot.get('cx') for dot in dots], ['14.5', '34.5', '54.5'])
                # The red lamp's centre coincides with the window's top-left corner-radius centre.
                self.assertEqual((dots[0].get('cx'), dots[0].get('cy')), ('14.5', '14.5'))

    def test_command_cursor_stays_with_typing_and_deletion(self):
        for asset in self.assets:
            root = ET.parse(asset)
            area = root.find('.//s:g[@id="command-area"]', NS)
            self.assertIsNotNone(area)
            saw_typing = saw_deleting = saw_hold_blink = False
            for j in range(3):
                clip = area.find(f'.//s:clipPath[@id="command-{j}"]/s:rect', NS)
                reveal = clip.find('s:animate', NS)
                widths = list(map(float, reveal.get('values').split(';')))
                cursor = area.find(f'.//s:rect[@id="command-cursor-{j}"]', NS)
                position = cursor.find('s:animate[@attributeName="x"]', NS)
                opacity = cursor.find('s:animate[@attributeName="opacity"]', NS)
                self.assertEqual(position.get('keyTimes'), reveal.get('keyTimes'))
                self.assertEqual(opacity.get('keyTimes'), reveal.get('keyTimes'))
                self.assertEqual(opacity.get('dur'), reveal.get('dur'))
                positions = list(map(float, position.get('values').split(';')))
                visible = list(map(float, opacity.get('values').split(';')))
                text = area.find(f'.//s:text[@clip-path="url(#command-{j})"]', NS)
                self.assertEqual(text.get('lengthAdjust'), 'spacingAndGlyphs')
                self.assertAlmostEqual(float(text.get('textLength')), max(widths))
                origin = float(clip.get('x'))
                for i,(width,x) in enumerate(zip(widths,positions)):
                    self.assertAlmostEqual(x-origin,width,places=4)
                    local = i/10-j*4
                    if not 0 <= local < 4: continue
                    if local < 3.2 and width < max(widths) or local >= 3.2:
                        self.assertEqual(visible[i],1)
                    if i and width != widths[i-1]:
                        self.assertEqual(visible[i],1)
                        saw_typing |= width > widths[i-1]
                        saw_deleting |= width < widths[i-1]
                    saw_hold_blink |= width == max(widths) and visible[i] == 0
            self.assertTrue(saw_typing and saw_deleting and saw_hold_blink)

    def test_requested_profile_copy(self):
        self.assertEqual(len(self.model["CAPTION_PHRASES"]),3)
        for asset in self.assets + list((ROOT/"assets").glob("profile-terminal-*-static.svg")):
            text=asset.read_text()
            for tool in ["Codex","Claude Code","DeepSeek Harness"]:
                self.assertIn(tool,text)
            self.assertNotIn("OpenAI",text)
            self.assertNotIn("ROCK / WAVE STUDY",text)
            self.assertNotIn("GEOMETRIC TYPE / ASCII FIELD",text)
            if "mobile" not in asset.name:
                self.assertIn(self.model["CAPTION_PHRASES"][0],text)
        readme=(ROOT/"README.md").read_text()
        self.assertIn("Codex, Claude Code, DeepSeek Harness",readme)

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
