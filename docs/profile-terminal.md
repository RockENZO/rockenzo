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
