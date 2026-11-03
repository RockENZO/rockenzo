# Profile terminal assets

The four `assets/profile-terminal-*.svg` files are self-contained images used by the README and the existing GitHub Pages site. They contain original geometric lettering and an ASCII background, SVG text and declarative SMIL animation. They need no JavaScript, external fonts, network requests or application backend.

Regenerate with Python 3.10+ (standard library only):

```sh
python3 scripts/generate_profile_terminal.py
python3 scripts/generate_profile_terminal.py --check
python3 -m unittest discover -s tests
```

Edit the field data, glyph masks or colors in the generator, then regenerate all four variants. Preserve the original `B1T1.png` header and the README's theme/mobile picture sources.

The About values reveal once in roughly four seconds, then remain visible. A subtle active-line highlight cycles afterward and a decorative terminal cursor blinks. This is a presentation effect, not a live session or execution of the displayed command. `prefers-reduced-motion: reduce` displays the complete static values immediately and hides moving elements. Base SVG text remains present if animation is unsupported. The SVG description and README image alt text provide the factual content without relying on motion.

Before publishing, inspect desktop/mobile and dark/light variants embedded through `<img>`, sample early and completed reveal frames, and check reduced-motion behavior. Actual GitHub/Pages rendering and browser motion preferences can differ; verify the published assets and embedding after deployment. No repository workflow or Pages setting change is required.

## ASCII water background

The ASCII field is a separate background layer. The generator precomputes 72 ASCII frames (nine frames per second) for an eight-second loop. Five holes expand and contract at staggered phases, and outward-travelling radial wave amplitudes are summed before character quantization. Native SVG visibility animation selects one frame at a time. The flat, filled geometric glyphs have chamfered corners and approximately uniform 12-unit stems; they use original SVG paths, with no external font, shadow, extrusion or rim layer. The paths live outside the animated frame group. A fixed clearance mask references the exact same paths, so the background cannot drift into the letters due to font fallback. This is a periodic visual interference model, not a physical fluid solver or an optical diffraction benchmark.

Reduced-motion users see the original unfiltered static ASCII field. Check that exactly one background frame is visible at each sample, that the loop closes, and that source radii peak at different times. Inspect the art region independently of the About highlight and command cursor when testing temporal changes, and verify that the stationary letter geometry stays unchanged.

The ASCII rows use explicit `textLength` and `lengthAdjust="spacingAndGlyphs"` to pin the character advance across Menlo, Consolas and monospace font fallbacks; the letter-clearance mask now uses the exact vector glyphs rather than font-dependent pixel runs. Check per-character positions when changing the grid metrics.

## Open-plane wave sampling

`field_character(x, y, phase)` evaluates the radial-wave expression for arbitrary coordinates, including positions beyond the visible region. There is no edge reflection, wrapping or viewport clamping in the field model. The SVG aperture is only an observation window: a soft elliptical feather hides the rendered grid boundaries without changing the travelling waves. Off-window waves continue mathematically; invisible pixels are not needlessly rendered.
