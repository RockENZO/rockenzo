# Profile terminal assets

The four `assets/profile-terminal-*.svg` files are self-contained images used by the README and the existing GitHub Pages site. They contain original ASCII lettering, SVG text and declarative SMIL animation. They need no JavaScript, external fonts, network requests or application backend.

Regenerate with Python 3.10+ (standard library only):

```sh
python3 scripts/generate_profile_terminal.py
python3 scripts/generate_profile_terminal.py --check
```

Edit the field data, glyph masks or colors in the generator, then regenerate all four variants. Preserve the original `B1T1.png` header and the README's theme/mobile picture sources.

The About values reveal once in roughly four seconds, then remain visible. A subtle active-line highlight cycles afterward and a decorative terminal cursor blinks. This is a presentation effect, not a live session or execution of the displayed command. `prefers-reduced-motion: reduce` displays the complete static values immediately and hides moving elements. Base SVG text remains present if animation is unsupported. The SVG description and README image alt text provide the factual content without relying on motion.

Before publishing, inspect desktop/mobile and dark/light variants embedded through `<img>`, sample early and completed reveal frames, and check reduced-motion behavior. Actual GitHub/Pages rendering and browser motion preferences can differ; verify the published assets and embedding after deployment. No repository workflow or Pages setting change is required.

## ASCII water background

The ASCII field is a separate background layer. A native SVG turbulence/displacement filter gently refracts that layer on a 14-second loop. The letter faces, amber edges and side volumes are outside the filter and contain no animations. A fixed mask keeps the refracted background out of those letter volumes. This is decorative ASCII image motion, not a fluid simulation or live data.

Reduced-motion users see the original unfiltered static ASCII field. Inspect the art region independently of the About highlight and command cursor when testing temporal changes, and verify that the stationary letter geometry stays unchanged.
