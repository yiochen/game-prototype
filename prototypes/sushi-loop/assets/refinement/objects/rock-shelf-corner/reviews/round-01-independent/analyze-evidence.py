import pathlib,json,sys,math,hashlib,shutil
sys.dont_write_bytecode=True
from PIL import Image,ImageChops,ImageDraw
P=pathlib.Path(__file__).resolve().parent;B=P.parents[1];C=B/'candidates/round-01';O=P/'analysis';O.mkdir(exist_ok=True)
def rgba(p):return Image.open(p).convert('RGBA')
def diff(a,b):
 d=ImageChops.difference(a,b);ps=list(d.getdata());return {'equalRGBA':a.tobytes()==b.tobytes(),'differentPixels':sum(any(v) for v in ps),'maxRGBA':[max(v[k] for v in ps) for k in range(4)]}
def background(im,color):
 bg=Image.new('RGBA',im.size,color);bg.alpha_composite(im);return bg.convert('RGB')
heroes={};families=[]
for d in 'NESW':
 im=rgba(P/f'native/hero-{d}-4x.png').resize((384,704),Image.Resampling.BOX);im.save(O/f'hero-{d}-2x.png');heroes[d]=diff(im,rgba(C/f'frames/static/{d}/000.png'))
for fixture in ['L','W','N']:
 for d,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
  native=rgba(P/f'native/family-{fixture}-{d}-4x.png').resize((896,1216),Image.Resampling.BOX);native.save(O/f'family-{fixture}-{d}-2x.png');consumer=rgba(P/f'browser/chromium/nativecanvas-{fixture}-{d}.png').crop((1,1,897,1217));editor=rgba(C/f'evidence/family/published-{fixture}-{d}.png');rec={'fixture':fixture,'direction':d,'freshNativeVsSubmittedNative':diff(native,editor),'wholeNativeVsIndependent':diff(native,consumer),'ports':{}}
  for port in (['W','N'] if fixture=='L' else [fixture]):
   points=[[-.5,y,z] if port=='W' else [-y,.5,z] for y,z in [[-.45,0],[.45,0],[.45,.28],[.39,.43],[-.39,.43],[-.45,.28]]];project=[]
   for x,y,z in points:
    x,y=x*math.cos(angle)-y*math.sin(angle),x*math.sin(angle)+y*math.cos(angle);project.append((448+x*256,752-y*256-z*179.2))
   box=(math.floor(min(x for x,y in project))-3,math.floor(min(y for x,y in project))-3,math.ceil(max(x for x,y in project))+4,math.ceil(max(y for x,y in project))+4);a=native.crop(box);b=consumer.crop(box);aa=list(a.getdata());bb=list(b.getdata());opaque=[i for i,v in enumerate(aa) if v[3]==255];loss=[255-bb[i][3] for i in opaque];rgb=[[abs(aa[i][k]-bb[i][k]) for k in range(3)] for i in opaque];rec['ports'][port]={'box':box,'nativeOpaquePixels':len(opaque),'opaquePixelsWithIndependentAlphaLoss':sum(v>0 for v in loss),'maxAlphaLoss':max(loss,default=0),'maxRGBDifferenceOnOpaque':[max((v[k] for v in rgb),default=0) for k in range(3)],'meanRGBDifferenceOnOpaque':[sum(v[k] for v in rgb)/len(rgb) if rgb else 0 for k in range(3)]}
  families.append(rec)
# Actual browser configuration parity; every fresh screenshot, no inferred pass.
parity=[]
for p in sorted((P/'browser/chromium').glob('*.png')):
 q=P/'browser/headless-shell'/p.name
 if q.is_file():parity.append({'path':p.name,**diff(rgba(p),rgba(q))})
(P/'render-verification.json').write_text(json.dumps({'candidatePacketSHA256':hashlib.sha256((C/'packet.json').read_bytes()).hexdigest(),'heroes':heroes,'families':families,'browserParity':{'images':len(parity),'differentImages':sum(not r['equalRGBA'] for r in parity),'maxRGBA':[max(r['maxRGBA'][k] for r in parity) for k in range(4)]},'browserParityRecords':parity,'residualPolicy':'Fresh native versus independent RGB is preserved. Broad finite-area-light/source-extent residuals differ from alpha undercoverage and local visible seams. No whole-image parity claimed for that comparison.'},indent=2)+'\n')
# Fixed region of each real screenshot, common extent in every facing; no fitting.
for mode in ['chromium','headless-shell']:
 for fixture in ['L','W','N']:
  sheet=Image.new('RGB',(416*4,520*3),'#909090');dr=ImageDraw.Draw(sheet)
  for j,bg in enumerate(['light','gray','dark']):
   for i,d in enumerate('NESW'):
    base=rgba(P/f'browser/{mode}/{fixture}-{d}-128-{bg}-integer.png');crop=base.crop((16,128,432,584)).convert('RGB');sheet.paste(crop,(i*416,j*520+14));phone=rgba(P/f'browser/{mode}/{fixture}-{d}-32-{bg}-integer.png');sheet.paste(phone.convert('RGB'),(i*416+152,j*520+368));dr.text((i*416+5,j*520),f'{mode} {fixture} {d} cell128 / actual32',fill='#102335')
  sheet.save(O/f'{mode}-{fixture}-review-sheet.png')
# S/W exposed side evidence at original2x and exact logical128/phone32; enlarged copy is diagnostic only.
sheet=Image.new('RGB',(900,600),'#909090');dr=ImageDraw.Draw(sheet)
for i,d in enumerate(['S','W']):
 hero=rgba(C/f'frames/static/{d}/000.png');bg=background(hero,(144,144,144,255));box=(60,498,324,628);sheet.paste(bg.crop(box),(i*450,30));sheet.paste(bg.crop(box).resize((396,195),Image.Resampling.NEAREST),(i*450,190));logical=background(hero.resize((192,352),Image.Resampling.BOX),(144,144,144,255));sheet.paste(logical,(i*450+20,250));phone=background(hero.resize((48,88),Image.Resampling.BOX),(144,144,144,255));sheet.paste(phone,(i*450+240,460));dr.text((i*450+6,6),f'{d}: actual2x side / diagnostic nearest zoom / logical128 / phone32',fill='white')
sheet.save(O/'exposed-side-evidence.png')
# Native cap field comparisons, exact actual source controls.
caps=[]
for port in ['W','N']:
 for mode in ['albedo','normal']:
  a=rgba(P/f'cap-controls/{port}-{mode}-candidate.png');b=rgba(P/f'cap-controls/{port}-{mode}-reference.png');caps.append({'port':port,'mode':mode,**diff(a,b)})
(P/'cap-independent-comparison.json').write_text(json.dumps(caps,indent=2)+'\n')
# Actually used third-party module closure; stdlib/Blender/node runtime remain identified runtimes.
loaded={};L=P/'resources/python-library/PIL';L.mkdir(parents=True,exist_ok=True)
for n,m in list(sys.modules.items()):
 f=getattr(m,'__file__',None)
 if f and n.startswith('PIL') and pathlib.Path(f).is_file():
  src=pathlib.Path(f);shutil.copyfile(src,L/src.name);loaded[n]={'path':str((L/src.name).relative_to(P)),'sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
(P/'used-modules.json').write_text(json.dumps({'python':sys.executable,'Pillow':__import__('PIL').__version__,'modules':loaded,'node':'Node.js and @playwright/test from current worktree, exact consumer/browser driver bound separately','blender':'/opt/homebrew/bin/blender5.2.2 LTS d13f752e3b9c bundled bpy/mathutils/bmesh; no model writes'},indent=2)+'\n')
print(json.dumps({'heroRGBAReplay':heroes,'browserParity':{'images':len(parity),'different':sum(not r['equalRGBA'] for r in parity)},'nativeFamilyFreshVsSubmittedExact':sum(r['freshNativeVsSubmittedNative']['equalRGBA'] for r in families),'totalLocalAlphaLossPixels':sum(v['opaquePixelsWithIndependentAlphaLoss'] for r in families for v in r['ports'].values()),'capControls':caps},indent=2))
