#!/usr/bin/env python3
"""Generate the featured-projects terminal panes as static SVGs.

Writes assets/projects-*.svg in light and dark palettes, plus 360px -mobile variants. Run from any
directory. --check verifies that tracked assets match this source.
No network, fonts, scripts or animation are used.
"""
from pathlib import Path
import argparse
import html
import textwrap

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check', action='store_true', help='verify assets without writing')
args = parser.parse_args()
ASSETS = Path(__file__).resolve().parents[1] / 'assets'
mismatches = []

def emit(name, content):
    path = ASSETS / name
    if args.check:
        if not path.is_file() or path.read_text() != content:
            mismatches.append(name)
    else:
        path.write_text(content)

L = dict(bg='#F7F6FC', bar='#ECE8FB', line='#D9D5EC', pane='#FBFAFF', fg='#1B2340',
         muted='#59627F', accent='#B45F06', label='#6B4FD3', dot=('#FF5F57', '#FEBC2E', '#28C840'))
D = dict(bg='#0D1B33', bar='#16284B', line='#1E2D4D', pane='#0F2140', fg='#E8EDF8',
         muted='#8B9BB4', accent='#FF9F43', label='#A78BFA', dot=('#FF5F57', '#FEBC2E', '#28C840'))

W = 880
MONO = "Menlo,Consolas,ui-monospace,monospace"

FEATURED = [
    ('datapipeline-etl', 'Knia Maps', 'Geospatial ETL for Sydney accessibility mapping, with Elasticsearch, PostgreSQL and Docker, plus reproducible integration tests.', 'https://github.com/RockENZO/datapipeline-etl'),
    ('NLP-Cyber-Harm-Detection', "CSIRO's Data61", 'Nine-class scam detection with macro F1 0.948 on an 18,261-record, template-grouped internal test.', 'https://github.com/RockENZO/NLP-Cyber-Harm-Detection'),
    ('data', 'Fraud dataset', 'A reproducible corpus of 194,913 scam and legitimate samples from 19 retained source datasets, with verified hashes.', 'https://github.com/RockENZO/data'),
    ('Automatic-web-scraper-with-LLM-parsing', 'LLM web scraper', 'Local LLMs extract structured webpage data with traceable source evidence. Field exact-match F1 0.938 on 16 synthetic HTML fixtures.', 'https://github.com/RockENZO/Automatic-web-scraper-with-LLM-parsing'),
    ('MyWeather', 'MyWeather', 'SwiftUI weather app with location-based OpenWeatherMap forecasts, animated transitions and Liquid Glass cards.', 'https://github.com/RockENZO/MyWeather'),
    ('ML-object-detection-project', 'Football match analysis', 'Experimental YOLOv8s football detection, player tracking and pitch mapping, with a match viewer for one 30-second clip.', 'https://github.com/RockENZO/ML-object-detection-project'),
]
MORE = [
    ('odyssey', 'a terminal coding agent with 17 tools and local Ollama inference'),
    ('MagicTrick', 'an iOS card trick with no buttons, only rotate, shake and a secret tap'),
    ('ControllerMouse', "drive your Mac's cursor with a game controller from the menu bar"),
    ('Road_Semantic_Segmentation_CV', 'PyTorch segmentation for driving scenes, with mIoU and FLOPs ablations'),
    ('flappy_bird_dqn-main', 'a DQN agent that learns to play Flappy Bird'),
]

R = 14

def window_shape(w, h, top=True, bottom=True):
    """Closed outline of a window section; rounded only where it is an outer edge."""
    x0, y0, x1, y1 = .5, .5, w - .5, h - .5
    d = [f'M{x0} {y0 + R if top else y0}']
    d.append(f'A{R} {R} 0 0 1 {x0 + R} {y0} H{x1 - R} A{R} {R} 0 0 1 {x1} {y0 + R}' if top else f'H{x1}')
    d.append(f'V{y1 - R} A{R} {R} 0 0 1 {x1 - R} {y1} H{x0 + R} A{R} {R} 0 0 1 {x0} {y1 - R}' if bottom else f'V{y1} H{x0}')
    return ' '.join(d) + ' Z'

def window_border(w, h, top=True, bottom=True):
    """Outline stroke that leaves seams between stacked images open."""
    x0, y0, x1, y1 = .5, .5, w - .5, h - .5
    if top and bottom:
        return window_shape(w, h)
    if top:
        return f'M{x0} {y1 + .5} V{y0 + R} A{R} {R} 0 0 1 {x0 + R} {y0} H{x1 - R} A{R} {R} 0 0 1 {x1} {y0 + R} V{y1 + .5}'
    return f'M{x0} {y0 - .5} V{y1 - R} A{R} {R} 0 0 0 {x0 + R} {y1} H{x1 - R} A{R} {R} 0 0 0 {x1} {y1 - R} V{y0 - .5}'

def esc(s):
    return html.escape(s, quote=True)

def text(x, y, s, size, fill, weight=None):
    w = f' font-weight="{weight}"' if weight else ''
    return f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{fill}"{w} xml:space="preserve">{esc(s)}</text>'

def window_top(p, title):
    out = [f'<rect x=".5" y=".5" width="{W-1}" height="0" rx="14" fill="{p["bg"]}"/>']
    out.append(f'<path d="M.5 14.5 A14 14 0 0 1 14.5 .5 H{W-14.5} A14 14 0 0 1 {W-.5} 14.5 V28.5 H.5 Z" fill="{p["bar"]}"/>')
    for i, c in enumerate(p['dot']):
        out.append(f'<circle cx="{14.5+20*i}" cy="14.5" r="5.5" fill="{c}"/>')
    out.append(text(W/2, 18.5, title, 12, p['muted']).replace('<text ', '<text text-anchor="middle" '))
    out.append(f'<path d="M0 28.5H{W}" stroke="{p["line"]}"/>')
    return ''.join(out)

def wrap(s, width):
    return textwrap.wrap(s, width=width, break_long_words=False)

def featured_svg(p, mobile=False):
    cols = 1 if mobile else 2
    pane_w = W // cols
    chars = 44 if mobile else 52
    heights = []
    rows = []
    for r in range(0, len(FEATURED), cols):
        pair = FEATURED[r:r+cols]
        h = 0
        for _, name, desc, link in pair:
            lines = wrap(desc, chars)
            h = max(h, 26 + 14 + 20 + len(lines) * 17 + 24 + 14)
        rows.append((r, pair, h))
        heights.append(h)
    prompt_h = 40
    total = 28 + prompt_h + sum(heights) + 1
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{total}" viewBox="0 0 {W} {total}" role="img" aria-label="Featured projects, shown as split terminal panes">',
           f'<defs><clipPath id="win"><path d="{window_shape(W, total, bottom=False)}"/></clipPath></defs>',
           f'<g clip-path="url(#win)"><rect width="{W}" height="{total}" fill="{p["bg"]}"/>',
           window_top(p, 'Projects' if mobile else 'Projects — tmux 120×30'),
           text(16, 28 + 26, '~ $ ls projects/ --featured', 14, p['accent'])]
    y = 28 + prompt_h
    out.append(f'<path d="M0 {y+.5}H{W}" stroke="{p["line"]}"/>')
    for r, pair, h in rows:
        for col, (repo, name, desc, _) in enumerate(pair):
            x = col * pane_w
            out.append(f'<rect x="{x}" y="{y}" width="{pane_w}" height="{h}" fill="{p["bg"]}"/>')
            out.append(f'<rect x="{x}" y="{y}" width="{pane_w}" height="26" fill="{p["pane"]}"/>')
            out.append(text(x + 14, y + 17, repo, 11, p['muted']))
            out.append(f'<path d="M{x+pane_w-.5} {y}V{y+h}" stroke="{p["line"]}"/>' if col == 0 and cols > 1 else '')
            out.append(f'<path d="M{x} {y+26.5}H{x+pane_w}" stroke="{p["line"]}"/>')
            out.append(text(x + 14, y + 26 + 24, name, 13, p['label']))
            ty = y + 26 + 24 + 20
            for line in wrap(desc, chars):
                out.append(text(x + 14, ty + 12, line, 12, p['fg']))
                ty += 17
        y += h
        out.append(f'<path d="M0 {y+.5}H{W}" stroke="{p["line"]}"/>')
    out.append('</g>')
    out.append(f'<path d="{window_border(W, total, bottom=False)}" fill="none" stroke="{p["line"]}"/>')
    out.append('</svg>')
    return ''.join(out)

def summary_svg(p):
    h = 44
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{h}" viewBox="0 0 {W} {h}" role="img" aria-label="More projects, 5 hidden">',
           f'<path d="{window_shape(W, h, top=False)}" fill="{p["bg"]}"/>',
           text(16, 27, '▸ more projects', 14, p['accent']),
           text(16 + 14 * 0.6 * 17, 27, f'({len(MORE)})', 14, p['muted']),
           f'<path d="{window_border(W, h, top=False)}" fill="none" stroke="{p["line"]}"/>',
           '</svg>']
    return ''.join(out)

def more_svg(p, mobile=False):
    if mobile:
        return more_svg_mobile(p)
    lines = []
    for name, desc in MORE:
        lines.append((name, desc))
    row_h = 26
    body = 16 + len(lines) * row_h + 10
    total = body
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{total}" viewBox="0 0 {W} {total}" role="img" aria-label="Five more projects">',
           f'<path d="{window_shape(W, total)}" fill="{p["bg"]}"/>']
    y = 16 + 16
    for name, desc in lines:
        out.append(text(16, y, name, 13, p['label'], 600))
        out.append(text(16 + 14 * 0.6 * 30, y, desc, 12, p['fg']))
        y += row_h
    out.append(f'<path d="{window_shape(W, total)}" fill="none" stroke="{p["line"]}"/>')
    out.append('</svg>')
    return ''.join(out)

def more_svg_mobile(p):
    """Narrow list: each name on its own line with the description wrapped below."""
    rows = [(name, wrap(desc, 44)) for name, desc in MORE]
    total = 16 + sum(20 + 17 * len(d) + 10 for _, d in rows) + 6
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{total}" viewBox="0 0 {W} {total}" role="img" aria-label="Five more projects">',
           f'<path d="{window_shape(W, total)}" fill="{p["bg"]}"/>']
    y = 16 + 16
    for name, desc in rows:
        out.append(text(16, y, name, 13, p['label'], 600))
        y += 20
        for line in desc:
            out.append(text(16, y, line, 12, p['fg']))
            y += 17
        y += 10
    out.append(f'<path d="{window_shape(W, total)}" fill="none" stroke="{p["line"]}"/>')
    out.append('</svg>')
    return ''.join(out)

for mobile in (False, True):
    W = 360 if mobile else 880
    sfx = '-mobile' if mobile else ''
    for label, p in [('light', L), ('dark', D)]:
        emit(f'projects-featured-{label}{sfx}.svg', featured_svg(p, mobile))
        emit(f'projects-more-summary-{label}{sfx}.svg', summary_svg(p))
        emit(f'projects-more-{label}{sfx}.svg', more_svg(p, mobile))

if mismatches:
    raise SystemExit('Generated assets differ: ' + ', '.join(mismatches))
print('Projects SVGs match the generator.' if args.check else 'Generated projects terminal panes.')
