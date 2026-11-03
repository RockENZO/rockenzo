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

G={
'R':['1111110','1100011','1100011','1100011','1111110','1101100','1100110','1100011','1100011'],
'O':['0111110','1100011','1100011','1100011','1100011','1100011','1100011','1100011','0111110'],
'C':['0111111','1100000','1100000','1100000','1100000','1100000','1100000','1100000','0111111'],
'K':['1100011','1100110','1101100','1111000','1110000','1111000','1101100','1100110','1100011']}
def mask(x,y):
 # 2 x 2 custom glyph layout, scaled into a field; RO / CK.
 xx=x-8;yy=y-6
 if xx<0 or yy<0:return False
 col=xx//31;row=yy//23
 if col>1 or row>1:return False
 gx=(xx%31)//3;gy=(yy%23)//2
 if gx>6 or gy>8:return False
 return G['ROCK'[row*2+col]][gy][gx]=='1'
ASCII_ADVANCE = 3.4371

def txt(x,y,s,size,col):
 # Pin the ASCII grid advance across Menlo, Consolas and monospace fallbacks.
 grid = f' textLength="{len(s)*ASCII_ADVANCE:.4f}" lengthAdjust="spacingAndGlyphs"' if size == 5.7 else ''
 return f'<text x="{x}" y="{y}" font-size="{size}" fill="{col}" xml:space="preserve"{grid}>{html.escape(s)}</text>'

field_rows=[]
fixed_rows=[]
cutout_runs=[]
a=['<g font-family="Menlo,Consolas,monospace" aria-label="ASCII ROCK: extruded lettering carved into a signal field">']
for y in range(58):
 layers={k:'' for k in ['field','side','face','rim']}
 for x in range(77):
  face=mask(x,y);side=not face and any(mask(x-d,y+d//2) for d in range(1,10));edge=face and not all(mask(x+dx,y+dy) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)])
  near=not face and not side and any(mask(x+dx,y+dy) for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)])
  wave=math.sin(x*.17+y*.12)+math.cos(y*.34-x*.07)
  # Leave front faces and their side volumes out of the background texture.
  field=(' /:-=+'[max(0,min(5,int((wave+2)*1.3)))]) if not face and not side else ' '
  if (x<4 or x>73 or y<3 or y>54) and (x+y)%3!=0:field=' '
  layers['field']+=field
  layers['side']+=('\\' if (x+y)%3==0 else '.') if side else ' '
  # White ridges retain the first study's sculptural face; darker interiors read as a cutout.
  layers['face']+=('+' if (x+y)%3==0 else '=') if edge else (('/' if (x-y)%5==0 else '.') if face and (x+y)%2==0 else ' ')
  layers['rim']+=(':' if (x+y)%2==0 else '.') if near else ' '
 field_rows.append(txt(43,115+y*4.7,layers['field'],5.7,'#354c49'))
 for k,col in [('side','#728e8a'),('face','#e1eae2'),('rim','#e5b879')]:
  fixed_rows.append(txt(43,115+y*4.7,layers[k],5.7,col))
 # Pixel-run cutouts keep refracted ASCII texture out of stationary letter volumes.
 occupied=[mask(x,y) or any(mask(x-d,y+d//2) for d in range(1,10)) for x in range(77)]
 start=None
 for x in range(78):
  hit=x<77 and occupied[x]
  if hit and start is None:start=x
  if not hit and start is not None:
   cutout_runs.append(f'<rect x="{43+start*ASCII_ADVANCE-.7:.3f}" y="{115+y*4.7-5.3:.3f}" width="{(x-start)*ASCII_ADVANCE+1.4:.3f}" height="6.2" fill="black"/>')
   start=None
background=''.join(field_rows)
a += ['<defs><filter id="ascii-water" filterUnits="userSpaceOnUse" x="35" y="105" width="284" height="290" color-interpolation-filters="sRGB"><feTurbulence type="fractalNoise" baseFrequency=".015 .03" numOctaves="1" seed="7" result="ripples"><animate attributeName="baseFrequency" values=".015 .03;.021 .022;.015 .03" dur="14s" repeatCount="indefinite"/></feTurbulence><feDisplacementMap in="SourceGraphic" in2="ripples" scale="7" xChannelSelector="R" yChannelSelector="G"/></filter><mask id="fixed-letter-clearance" maskUnits="userSpaceOnUse" x="35" y="105" width="284" height="290"><rect x="35" y="105" width="284" height="290" fill="white"/>'+''.join(cutout_runs)+'</mask></defs>',
      '<g class="motion water-background" mask="url(#fixed-letter-clearance)"><g filter="url(#ascii-water)">'+background+'</g></g>',
      '<g class="still water-static">'+background+'</g>',
      '<g id="fixed-rock-letters">'+''.join(fixed_rows)+'</g>']
a+=['<path d="M41 407h267" stroke="#303943"/>',txt(43,430,'ROCK / SIGNAL SCULPTURE',10,'#e5b879'),txt(43,450,'ASCII FORM + NEGATIVE SPACE',9,'#9ba7ad'),'</g><path d="M348 76V520" stroke="#303943"/>']

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
  W,H=(360,1070) if mobile else (900,560)
  out=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" role="img" aria-labelledby="title desc">','<title id="title">RockENZO — animated terminal profile</title>','<desc id="desc">Original ASCII ROCK lettering. Master of IT (Applied AI) at Adelaide University; Bachelor of IT at University of Adelaide, 2025. Focus: web development, scalable apps, AI and ML. Core: Python, React, Vue, Elasticsearch, Docker. AI and ML: PyTorch, TensorFlow, scikit-learn, Pandas, NumPy. LLM tools: Hugging Face, Ollama, OpenAI, Streamlit. Born 2004-04-21. Stationary ASCII letters sit over a decorative, rippling ASCII background. Reveal and cursor effects do not execute commands or represent live system activity.</desc>','<style>.still{display:none}@media(prefers-reduced-motion:reduce){.motion{display:none}.still{display:inline}}</style>',f'<rect x=".5" y=".5" width="{W-1}" height="{H-1}" rx="12" fill="{{bg}}" stroke="{{line}}"/>',f'<path d="M1 46H{W-1}" stroke="{{line}}"/>','<g font-family="Menlo,Consolas,monospace">',tx(22,29,'ROCK / FIELD NOTES',12,'muted'),tx(W-112,29,'PROFILE 01',11,'muted')]
  mark=art
  if theme=='light':
   for old,new in {'#354c49':'#9daa9f','#728e8a':'#496e5e','#e1eae2':'#102b21','#e5b879':L['accent'],'#9ba7ad':L['muted'],'#303943':L['line']}.items():mark=mark.replace(old,new)
  if mobile:
   mark=mark[:mark.index('<path d="M41 407')]+ '</g>'
   out+=['<g transform="translate(28,-28) scale(.85)">'+mark+'</g>'];x,y=23,350
  else:out +=[mark,'<path d="M348 76V520" stroke="{line}"/>'];x,y=382,94
  out += [tx(x,y,'rockenzo@github',14,'accent'),tx(x,y+49,'Build. Verify.',28 if mobile else 34),tx(x,y+88,'Make it tangible.',25 if mobile else 29)]
  fields=[('STUDY','Master of IT (Applied AI) @ Adelaide University'),('GRADUATED','Bachelor of IT @ University of Adelaide (2025)'),('FOCUS','Web development / scalable apps / AI & ML'),('CORE','Python / React / Vue / Elasticsearch / Docker'),('AI / ML','PyTorch / TensorFlow / scikit-learn / Pandas / NumPy'),('LLM TOOLS','Hugging Face / Ollama / OpenAI / Streamlit'),('BORN','2004-04-21')]
  if mobile:
   fields=[('STUDY','Master of IT (Applied AI)'),('','@ Adelaide University'),('GRADUATED','Bachelor of IT (2025)'),('','@ University of Adelaide'),('FOCUS','Web development / scalable apps / AI & ML'),('CORE','Python / React / Vue'),('','Elasticsearch / Docker'),('AI / ML','PyTorch / TensorFlow / scikit-learn'),('','Pandas / NumPy'),('LLM TOOLS','Hugging Face / Ollama / OpenAI'),('','Streamlit'),('BORN','2004-04-21')]
  ys=[500,524,572,596,644,704,728,776,800,848,872,920] if mobile else [224+35*i for i in range(7)]
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
  fy=1020 if mobile else 495
  out += [f'<path d="M{x} {fy-24}H{337 if mobile else 865}" stroke="{{line}}"/>', command_area(x,fy), '</g></svg>']
  s=''.join(out)
  for k,v in pal.items():s=s.replace('{'+k+'}',v)
  ET.fromstring(s);emit(p/f'profile-terminal-{theme}{"-mobile" if mobile else ""}.svg',s)

if mismatches:
    raise SystemExit('Generated assets differ: ' + ', '.join(mismatches))
print('Profile SVGs match the generator.' if args.check else 'Generated four profile SVGs.')
