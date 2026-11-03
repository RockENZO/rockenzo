#!/usr/bin/env python3
"""Generate the self-contained SVG profile cards using only Python's standard library.

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
  shift=';'.join(f'{dx} {dy}' for dx,dy in zip(t['x'],t['y']))
  turn=';'.join(f'{angle} {cx} {cy}' for angle in t['tilt'])
  groups.append(f'<g id="{instance}-{letter}" data-letter="{letter}" transform="translate({t["x"][0]} {t["y"][0]})"><animateTransform attributeName="transform" type="translate" values="{shift}" keyTimes="{times}" dur="{t["period"]}s" repeatCount="indefinite" calcMode="linear"/><g transform="rotate({t["tilt"][0]} {cx} {cy})"><animateTransform attributeName="transform" type="rotate" values="{turn}" keyTimes="{times}" dur="{t["period"]}s" repeatCount="indefinite" calcMode="linear"/><use href="#glyph-{letter}"/></g></g>')
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
   widths.append(round(count*6.633,4) if active==j else 0)
   visible.append('1' if active==j else '0')
  values=';'.join(map(str,widths));positions=';'.join(str(43+w) for w in widths)
  parts.append(f'<g opacity="{visible[0]}"><animate attributeName="opacity" values="{";".join(visible)}" keyTimes="{times}" dur="15s" repeatCount="indefinite" calcMode="discrete"/><defs><clipPath id="caption-{j}"><rect x="43" y="424" width="0" height="19"><animate attributeName="width" values="{values}" keyTimes="{times}" dur="15s" repeatCount="indefinite" calcMode="discrete"/></rect></clipPath></defs><text x="43" y="438" font-size="11" fill="#e5b879" clip-path="url(#caption-{j})">{html.escape(phrase)}</text><rect x="43" y="427" width="5" height="13" fill="#e5b879"><animate attributeName="x" values="{positions}" keyTimes="{times}" dur="15s" repeatCount="indefinite" calcMode="discrete"/><animate attributeName="opacity" values="1;0;1" keyTimes="0;.5;1" dur="1.2s" repeatCount="indefinite" calcMode="discrete"/></rect></g>')
 parts += ['</g><g class="still">', txt(43,438,CAPTION_PHRASES[0],11,'#e5b879'), '</g>']
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
a += ['<defs>'+glyph_paths()+'<g id="rock-glyphs">'+''.join(f'<use href="#glyph-{letter}"/>' for letter,_,_ in PLACEMENTS)+'</g><pattern id="rock-ascii-fill" patternUnits="userSpaceOnUse" width="22.8" height="12"><g font-family="Menlo,Consolas,monospace" font-size="6.8" font-weight="700" fill="#e1eae2" xml:space="preserve"><text x="0" y="5.2" textLength="22.8" lengthAdjust="spacingAndGlyphs">#+=/#+</text><text x="0" y="11.2" textLength="22.8" lengthAdjust="spacingAndGlyphs">=/#+=/</text></g></pattern><radialGradient id="wave-feather" gradientUnits="userSpaceOnUse" cx="175" cy="249" r="128" gradientTransform="translate(0 -7.47) scale(1 1.03)"><stop offset="0" stop-color="white"/><stop offset=".7" stop-color="white"/><stop offset="1" stop-color="black"/></radialGradient><mask id="open-field-window" maskUnits="userSpaceOnUse" x="35" y="105" width="284" height="290"><rect x="35" y="105" width="284" height="290" fill="url(#wave-feather)"/></mask><mask id="fixed-letter-clearance" maskUnits="userSpaceOnUse" x="35" y="105" width="284" height="290"><rect x="35" y="105" width="284" height="290" fill="white"/><g class="motion" fill="black" stroke="black" stroke-width="1.8" stroke-linejoin="round">'+suspended_glyphs('mask')+'</g><g class="still"><use href="#rock-glyphs" fill="black" stroke="black" stroke-width="1.8" stroke-linejoin="round"/></g></mask></defs>',
      '<g mask="url(#open-field-window)"><g class="motion water-background" mask="url(#fixed-letter-clearance)">'+''.join(frames)+'</g>',
      '<g class="still water-static">'+background+'</g></g>',
      '<g class="motion" id="rock-animated-letters" fill="url(#rock-ascii-fill)" stroke="#e1eae2" stroke-opacity=".3" stroke-width=".4">'+suspended_glyphs('fore')+'</g><g class="still" id="fixed-rock-letters"><use href="#rock-glyphs" fill="url(#rock-ascii-fill)" stroke="#e1eae2" stroke-opacity=".3" stroke-width=".4"/></g>']
a+=['<path d="M41 407h267" stroke="#303943"/>',typing_caption(),'</g><path d="M348 76V520" stroke="#303943"/>']

art=''.join(a)
D={'bg':'#10151b','line':'#303943','fg':'#e5e9e6','muted':'#9ba7ad','accent':'#e5b879','active':'#1c2b2b'}
L={'bg':'#f8f7f2','line':'#c9cfc9','fg':'#24312e','muted':'#586b64','accent':'#885b25','active':'#e5e9dc'}
def tx(x,y,v,size=11,c='fg',extra=''):
 return f'<text x="{x}" y="{y}" font-size="{size}" fill="{{{c}}}" {extra}>{html.escape(v)}</text>'
def anim(attr,values,times,dur,extra=''):
 return f'<animate attributeName="{attr}" values="'+ ';'.join(str(round(v,5)) if isinstance(v,(float,int)) else v for v in values)+'" keyTimes="'+';'.join(str(round(t,6)) for t in times)+f'" dur="{dur}s" {extra}/>'
def command_area(x, y):
    commands = ['cat about.txt', 'ls projects/', 'ls toolshed/']
    results = ['profile / skills / projects', 'agents/ research/ playground/ toolshed/', 'readme-reality/ demo-proof/']
    times = [i / 120 for i in range(121)]
    parts = ['<g class="motion">']
    for j, (command, result) in enumerate(zip(commands, results)):
        widths, visible, output_visible = [], [], []
        for i in range(121):
            t = (i / 10) % 12
            active, phase = int(t // 4), t % 4
            count = min(len(command), max(0, int((phase - .2) / .075))) if phase < 3.2 else max(0, len(command) - int((phase - 3.2) / .045))
            widths.append(count * 7.23 if active == j else 0)
            visible.append(1 if active == j else 0)
            output_visible.append(1 if active == j and 1.5 < phase < 3.2 else 0)
        parts += [f'<g opacity="{visible[0]}">' + anim('opacity', visible, times, 12, 'repeatCount="indefinite" calcMode="discrete"'),
                  f'<defs><clipPath id="command-{j}"><rect x="{x+29}" y="{y-14}" width="0" height="20">' + anim('width', widths, times, 12, 'repeatCount="indefinite" calcMode="discrete"') + '</rect></clipPath></defs>',
                  tx(x, y, '~ $', 12, 'accent'), tx(x+29, y, command, 12, 'accent', f'clip-path="url(#command-{j})"'),
                  f'<rect x="{x+29}" y="{y-11}" width="6" height="14" fill="{{accent}}">' + anim('x', [x+29+w for w in widths], times, 12, 'repeatCount="indefinite" calcMode="discrete"') + anim('opacity', [1,0,1], [0,.5,1], 1.2, 'repeatCount="indefinite" calcMode="discrete"') + '</rect>',
                  '<g opacity="0">' + anim('opacity', output_visible, times, 12, 'repeatCount="indefinite" calcMode="discrete"') + tx(x, y+24, result, 10, 'muted') + '</g></g>']
    parts += ['</g>', '<g class="still">', tx(x,y,'~ $ cat about.txt',12,'accent'), tx(x,y+24,results[0],10,'muted'), '</g>']
    return ''.join(parts)

for theme,pal in [('dark',D),('light',L)]:
 for mobile in [False,True]:
  W,H=(360,1070) if mobile else (900,580)
  out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">','<title id="title">RockENZO — animated terminal profile</title>','<desc id="desc">Original ASCII-filled geometric ROCK lettering over animated ASCII waves. Master of IT (Applied AI) at Adelaide University; Bachelor of IT at University of Adelaide, 2025. Focus: web development, scalable apps, AI and ML. Core: Python, React, Vue, Elasticsearch, Docker, Streamlit. AI and ML: PyTorch, TensorFlow, scikit-learn, Pandas, NumPy. LLM tools: Codex, Claude Code, DeepSeek Harness, Hugging Face and Ollama. Asynchronously suspended geometric letters with an ASCII-text fill sit over a decorative, multi-source ASCII interference background. Reveal and cursor effects do not execute commands or represent live system activity.</desc>','<style>.still{display:none}@media(prefers-reduced-motion:reduce){.motion{display:none}.still{display:inline}}</style>',f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="{{bg}}" stroke="{{line}}"/>',f'<path d="M1 46H{W-1}" stroke="{{line}}"/>','<g font-family="Menlo,Consolas,monospace">',tx(22,29,'ROCK / FIELD NOTES',12,'muted'),tx(W-112,29,'PROFILE 01',11,'muted')]
  mark=art
  if theme=='light':
   for old,new in {'#54766d':'#678575','#354c49':'#9daa9f','#728e8a':'#496e5e','#e1eae2':'#102b21','#e5b879':L['accent'],'#9ba7ad':L['muted'],'#303943':L['line']}.items():mark=mark.replace(old,new)
  if mobile:
   mark=mark[:mark.index('<path d="M41 407')]+ '</g>'
   out+=['<g transform="translate(28,-28) scale(.85)">'+mark+'</g>'];x,y=23,350
  else:out +=[mark,'<path d="M348 76V520" stroke="{line}"/>'];x,y=382,94
  out += [tx(x,y,'rockenzo@github',14,'accent'),tx(x,y+49,'Build. Verify.',28 if mobile else 34),tx(x,y+88,'Make it tangible.',25 if mobile else 29)]
  fields=[('STUDY','Master of IT (Applied AI) @ Adelaide University'),('GRADUATED','Bachelor of IT @ University of Adelaide (2025)'),('FOCUS','Web development / scalable apps / AI & ML'),('CORE','Python / React / Vue / Elasticsearch / Docker / Streamlit'),('AI / ML','PyTorch / TensorFlow / scikit-learn / Pandas / NumPy'),('LLM TOOLS','Codex / Claude Code / DeepSeek Harness'),('','Hugging Face / Ollama')]
  if mobile:
   fields=[('STUDY','Master of IT (Applied AI)'),('','@ Adelaide University'),('GRADUATED','Bachelor of IT (2025)'),('','@ University of Adelaide'),('FOCUS','Web development / scalable apps / AI & ML'),('CORE','Python / React / Vue'),('','Elasticsearch / Docker / Streamlit'),('AI / ML','PyTorch / TensorFlow / scikit-learn'),('','Pandas / NumPy'),('LLM TOOLS','Codex / Claude Code'),('','DeepSeek Harness / Hugging Face / Ollama')]
  ys=[500,524,572,596,644,704,728,776,800,848,872] if mobile else [224,259,294,329,364,399,419]
  value_x=23 if mobile else 469;size=12 if mobile else 11;cw=size*.603
  out += ['<g class="motion" opacity=".8"><rect x="'+str(x-8)+'" y="'+str(ys[0]-14)+'" width="'+str(326 if mobile else 490)+'" height="'+str(43 if mobile else 27)+'" rx="3" fill="{active}">'+anim('y',[v-14 for v in ys]+[ys[0]-14],[i/len(ys) for i in range(len(ys)+1)],len(ys)*2,'begin="5s" repeatCount="indefinite" calcMode="discrete"')+'</rect></g>']
  for i,((label,value),yy) in enumerate(zip(fields,ys)):
   vy=yy+20 if mobile else yy
   if label:out.append(tx(x,yy,label,10,'muted'))
   width=len(value)*cw+2;start=.25+i*(.32 if mobile else .5);duration=start+.65
   times=[0,start/duration]+[(start+.65*j/len(value))/duration for j in range(1,len(value)+1)]
   vals=[0,0]+[width*j/len(value) for j in range(1,len(value)+1)]
   out += [f'<defs><clipPath id="about-{i}"><rect x="{value_x}" y="{vy-14}" width="{width}" height="19">'+anim('width',vals,times,duration,'fill="freeze" calcMode="discrete"')+'</rect></clipPath></defs>',tx(value_x,vy,value,size,extra=f'class="motion" clip-path="url(#about-{i})"'),tx(value_x,vy,value,size,extra='class="still"')]
  # A quiet line pointer cycles after the one-time boot; factual values stay fully readable.
  out += ['<g class="motion"><rect x="'+str(8 if mobile else 365)+'" y="'+str(ys[0]-8)+'" width="3" height="9" fill="{accent}" opacity="0">'+anim('opacity',[0,0,1],[0,.999,1],5,'fill="freeze"')+anim('y',[v-8 for v in ys]+[ys[0]-8],[i/len(ys) for i in range(len(ys)+1)],len(ys)*2,'begin="5s" repeatCount="indefinite" calcMode="discrete"')+'</rect></g>']
  fy=1020 if mobile else 515
  out += [f'<path d="M{x} {fy-24}H{337 if mobile else 865}" stroke="{{line}}"/>', command_area(x,fy), '</g></svg>']
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

if mismatches:
    raise SystemExit('Generated assets differ: ' + ', '.join(mismatches))
print('Profile SVGs match the generator.' if args.check else 'Generated four animated and four static profile SVGs.')
