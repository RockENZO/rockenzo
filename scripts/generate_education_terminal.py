#!/usr/bin/env python3
"""Generate the education section as a static terminal-style SVG.

Writes assets/education-terminal-{light,dark}[-mobile].svg. Run from any directory.
--check verifies that tracked assets match this source. No network, fonts,
scripts or animation are used. Progress values are data in PROGRESS below.
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

L = dict(bg='#F7F6FC', bar='#ECE8FB', line='#D9D5EC', fg='#1B2340', muted='#59627F',
         accent='#B45F06', label='#6B4FD3', track='#E4E0F3', fill='#6B4FD3', glow='#B3A1FF',
         dot=('#FF5F57', '#FEBC2E', '#28C840'))
D = dict(bg='#0D1B33', bar='#16284B', line='#1E2D4D', fg='#E8EDF8', muted='#8B9BB4',
         accent='#FF9F43', label='#A78BFA', track='#1E2D4D', fill='#A78BFA', glow='#EDE7FF',
         dot=('#FF5F57', '#FEBC2E', '#28C840'))

MONO = "Menlo,Consolas,ui-monospace,monospace"
DATE_X, TITLE_X = 16, 170
DOTS, DOT_STEP, DOT_R = 24, 7.22, 2.6
# Pulse on in-progress meters: a highlight sweeps the lit dots, then rests.
PULSE_CYCLE, PULSE_SWEEP, PULSE_WIDTH = 5.0, 1.5, .45

# (date, title, lines, progress or None). Progress is the share completed (0..1).
ENTRIES = [
    ('2026 — now', 'Master of Information Technology (Applied AI)',
     ['Adelaide University'], 0.50),
    ('2023 — 2025', 'Bachelor of Information Technology',
     ['University of Adelaide',
      'High Distinction: Applied Programming; Computer Systems, Networks & Security',
      'Distinction: AI Technologies; Web & Database Computing; Programming for IT Specialists'], 1.00),
    ('Sep 2024', 'HackerRank Software Engineer',
     ['problem solving · Python · SQL · REST APIs'], None),
]

R = 14

# Title-bar size label: pixels divided by one character cell (7.5 x 17 px).
CELL_W, CELL_H = 7.5, 17

def term_size(w, h):
    return f'{round(w / CELL_W)}×{round((h - 28) / CELL_H)}'

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

def wrap(s, width):
    return textwrap.wrap(s, width=width, break_long_words=False)

def pulse(cx, cy, i, filled, p):
    peak = PULSE_SWEEP * i / max(filled - 1, 1)
    keys = [0, max(peak - PULSE_WIDTH / 2, 0), peak, peak + PULSE_WIDTH / 2, PULSE_CYCLE]
    times = ';'.join(f'{k / PULSE_CYCLE:.4f}' for k in keys)
    return (f'<circle class="motion" cx="{cx}" cy="{cy}" r="{DOT_R + .5}" fill="{p["glow"]}" opacity="0">'
            f'<animate attributeName="opacity" values="0;0;1;0;0" keyTimes="{times}" dur="{PULSE_CYCLE}s" begin="1s" repeatCount="indefinite"/></circle>')

def build(p, mobile=False, animated=True):
    W = 360 if mobile else 880
    tx = 16 if mobile else TITLE_X
    rows = []
    y = 28 + 44  # title bar plus prompt line
    rows.append(('prompt', y))
    y += 34
    for date, title, lines, prog in ENTRIES:
        y += 8
        if mobile:
            # Narrow layout: date above a wrapped title, details wrapped below.
            rows.append(('date', y, date))
            y += 21
            for part in wrap(title, 40):
                rows.append(('title', y, part))
                y += 19
            y += 3
            lines = [part for line in lines for part in wrap(line, 44)]
        else:
            rows.append(('entry', y, date, title))
            y += 22
        for line in lines:
            rows.append(('line', y, line))
            y += 19
        if prog is not None:
            rows.append(('bar', y, prog))
            y += 24
        y += 6
    total = y + 14
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{total}" viewBox="0 0 {W} {total}" role="img" aria-label="Education and certification as a terminal listing">',
           '<style>@media(prefers-reduced-motion:reduce){.motion{display:none}}</style>' if animated else '',
           f'<defs><clipPath id="win"><path d="{window_shape(W, total)}"/></clipPath></defs>',
           f'<g clip-path="url(#win)"><rect width="{W}" height="{total}" fill="{p["bg"]}"/>',
           f'<path d="M.5 14.5 A14 14 0 0 1 14.5 .5 H{W-14.5} A14 14 0 0 1 {W-.5} 14.5 V28.5 H.5 Z" fill="{p["bar"]}"/>',
           f'<path d="M0 28.5H{W}" stroke="{p["line"]}"/>']
    for i, c in enumerate(p['dot']):
        out.append(f'<circle cx="{14.5+20*i}" cy="14.5" r="5.5" fill="{c}"/>')
    out.append(text(W/2, 18.5, 'Education' if mobile else f'Education — {term_size(W, total)}', 12, p['muted']).replace('<text ', '<text text-anchor="middle" '))
    for r in rows:
        kind = r[0]
        if kind == 'prompt':
            out.append(text(16, r[1] + 2, '~ $', 14, p['accent']))
            out.append(text(16 + 4 * 8.4, r[1] + 2, 'cat education.txt', 14, p['fg']))
        elif kind == 'entry':
            _, yy, date, title = r
            out.append(text(DATE_X, yy, date, 13, p['label']))
            out.append(text(TITLE_X, yy, title, 13, p['fg'], 600))
        elif kind == 'date':
            out.append(text(tx, r[1], r[2], 12, p['label']))
        elif kind == 'title':
            out.append(text(tx, r[1], r[2], 13, p['fg'], 600))
        elif kind == 'line':
            _, yy, line = r
            out.append(text(tx, yy, line, 12, p['muted']))
        elif kind == 'bar':
            _, yy, prog = r
            # Dot meter drawn as circles so it aligns in any viewer font.
            filled = round(DOTS * prog)
            for i in range(DOTS):
                c = p['fill'] if i < filled else p['track']
                cx = round(tx + DOT_STEP * (i + .5), 2)
                out.append(f'<circle cx="{cx}" cy="{yy - 3.5}" r="{DOT_R}" fill="{c}"/>')
                if animated and 0 < prog < 1 and i < filled:
                    out.append(pulse(cx, yy - 3.5, i, filled, p))
            out.append(text(round(tx + DOT_STEP * DOTS + 12, 2), yy + 1, f'{round(prog*100)}%', 12, p['muted']))
    out.append('</g>')
    out.append(f'<path d="{window_shape(W, total)}" fill="none" stroke="{p["line"]}"/>')
    out.append('</svg>')
    return total, ''.join(out)

for label, p in [('light', L), ('dark', D)]:
    for mobile in (False, True):
        stem = f'education-terminal-{label}{"-mobile" if mobile else ""}'
        emit(f'{stem}.svg', build(p, mobile)[1])
        # Picture sources choose this one under reduced motion, as the profile card does.
        emit(f'{stem}-static.svg', build(p, mobile, animated=False)[1])

if mismatches:
    raise SystemExit('Generated assets differ: ' + ', '.join(mismatches))
print('Education SVGs match the generator.' if args.check else 'Generated education terminal SVGs.')
