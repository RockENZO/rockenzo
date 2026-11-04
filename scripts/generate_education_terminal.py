#!/usr/bin/env python3
"""Generate the education section as a static terminal-style SVG.

Writes assets/education-terminal-{light,dark}.svg. Run from any directory.
--check verifies that tracked assets match this source. No network, fonts,
scripts or animation are used. Progress values are data in PROGRESS below.
"""
from pathlib import Path
import argparse
import html

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
         accent='#B45F06', label='#6B4FD3', track='#E4E0F3', fill='#6B4FD3',
         dot=('#FF5F57', '#FEBC2E', '#28C840'))
D = dict(bg='#0D1B33', bar='#16284B', line='#1E2D4D', fg='#E8EDF8', muted='#8B9BB4',
         accent='#FF9F43', label='#A78BFA', track='#1E2D4D', fill='#A78BFA',
         dot=('#FF5F57', '#FEBC2E', '#28C840'))

W = 880
MONO = "Menlo,Consolas,ui-monospace,monospace"
DATE_X, TITLE_X = 16, 170
BAR_W, BAR_H = 220, 8

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

def esc(s):
    return html.escape(s, quote=True)

def text(x, y, s, size, fill, weight=None):
    w = f' font-weight="{weight}"' if weight else ''
    return f'<text x="{x}" y="{y}" font-family="{MONO}" font-size="{size}" fill="{fill}"{w} xml:space="preserve">{esc(s)}</text>'

def build(p):
    rows = []
    y = 28 + 44  # title bar plus prompt line
    rows.append(('prompt', y))
    y += 34
    for date, title, lines, prog in ENTRIES:
        y += 8
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
           f'<rect width="{W}" height="{total}" fill="{p["bg"]}"/>',
           f'<path d="M.5 14.5 A14 14 0 0 1 14.5 .5 H{W-14.5} A14 14 0 0 1 {W-.5} 14.5 V28.5 H.5 Z" fill="{p["bar"]}"/>',
           f'<path d="M0 28.5H{W}" stroke="{p["line"]}"/>']
    for i, c in enumerate(p['dot']):
        out.append(f'<circle cx="{14.5+20*i}" cy="14.5" r="5.5" fill="{c}"/>')
    out.append(text(W/2, 18.5, 'Education — 120×30', 12, p['muted']).replace('<text ', '<text text-anchor="middle" '))
    for r in rows:
        kind = r[0]
        if kind == 'prompt':
            out.append(text(16, r[1] + 2, '~ $', 14, p['accent']))
            out.append(text(16 + 4 * 8.4, r[1] + 2, 'cat education.txt', 14, p['fg']))
        elif kind == 'entry':
            _, yy, date, title = r
            out.append(text(DATE_X, yy, date, 13, p['label']))
            out.append(text(TITLE_X, yy, title, 13, p['fg'], 600))
        elif kind == 'line':
            _, yy, line = r
            out.append(text(TITLE_X, yy, line, 12, p['muted']))
        elif kind == 'bar':
            _, yy, prog = r
            out.append(text(TITLE_X, yy + 1, 'progress', 12, p['muted']))
            bx = TITLE_X + 78
            out.append(f'<rect x="{bx}" y="{yy-BAR_H+1}" width="{BAR_W}" height="{BAR_H}" rx="2" fill="{p["track"]}"/>')
            out.append(f'<rect x="{bx}" y="{yy-BAR_H+1}" width="{round(BAR_W*prog,2)}" height="{BAR_H}" rx="2" fill="{p["fill"]}"/>')
            out.append(text(bx + BAR_W + 12, yy + 1, f'{round(prog*100)}%', 12, p['muted']))
    out.append('</svg>')
    return total, ''.join(out)

for label, p in [('light', L), ('dark', D)]:
    _, svg = build(p)
    emit(f'education-terminal-{label}.svg', svg)

if mismatches:
    raise SystemExit('Generated assets differ: ' + ', '.join(mismatches))
print('Education SVGs match the generator.' if args.check else 'Generated education terminal SVGs.')
