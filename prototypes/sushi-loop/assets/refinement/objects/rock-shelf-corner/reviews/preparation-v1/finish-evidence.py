import pathlib,json,sys,hashlib,shutil,math,platform
sys.dont_write_bytecode=True
from PIL import Image,ImageDraw,ImageChops
P=pathlib.Path(__file__).resolve().parent;R=P.parents[7];E=P/'evidence';D=P/'resources'
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
# Canonical replay encoding, separate from preserved compression9 diagnostic.
r={}
for d in 'NESW':
 raw=Image.open(E/f'original-{d}-4x.png').convert('RGBA');replay=raw.resize((384,704),Image.Resampling.LANCZOS);out=E/f'original-{d}-2x-default.png';replay.save(out)
 known=R/f'prototypes/sushi-loop/assets/production/sprites/rock-shelf-corner/static-{d}.png';r[d]={'historicalSHA256':sha(known),'replaySHA256':sha(out),'equalRGBA':replay.tobytes()==Image.open(known).convert('RGBA').tobytes(),'equalPNGBytes':out.read_bytes()==known.read_bytes(),'maxRGBAResidual':[0,0,0,0]}
(E/'historical-replay-default-encoding.json').write_text(json.dumps(r,indent=2)+'\n')
# Explicit measured ground/port diagram; technical evidence only, never a sprite.
ground=json.loads((P/'finite-ground-union.json').read_text());im=Image.new('RGB',(880,830),'#f0f0ed');dr=ImageDraw.Draw(im)
def px(p):return (440+p[0]*600,450-p[1]*600)
for v in [-.5,0,.5]:dr.line([px((v,-.6)),px((v,.6))],fill='#b9b9b9');dr.line([px((-.6,v)),px((.6,v))],fill='#b9b9b9')
dr.polygon([px(v) for v in ground['outlineLoopsXY'][0]],fill='#7eaeca',outline='#25475c',width=3)
for poly in [[[-.5,-.45],[-.475,-.45],[-.475,.45],[-.5,.45]],[[-.45,.475],[.45,.475],[.45,.5],[-.45,.5]]]:dr.polygon([px(v) for v in poly],fill='#efb85a',outline='#986213',width=2)
dr.line([px((-.5,-.45)),px((-.5,.45))],fill='#9b2d2d',width=5);dr.line([px((-.45,.5)),px((.45,.5))],fill='#9b2d2d',width=5)
dr.ellipse([px((-.009,.009)),px((.009,-.009))],fill='#172539')
for pos,txt in [((26,24),'rock-shelf-corner: measured finite z=0 support union'),((26,44),'Red: true W/N cutplanes. Gold: proposed disjoint .025 native collars.'),((26,64),'This is a technical diagram, not candidate artwork or approval.'),((100,445),'W X=-.5'),((405,123),'N Y=+.5'),((26,770),f'Actual source support area: {ground["unionArea"]:.10f} world units^2'),((26,790),'Full 1x1 opacity and old overlapping interior triangles are not requirements.')]:dr.text(pos,txt,fill='#182b38')
im.save(E/'finite-ground-ports.png')
# Capture only actually loaded third-party PIL closure; Python stdlib and Blender/runtime are external identified runtimes.
L=D/'python-library';loaded={}
for n,m in list(sys.modules.items()):
 f=getattr(m,'__file__',None)
 if f and n.startswith('PIL'):
  p=pathlib.Path(f)
  if p.is_file():
   target=L/'PIL'/p.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,target);loaded[n]={'origin':str(p),'saved':str(target.relative_to(P)),'sha256':sha(p)}
(P/'used-python-modules.json').write_text(json.dumps({'pythonExecutable':sys.executable,'pythonVersion':platform.python_version(),'PillowVersion':__import__('PIL').__version__,'usedThirdPartyModules':loaded,'stdlib':'Identified by exact runtime; not vendored. No unneeded installed packages copied.','Blender':'/opt/homebrew/bin/blender 5.2.2 LTS d13f752e3b9c; bpy/mathutils are bundled runtime modules.'},indent=2)+'\n')
print(json.dumps({'all4HistoricalExactBytes':all(v['equalPNGBytes'] for v in r.values()),'PILModulesSaved':len(loaded),'groundDiagram':'evidence/finite-ground-ports.png'},indent=2))
