#!/usr/bin/env python3
"""Generate self-contained SVG profile cards and static section wordmarks.

Run from any directory. --check verifies that tracked assets match the source.
No network, external fonts, JavaScript or third-party assets are required.
"""
from pathlib import Path
import argparse
import html
import math
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--check', action='store_true', help='verify assets without writing')
args = parser.parse_args()
p = Path(__file__).resolve().parents[1] / 'assets'
mismatches = []
def emit(path, content):
    if args.check:
        if not path.is_file() or path.read_text() != content:
            mismatches.append(path.name)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

# Original geometric glyph outlines. Flat fills, chamfered corners and an
# approximately 12-unit stem weight; no font files, extrusion or shadow layers.
GLYPHS = {
 'R': [[(0,0),(43,0),(57,14),(57,36),(44,49),(35,49),(59,78),(43,78),(20,49),(12,49),(12,78),(0,78)], [(12,12),(38,12),(45,19),(45,31),(38,38),(12,38)]],
 'O': [[(14,0),(44,0),(58,14),(58,64),(44,78),(14,78),(0,64),(0,14)], [(18,12),(40,12),(46,18),(46,60),(40,66),(18,66),(12,60),(12,18)]],
 'C': [[(14,0),(58,0),(58,12),(18,12),(12,18),(12,60),(18,66),(58,66),(58,78),(14,78),(0,64),(0,14)]],
 'K': [[(0,0),(12,0),(12,31),(42,0),(58,0),(23,39),(60,78),(43,78),(12,47),(12,78),(0,78)]]
}
PLACEMENTS = [('R',74,145),('O',195,145),('C',74,266),('K',195,266)]
def inside_polygon(x,y,polygon):
 inside=False
 for (ax,ay),(bx,by) in zip(polygon,polygon[1:]+polygon[:1]):
  if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax:inside=not inside
 return inside

def mask(x,y):
 # Background text is sampled in SVG coordinates; vector counters stay open.
 px,py=43+x*ASCII_ADVANCE,115+y*4.7-2.5
 return any(sum(inside_polygon(px-ox,py-oy,poly) for poly in GLYPHS[letter])%2 for letter,ox,oy in PLACEMENTS)

def glyph_paths():
 paths=[]
 for letter,x,y in PLACEMENTS:
  d=' '.join('M'+' L'.join(f'{px},{py}' for px,py in polygon)+' Z' for polygon in GLYPHS[letter])
  paths.append(f'<g id="glyph-{letter}"><path d="{d}" transform="translate({x} {y})" fill-rule="evenodd"/></g>')
 return ''.join(paths)

# Separate glyph-local tiles prevent RO and CK from sharing a timeline.
# Each tier has seven staggered bands, with a non-overlapping handoff.
FLAP_SECONDS = 10
FLAP_GROUP_ROWS = 7
FLAP_ROWS = 2 * FLAP_GROUP_ROWS
FLAP_SWEEP_SECONDS = (FLAP_GROUP_ROWS - 1) * .18 + 6 * .12 + .105
FLAP_STATES = [('#+=/#+', '=/#+=/'), ('R0CK42', '7A9C2F'),
               ('H4X019', 'AB7306'), ('01:/+=', '9K2R4C'),
               ('[0][1]', '#+=/#+'), ('7F3A09', 'C2E841'),
               ('=/#+=/', '42R0CK')]

def flap_schedule(row):
 tier, band = divmod(row, FLAP_GROUP_ROWS)
 start = .8 + band * .18 + tier * (FLAP_SWEEP_SECONDS + .03)
 times, scales = [0.], [1.]
 changes, states = [0.], [0]
 for flip in range(7):
  moment = start + flip * .12
  times += [moment, moment + .05, moment + .105]
  scales += [1., .08, 1.]
  changes.append(moment + .05)
  states.append(0 if flip == 6 else 1 + (flip + row) % 6)
 times.append(FLAP_SECONDS); scales.append(1.)
 changes.append(FLAP_SECONDS); states.append(0)
 return times, scales, changes, states

def flap_band_y(row):
 tier, band = divmod(row, FLAP_GROUP_ROWS)
 return band * 12

def ascii_fill():
 def pair(rows, shifted=False):
  return '<g font-family="Menlo,Consolas,monospace" font-size="6.8" font-weight="700" fill="#e1eae2" xml:space="preserve">' + ''.join(
   f'<text x="0" y="{y}" textLength="22.8" lengthAdjust="spacingAndGlyphs">{html.escape(text)}</text>'
   for y,text in zip((-.8,5.2) if shifted else (5.2,11.2), rows)) + '</g>'
 out = ['<pattern id="rock-ascii-fill-static" patternUnits="userSpaceOnUse" width="22.8" height="12">'+pair(FLAP_STATES[0])+'</pattern>']
 out += [f'<g id="flap-state-{i}">'+pair(rows,True)+'</g>' for i,rows in enumerate(FLAP_STATES)]
 for row in range(FLAP_ROWS):
  out.append(f'<clipPath id="flap-clip-{row}"><rect x="0" y="{flap_band_y(row)}" width="22.8" height="12"/></clipPath>')
 for row in range(FLAP_ROWS):
  if row % FLAP_GROUP_ROWS == 0:
   suffix = "-lower" if row else ""
   out.append(f'<pattern id="rock-ascii-fill{suffix}" patternUnits="userSpaceOnUse" width="22.8" height="84">')
  times,scales,changes,states = flap_schedule(row)
  keys = ';'.join(f'{t/FLAP_SECONDS:.6f}' for t in times)
  values = ';'.join(f'1 {v}' for v in scales)
  change_keys = ';'.join(f'{t/FLAP_SECONDS:.6f}' for t in changes)
  refs = ';'.join(f'#flap-state-{state}' for state in states)
  out.append(f'<g data-flap-row="{row}" clip-path="url(#flap-clip-{row})"><g transform="translate(0 {flap_band_y(row)+6})"><g><animateTransform attributeName="transform" type="scale" values="{values}" keyTimes="{keys}" dur="{FLAP_SECONDS}s" repeatCount="indefinite" calcMode="linear"/><use href="#flap-state-0"><animate attributeName="href" values="{refs}" keyTimes="{change_keys}" dur="{FLAP_SECONDS}s" repeatCount="indefinite" calcMode="discrete"/></use></g></g></g>')
  if row % FLAP_GROUP_ROWS == FLAP_GROUP_ROWS - 1: out.append('</pattern>')
 return ''.join(out)

# Periodic steady-state responses to a multi-harmonic drive of the same
# mass/spring/damper equation. Units are visual design units, not material data.
SUSPENSION = {
 'R': dict(period=7.4, mass=1.4, stiffness=2.2, damping=.3, phase=.1, x=.9, y=2.7, tilt=.7),
 'O': dict(period=5.8, mass=.85, stiffness=2.5, damping=.22, phase=1.8, x=1.1, y=3.8, tilt=.9),
 'C': dict(period=8.6, mass=1.1, stiffness=1.8, damping=.27, phase=3.2, x=2.1, y=2.6, tilt=.8),
 'K': dict(period=6.6, mass=1., stiffness=3.2, damping=.2, phase=4.6, x=.8, y=2., tilt=1.0),
}

def spring_response(phase, config, offset):
 omega=math.tau/config['period']
 c=2*config['damping']*math.sqrt(config['stiffness']*config['mass'])
 response=0.
 for harmonic,force in [(1,1.),(2,.22),(3,.075)]:
  drive=harmonic*omega
  detuning=config['stiffness']-config['mass']*drive*drive
  gain=force/math.hypot(detuning,c*drive)
  lag=math.atan2(c*drive,detuning)
  response+=gain*math.sin(harmonic*phase+offset-lag)
 return response

def suspension_track(letter):
 config=SUSPENSION[letter]
 axes=[]
 for limit,offset in [(config['x'],config['phase']+.9),(config['y'],config['phase']),(config['tilt'],config['phase']+1.7)]:
  # Normalize the visual range; mass/stiffness/damping still govern phase and
  # harmonic balance. Sampling closes explicitly so repeat has no seam.
  peak=max(abs(spring_response(i*math.tau/720,config,offset)) for i in range(720))
  values=[round(limit*spring_response(i*math.tau/72,config,offset)/peak,5) for i in range(72)]
  axes.append(values+[values[0]])
 return dict(period=config['period'],x=axes[0],y=axes[1],tilt=axes[2])

TRACKS={letter:suspension_track(letter) for letter,_,_ in PLACEMENTS}

def suspended_glyphs(instance):
 groups=[]
 times=';'.join(f'{i/72:.9f}' for i in range(73))
 for letter,x,y in PLACEMENTS:
  t=TRACKS[letter];cx,cy=x+29,y+39
  fill = ' fill="url(#rock-ascii-fill-lower)"' if instance == 'fore' and letter in 'CK' else ''
  shift=';'.join(f'{dx} {dy}' for dx,dy in zip(t['x'],t['y']))
  turn=';'.join(f'{angle} {cx} {cy}' for angle in t['tilt'])
  groups.append(f'<g id="{instance}-{letter}" data-letter="{letter}" transform="translate({t["x"][0]} {t["y"][0]})"><animateTransform attributeName="transform" type="translate" values="{shift}" keyTimes="{times}" dur="{t["period"]}s" repeatCount="indefinite" calcMode="linear"/><g transform="rotate({t["tilt"][0]} {cx} {cy})"><animateTransform attributeName="transform" type="rotate" values="{turn}" keyTimes="{times}" dur="{t["period"]}s" repeatCount="indefinite" calcMode="linear"/><use href="#glyph-{letter}"{fill}/></g></g>')
 return ''.join(groups)

ASCII_ADVANCE = 3.4371

def txt(x,y,s,size,col):
 # Pin the ASCII grid advance across Menlo, Consolas and monospace fallbacks.
 grid = f' textLength="{len(s)*ASCII_ADVANCE:.4f}" lengthAdjust="spacingAndGlyphs"' if size == 5.7 else ''
 return f'<text x="{x}" y="{y}" font-size="{size}" fill="{col}" xml:space="preserve"{grid}>{html.escape(s)}</text>'

CAPTION_PHRASES = ['Building local-first AI tools.', 'Exploring applied machine learning.', 'Making software you can explore.']

def typing_caption():
 parts=['<g class="motion">']
 times=';'.join(f'{i/150:.9f}' for i in range(151))
 for j,phrase in enumerate(CAPTION_PHRASES):
  widths=[];visible=[]
  for i in range(151):
   t=(i/10)%15;active=int(t//5);phase=t%5
   count=min(len(phrase),max(0,int((phase-.15)/.07))) if phase<4 else max(0,len(phrase)-int((phase-4)/.02))
   widths.append(round(count*7.839,4) if active==j else 0)
   visible.append('1' if active==j else '0')
  values=';'.join(map(str,widths));positions=';'.join(str(43+w) for w in widths)
  parts.append(f'<g opacity="{visible[0]}"><animate attributeName="opacity" values="{";".join(visible)}" keyTimes="{times}" dur="15s" repeatCount="indefinite" calcMode="discrete"/><defs><clipPath id="caption-{j}"><rect x="43" y="424" width="0" height="19"><animate attributeName="width" values="{values}" keyTimes="{times}" dur="15s" repeatCount="indefinite" calcMode="discrete"/></rect></clipPath></defs><text x="43" y="438" font-size="13" fill="#e5b879" clip-path="url(#caption-{j})">{html.escape(phrase)}</text><rect x="43" y="425" width="7" height="15" fill="#e5b879"><animate attributeName="x" values="{positions}" keyTimes="{times}" dur="15s" repeatCount="indefinite" calcMode="discrete"/><animate attributeName="opacity" values="1;0;1" keyTimes="0;.5;1" dur="1.2s" repeatCount="indefinite" calcMode="discrete"/></rect></g>')
 parts += ['</g><g class="still">', txt(43,438,CAPTION_PHRASES[0],13,'#e5b879'), '</g>']
 return ''.join(parts)

# Static ASCII fallback and the animated field share the same aperture. Only
# the display is cropped: the radial-wave expression below has no edge walls.
field_rows=[]
a=['<g font-family="Menlo,Consolas,monospace" aria-label="Flat geometric ROCK over an open ASCII wave field">']
for y in range(58):
 row=''
 for x in range(77):
  wave=math.sin(x*.17+y*.12)+math.cos(y*.34-x*.07)
  row+=' ' if mask(x,y) else ' /:-=+'[max(0,min(5,int((wave+2)*1.3)))]
 field_rows.append(txt(43,115+y*4.7,row,5.7,'#354c49'))
background=''.join(field_rows)
# A closed periodic visual model: staggered breathing holes and the summed
# amplitudes of several outward-travelling radial waves. No runtime simulation.
WAVE_FRAMES = 72
WAVE_SECONDS = 8
WAVE_SOURCES = [(19, 12, 0.0), (49, 15, .29), (21, 39, .53), (62, 41, .76), (37, 29, .12)]
def field_character(x,y,phase):
 # Analytic open-plane sampling works equally inside and outside the visible
 # aperture. The viewport never clamps, reflects or wraps a travelling wave.
 angle=(phase % 1)*math.tau
 samples=[(math.hypot((x-sx)*.8,y-sy),offset) for sx,sy,offset in WAVE_SOURCES]
 holes=[(distance,4+2.8*math.sin(angle+offset*math.tau)) for distance,offset in samples]
 if any(distance<radius for distance,radius in holes):return ' '
 wave=sum(math.cos(.72*distance-2*angle+offset*math.tau)*math.exp(-distance/26) for distance,offset in samples)
 wave+=.3*math.sin(.15*x+.11*y-angle)
 near=any(0<=distance-radius<.9 for distance,radius in holes)
 level=max(0,min(7,int((wave+1.25)*2.5)))
 return ':' if near else ' .:-=+*#'[level]

def wave_rows(phase):
 return [''.join(field_character(x,y,phase) for x in range(77)) for y in range(58)]
frames=[]
for frame in range(WAVE_FRAMES):
 start,end=frame/WAVE_FRAMES,(frame+1)/WAVE_FRAMES
 if frame==0:times=[0,end,1];values=['visible','hidden','hidden']
 elif frame==WAVE_FRAMES-1:times=[0,start,1];values=['hidden','visible','hidden']
 else:times=[0,start,end,1];values=['hidden','visible','hidden','hidden']
 switch='<animate attributeName="visibility" values="'+';'.join(values)+'" keyTimes="'+';'.join(f'{t:.9f}' for t in times)+f'" dur="{WAVE_SECONDS}s" repeatCount="indefinite" calcMode="discrete"/>'
 frame_rows='<text font-size="5.7" fill="#54766d" xml:space="preserve">'+''.join(f'<tspan x="43" y="{115+y*4.7}" textLength="{len(row)*ASCII_ADVANCE:.4f}" lengthAdjust="spacingAndGlyphs">{html.escape(row)}</tspan>' for y,row in enumerate(wave_rows(start)) if row.strip())+'</text>'
 frames.append(f'<g class="wave-frame" data-frame="{frame}" visibility="'+('visible' if frame==0 else 'hidden')+'">'+switch+frame_rows+'</g>')
a += ['<defs>'+glyph_paths()+'<g id="rock-glyphs">'+''.join(f'<use href="#glyph-{letter}"/>' for letter,_,_ in PLACEMENTS)+'</g>'+ascii_fill()+'<radialGradient id="wave-feather" gradientUnits="userSpaceOnUse" cx="175" cy="249" r="128" gradientTransform="translate(0 -7.47) scale(1 1.03)"><stop offset="0" stop-color="white"/><stop offset=".7" stop-color="white"/><stop offset="1" stop-color="black"/></radialGradient><mask id="open-field-window" maskUnits="userSpaceOnUse" x="35" y="105" width="284" height="290"><rect x="35" y="105" width="284" height="290" fill="url(#wave-feather)"/></mask><radialGradient id="wave-veil" gradientUnits="userSpaceOnUse" cx="175" cy="249" r="128" gradientTransform="translate(0 -7.47) scale(1 1.03)"><stop offset="0" stop-color="{bg}" stop-opacity="0"/><stop offset=".7" stop-color="{bg}" stop-opacity="0"/><stop offset="1" stop-color="{bg}"/></radialGradient></defs>',
      # Animated water is painted without masks: SVG images repaint as a whole, and a live mask forces the
      # large water layer through an offscreen pass on every frame. The card background is flat, so painting
      # background-coloured shapes over the water gives the same pixels as the former masks: a radial veil
      # reproduces the feathered aperture, and moving plates (same geometry and tracks as the letters) clear the
      # water behind each letter. The static fallback keeps its mask.
      '<g class="motion water-background">'+''.join(frames)+'</g>',
      '<rect class="motion" id="wave-aperture-veil" x="35" y="105" width="284" height="290" fill="url(#wave-veil)"/>',
      '<g class="motion" id="letter-clearance" fill="{bg}" stroke="{bg}" stroke-width="1.8" stroke-linejoin="round">'+suspended_glyphs('mask')+'</g>',
      '<g mask="url(#open-field-window)"><g class="still water-static">'+background+'</g></g>',
      '<g class="motion" id="rock-animated-letters" fill="url(#rock-ascii-fill)" stroke="#e1eae2" stroke-opacity=".3" stroke-width=".4">'+suspended_glyphs('fore')+'</g><g class="still" id="fixed-rock-letters"><use href="#rock-glyphs" fill="url(#rock-ascii-fill-static)" stroke="#e1eae2" stroke-opacity=".3" stroke-width=".4"/></g>']
a+=['<path d="M41 407h267" stroke="#303943"/>',typing_caption(),'</g><path d="M348 76V480" stroke="#303943"/>']

art=''.join(a)
# Palette shared with the README: navy (0D1B33), gold (FF9F43), lavender (A78BFA), plus a teal water field.
D={'bg':'#0D1B33','line':'#1E2D4D','fg':'#E8EDF8','muted':'#8B9BB4','accent':'#FF9F43','active':'#16284B','titlebar':'#16284B','label':'#A78BFA'}
L={'bg':'#F7F6FC','line':'#D9D5EC','fg':'#1B2340','muted':'#59627F','accent':'#B45F06','active':'#ECE8FB','titlebar':'#ECE8FB','label':'#6B4FD3'}
MARK_COLORS={
 'dark':{'#54766d':'#2FA79B','#354c49':'#1F6F6A','#e1eae2':'#D9CCFF','#e5b879':D['accent'],'#9ba7ad':D['muted'],'#303943':D['line']},
 'light':{'#54766d':'#2A8F86','#354c49':'#8CBDB7','#e1eae2':'#2A2060','#e5b879':L['accent'],'#9ba7ad':L['muted'],'#303943':L['line']},
}
def tx(x,y,v,size=11,c='fg',extra=''):
 return f'<text x="{x}" y="{y}" font-size="{size}" fill="{{{c}}}" {extra}>{html.escape(v)}</text>'
def anim(attr,values,times,dur,extra=''):
 return f'<animate attributeName="{attr}" values="'+ ';'.join(str(round(v,5)) if isinstance(v,(float,int)) else v for v in values)+'" keyTimes="'+';'.join(str(round(t,6)) for t in times)+f'" dur="{dur}s" {extra}/>'
HEADLINE_WORDS = ['Praxis.', 'Palimpsest.', 'Autopoiesis.']

def headline_timeline():
    # Events occur only when a character changes; a two-second hold costs no
    # extra keyframes. The final blank state matches the start of the loop.
    t = 0.
    events = [(t, 0, 0)]
    for active, word in enumerate(HEADLINE_WORDS):
        for count in range(1, len(word) + 1):
            t = round(t + .1, 5)
            events.append((t, active, count))
        t = round(t + 2., 5)
        for count in range(len(word) - 1, -1, -1):
            t = round(t + .05, 5)
            events.append((t, active, count))
        t = round(t + .3, 5)
        events.append((t, (active + 1) % len(HEADLINE_WORDS), 0))
    return events, t

def typing_headline(x, y, size):
    events, duration = headline_timeline()
    times = [t / duration for t, _, _ in events]
    advance = size * .603
    repeat = 'repeatCount="indefinite" calcMode="discrete"'
    parts = ['<g id="profile-headline" aria-label="'+html.escape(' '.join(HEADLINE_WORDS))+'"><g class="motion">']
    for active, word in enumerate(HEADLINE_WORDS):
        widths = [count * advance if current == active else 0 for _, current, count in events]
        visible = [1 if current == active else 0 for _, current, _ in events]
        # First word remains visible if declarative animation is unsupported.
        base_width = len(word) * advance if active == 0 else 0
        parts += [f'<g opacity="{1 if active == 0 else 0}">'+anim('opacity', visible, times, duration, repeat),
                  f'<defs><clipPath id="headline-{active}"><rect x="{x}" y="{y-size}" width="{base_width}" height="{size+10}">'+anim('width', widths, times, duration, repeat)+'</rect></clipPath></defs>',
                  tx(x,y,word,size,extra=f'textLength="{len(word)*advance}" lengthAdjust="spacingAndGlyphs" clip-path="url(#headline-{active})"'), '</g>']
    parts += [f'<rect x="{x+len(HEADLINE_WORDS[0])*advance}" y="{y+5}" width="{advance*.85}" height="2" fill="{{accent}}">'+anim('x',[x+count*advance for _,_,count in events],times,duration,repeat)+anim('opacity',[1,0,1],[0,.5,1],1.2,repeat)+'</rect></g>',
              '<g class="still">'+tx(x,y,HEADLINE_WORDS[0],size)+'</g></g>']
    return ''.join(parts)

def command_area(x, y, cs, os):
    cw = cs * .603
    off = round(4 * cw)
    commands = ['cat about.txt', 'ls projects/', 'ls toolshed/']
    results = ['profile / skills / projects', 'agents/ research/ playground/ toolshed/', 'readme-reality/ demo-proof/']
    times = [i / 120 for i in range(121)]
    parts = ['<g id="command-area"><g class="motion">']
    for j, (command, result) in enumerate(zip(commands, results)):
        widths, visible, output_visible, cursor_visible = [], [], [], []
        for i in range(121):
            t = (i / 10) % 12
            active, phase = int(t // 4), t % 4
            count = min(len(command), max(0, int((phase - .2) / .075))) if phase < 3.2 else max(0, len(command) - int((phase - 3.2) / .045))
            widths.append(count * cw if active == j else 0)
            visible.append(1 if active == j else 0)
            output_visible.append(1 if active == j and 1.5 < phase < 3.2 else 0)
            # Do not blink away while characters are entering or being deleted.
            # Hold-only blinking uses the same sampled timeline as the reveal
            # and cursor position, rather than an independent repeating clock.
            holding = count == len(command) and phase < 3.2
            blink_on = not holding or int(max(0, phase - (.2 + len(command)*.075)) / .6) % 2 == 0
            cursor_visible.append(1 if active == j and blink_on else 0)
        parts += [f'<g opacity="{visible[0]}">' + anim('opacity', visible, times, 12, 'repeatCount="indefinite" calcMode="discrete"'),
                  f'<defs><clipPath id="command-{j}"><rect x="{x+off}" y="{y-cs-1}" width="0" height="{cs+8}">' + anim('width', widths, times, 12, 'repeatCount="indefinite" calcMode="discrete"') + '</rect></clipPath></defs>',
                  tx(x, y, '~ $', cs, 'accent'), tx(x+off, y, command, cs, 'accent', f'textLength="{len(command)*cw}" lengthAdjust="spacingAndGlyphs" clip-path="url(#command-{j})"'),
                  f'<rect id="command-cursor-{j}" x="{x+off}" y="{y-cs*.92:.1f}" width="{cs*.55:.1f}" height="{cs*1.15:.1f}" fill="{{accent}}">' + anim('x', [x+off+w for w in widths], times, 12, 'repeatCount="indefinite" calcMode="discrete"') + anim('opacity', cursor_visible, times, 12, 'repeatCount="indefinite" calcMode="discrete"') + '</rect>',
                  '<g opacity="0">' + anim('opacity', output_visible, times, 12, 'repeatCount="indefinite" calcMode="discrete"') + tx(x, y+os*2.3, result, os, 'muted') + '</g></g>']
    parts += ['</g>', '<g class="still">', tx(x,y,'~ $ cat about.txt',cs,'accent'), tx(x,y+os*2.3,results[0],os,'muted'), '</g></g>']
    return ''.join(parts)

for theme,pal in [('dark',D),('light',L)]:
 for mobile in [False,True]:
  W,H=(360,1010) if mobile else (900,602)
  window_title = 'rockingmac — zsh' if mobile else 'rockingmac — -zsh — 120×30'
  out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">','<title id="title">RockENZO — animated terminal profile</title>','<desc id="desc">Original ASCII-filled geometric ROCK lettering over animated ASCII waves. Headline cycles through Praxis, Palimpsest and Autopoiesis. Master of IT (Applied AI) at Adelaide University; Bachelor of IT at University of Adelaide, 2025. Focus: web development, scalable apps, AI and ML. Core: Python, React, Vue, Elasticsearch, Docker, Streamlit. AI and ML: PyTorch, TensorFlow, scikit-learn, Pandas, NumPy. LLM tools: Codex, Claude Code, DeepSeek Harness, Hugging Face and Ollama. Asynchronously suspended geometric letters with an ASCII-text fill sit over a decorative, multi-source ASCII interference background. Reveal and cursor effects do not execute commands or represent live system activity.</desc>','<style>.still{display:none}@media(prefers-reduced-motion:reduce){.motion{display:none}.still{display:inline}}</style>',f'<defs><clipPath id="window-clip"><rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12"/></clipPath></defs>',f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="{{bg}}" stroke="{{line}}"/>',f'<rect id="titlebar" x=".5" y=".5" width="{W-1}" height="45.5" fill="{{titlebar}}" clip-path="url(#window-clip)"/>',f'<path d="M1 46H{W-1}" stroke="{{line}}"/>','<g font-family="Menlo,Consolas,monospace">','<g id="window-controls" aria-hidden="true"><circle cx="23" cy="24" r="6" fill="#FF5F57"/><circle cx="41" cy="24" r="6" fill="#FEBC2E"/><circle cx="59" cy="24" r="6" fill="#28C840"/></g>',f'<text id="window-title" x="{W/2}" y="29" font-size="12" text-anchor="middle" fill="{{muted}}">{window_title}</text>']
  mark=art
  for old,new in MARK_COLORS[theme].items():mark=mark.replace(old,new)
  if mobile:
   mark=mark[:mark.index('<path d="M41 407')]+ '</g>'
   out+=['<g transform="translate(28,-28) scale(.85)">'+mark+'</g>'];x,y=23,350
  else:
   cut=mark.index('<path d="M348 76V')
   out+=['<g transform="translate(0,45)">'+mark[:cut]+'</g>','<path d="M348 76V536" stroke="{line}"/>'];x,y=382,94
  out += [tx(x,y,'rockenzo@github',17,'accent'),typing_headline(x,y+67,32 if mobile else 40)]
  fields=[('STUDY','Master of IT (Applied AI) @ Adelaide University'),('GRADUATED','Bachelor of IT @ University of Adelaide (2025)'),('FOCUS','Web development / scalable apps / AI & ML'),('CORE','Python / React / Vue'),('','Elasticsearch / Docker / Streamlit'),('AI / ML','PyTorch / TensorFlow / scikit-learn'),('','Pandas / NumPy'),('LLM TOOLS','Codex / Claude Code / DeepSeek Harness'),('','Hugging Face / Ollama')]
  if mobile:
   fields=[('STUDY','Master of IT (Applied AI)'),('','@ Adelaide University'),('GRADUATED','Bachelor of IT (2025)'),('','@ University of Adelaide'),('FOCUS','Web development / scalable apps / AI & ML'),('CORE','Python / React / Vue'),('','Elasticsearch / Docker / Streamlit'),('AI / ML','PyTorch / TensorFlow / scikit-learn'),('','Pandas / NumPy'),('LLM TOOLS','Codex / Claude Code'),('','DeepSeek Harness / Hugging Face / Ollama')]
  ys=[500,524,572,596,644,704,728,776,800,848,872] if mobile else [222,258,294,330,352,388,410,446,468]
  value_x=23 if mobile else 462;size=13 if mobile else 14;hy=14 if mobile else 17;cw=size*.603
  out += ['<g class="motion" opacity=".8"><rect x="'+str(x-8)+'" y="'+str(ys[0]-hy)+'" width="'+str(332 if mobile else 497)+'" height="'+str(43 if mobile else 27)+'" rx="3" fill="{active}">'+anim('y',[v-hy for v in ys]+[ys[0]-hy],[i/len(ys) for i in range(len(ys)+1)],len(ys)*2,'begin="5s" repeatCount="indefinite" calcMode="discrete"')+'</rect></g>']
  for i,((label,value),yy) in enumerate(zip(fields,ys)):
   vy=yy+20 if mobile else yy
   if label:out.append(tx(x,yy,label,11.5 if mobile else 12,'label'))
   width=len(value)*cw+2;start=.25+i*(.32 if mobile else .5);duration=start+.65
   times=[0,start/duration]+[(start+.65*j/len(value))/duration for j in range(1,len(value)+1)]
   vals=[0,0]+[width*j/len(value) for j in range(1,len(value)+1)]
   out += [f'<defs><clipPath id="about-{i}"><rect x="{value_x}" y="{vy-hy}" width="{width}" height="{hy+6}">'+anim('width',vals,times,duration,'fill="freeze" calcMode="discrete"')+'</rect></clipPath></defs>',tx(value_x,vy,value,size,extra=f'class="motion" clip-path="url(#about-{i})"'),tx(value_x,vy,value,size,extra='class="still"')]
  # A quiet line pointer cycles after the one-time boot; factual values stay fully readable.
  out += ['<g class="motion"><rect x="'+str(8 if mobile else 365)+'" y="'+str(ys[0]-8)+'" width="3" height="9" fill="{label}" opacity="0">'+anim('opacity',[0,0,1],[0,.999,1],5,'fill="freeze"')+anim('y',[v-8 for v in ys]+[ys[0]-8],[i/len(ys) for i in range(len(ys)+1)],len(ys)*2,'begin="5s" repeatCount="indefinite" calcMode="discrete"')+'</rect></g>']
  fy=952 if mobile else 528
  out += [f'<path d="M{x} {fy-24}H{344 if mobile else 870}" stroke="{{line}}"/>', command_area(x,fy,14 if mobile else 15,13 if mobile else 15), '</g></svg>']
  s=''.join(out)
  for k,v in pal.items():s=s.replace('{'+k+'}',v)
  root=ET.fromstring(s)
  stem=f'profile-terminal-{theme}{"-mobile" if mobile else ""}'
  emit(p/f'{stem}.svg',s)
  # HTML picture media chooses a genuinely static image even where a browser
  # does not propagate reduced-motion into an SVG image document.
  ns='http://www.w3.org/2000/svg'
  for parent in root.iter():
   for child in list(parent):
    tag=child.tag.rsplit('}',1)[-1]
    if 'motion' in child.get('class','').split() or tag in ['animate','animateTransform','set']:
     parent.remove(child)
  for style in root.findall(f'.//{{{ns}}}style'):
   style.text='.motion{display:none}.still{display:inline}'
  ET.register_namespace('',ns)
  emit(p/f'{stem}-static.svg',ET.tostring(root,encoding='unicode'))

# Quiet chapter markers balance the animated terminal card. Transparent SVGs
# use explicit light/dark picture sources and a 360px intrinsic width, so type
# remains readable on narrow screens rather than shrinking a desktop banner.
SECTION_PATHS = ['projects', 'playground', 'toolshed', 'agents', 'education', 'activity', 'elsewhere']
for theme, palette in [('dark', D), ('light', L)]:
 for number, path in enumerate(SECTION_PATHS, 1):
  rule_start = round(60 + len(path)*22*.603 + 20, 2)
  # A quiet terminal rule: a rounded 2.5px accent-coloured line rather than the
  # old hairline, closed by a small accent block like a terminal cursor.
  wordmark = f'<svg xmlns="http://www.w3.org/2000/svg" width="360" height="40" viewBox="0 0 360 40" role="img" aria-labelledby="section-title"><title id="section-title">{number:02d} / {path}</title><g font-family="Menlo,Consolas,monospace"><text x="0" y="28" font-size="14" letter-spacing="1" fill="{palette["accent"]}">{number:02d}</text><text x="35" y="28" font-size="19" fill="{palette["muted"]}">/</text><text x="60" y="28" font-size="22" font-weight="500" fill="{palette["label"]}">{path}</text></g><path d="M{rule_start} 22H347" fill="none" stroke="{palette["label"]}" stroke-width="2.5" stroke-linecap="round"/><rect x="351" y="18.5" width="7" height="7" rx="1.5" fill="{palette["accent"]}"/></svg>'
  emit(p/f'section-{path}-{theme}.svg', wordmark)

if mismatches:
    raise SystemExit('Generated assets differ: ' + ', '.join(mismatches))
print('Profile SVGs match the generator.' if args.check else 'Generated profile cards and static section wordmarks.')
