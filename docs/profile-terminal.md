# Profile terminal assets

The four animated and four explicit static `assets/profile-terminal-*.svg` files are self-contained images used by the README and the existing GitHub Pages site. They contain original geometric lettering and an ASCII background, SVG text and declarative SMIL animation. They need no JavaScript, external fonts, network requests or application backend.

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

The ASCII field is a separate background layer. The generator precomputes 72 ASCII frames (nine frames per second) for an eight-second loop. Five holes expand and contract at staggered phases, and outward-travelling radial wave amplitudes are summed before character quantization. Native SVG visibility animation selects one frame at a time. The flat geometric glyphs have chamfered corners and approximately uniform 12-unit stems; their original SVG paths are filled with stationary, literal ASCII text from a small repeating SVG pattern. An unobtrusive subpixel contour keeps the shape readable at small sizes; there is no offset shadow or extrusion. No external font is loaded. The paths live outside the water frame group. Foreground and clearance-mask instances reference the exact same glyph geometry and receive identical per-letter motion tracks. This is a periodic visual interference model, not a physical fluid solver or an optical diffraction benchmark.

Reduced-motion users see the original unfiltered static ASCII field. Check that exactly one background frame is visible at each sample, that the loop closes, and that source radii peak at different times. Inspect the art region independently of the About highlight and command cursor when testing temporal changes, and verify that each letter and its mask follow the same motion track.

The ASCII rows use explicit `textLength` and `lengthAdjust="spacingAndGlyphs"` to pin the character advance across Menlo, Consolas and monospace font fallbacks; the letter-clearance mask now uses the exact vector glyphs rather than font-dependent pixel runs. Check per-character positions when changing the grid metrics.

## Open-plane wave sampling

`field_character(x, y, phase)` evaluates the radial-wave expression for arbitrary coordinates, including positions beyond the visible region. There is no edge reflection, wrapping or viewport clamping in the field model. The SVG aperture is only an observation window: a soft elliptical feather hides the rendered grid boundaries without changing the travelling waves. Off-window waves continue mathematically; invisible pixels are not needlessly rendered.

## Terminal character fill

The modern glyph outlines are unchanged. Their fill is a repeating pair of literal ASCII text rows (`#+=/#+` and `=/#+=/`), not a raster texture or external font. Explicit textLength/spacingAndGlyphs keeps the tile width stable across fallback fonts. The character pattern has no internal animation or noise; it moves rigidly with each suspended glyph. Water, About and command animations retain independent timelines.

## Independent suspended letters

Four glyphs use separate periodic tracks (R 7.4 s, O 5.8 s, C 8.6 s, K 6.6 s), independent of the eight-second water loop. The generator samples the periodic steady-state response of a common mass/spring/damper equation under a multi-harmonic drive. Mass, stiffness, damping and phase differ per letter; each axis is normalized to a small visual displacement/tilt budget. These are visual design units, not measured material properties. Each 73-point track closes exactly and SVG interpolates continuously between the samples.

The foreground and its clearance-mask instances share the same geometry and identical translation/rotation tracks. This is geometric occlusion only: water never drives the letters and the letters do not alter the wave propagation model. Previously baked-in letter holes are removed from the moving water frames so vacated positions do not leave ghost silhouettes. The wave sources, equations, timing, frame rate and feathered observation aperture stay unchanged.

Reduced motion hides all suspended foreground/mask instances and selects the original static glyphs and static field. Inspect both normal and reduced-motion variants when updating the trajectories.

The README's picture sources explicitly select the four `-static.svg` files when the parent page matches `prefers-reduced-motion: reduce`, before the animated theme/mobile sources. This avoids relying on reduced-motion propagation into an SVG img document, which did not respond reliably to browser emulation during the embedding checks. Static files omit motion groups and all animation elements, and retain the complete text and unfiltered field. The standalone animated SVG's CSS fallback remains available too.

The desktop art caption cycles through meaningful project-focus phrases using typing, pause and deletion; the compact mobile card omits this caption. Static variants retain the first phrase. The tool labels use Codex, Claude Code and DeepSeek Harness; Hugging Face and Ollama remain, while Streamlit is listed under Core. README alt text and SVG descriptions carry the same tool names.
