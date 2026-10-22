"""Preview-only whole-frame composition; never changes native sprites/atlases."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,math,shutil
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-05';P=O/'previews';P.mkdir(exist_ok=True);(O/'atlases').mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
D='NESW';BG={'light':'#f2f0e6','gray':'#a7a7a7','dark':'#20242a'};records=[]
def save(im,name,method):
 p=P/(name+'.png');im.save(p);records.append({'path':str(p.relative_to(B)),'sha256':sha(p),'method':method});return p
# Whole native frame region in atlas, byte-for-byte copy.
for d in D:shutil.copyfile(O/f'static-{d}.png',O/f'atlases/static-{d}.png')
sheet=Image.new('RGBA',(1536,704));logical=Image.new('RGBA',(768,352))
for i,d in enumerate(D):
 im=Image.open(O/f'static-{d}.png').convert('RGBA');sheet.alpha_composite(im,(i*384,0));logical.alpha_composite(im.resize((192,352),Image.Resampling.LANCZOS),(i*192,0))
save(sheet,'four-view-sheet','Exact registered384x704 native frames in N/E/S/W order; no crop/fitting.');save(logical,'four-view-logical','Uniform 2:1 whole-frame resample of native N/E/S/W.')
for bgname,bg in BG.items():
 s=Image.new('RGB',(768,352),bg)
 for i,d in enumerate(D):s.paste(Image.open(O/f'static-{d}.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS),(i*192,0),Image.open(O/f'static-{d}.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS))
 save(s,'standalone-'+bgname,'Whole-frame logical size on background; no alpha replacement.')
 # Fixed original/current source comparison uses complete whole frames.
 s=Image.new('RGBA',(768,704),bg)
 for i,d in enumerate(D):
  orig=Image.open(B/'source/resources/original-atlases'/f'static-{d}.png').convert('RGBA')
  if orig.size!=(384,704):orig=orig.resize((384,704),Image.Resampling.LANCZOS)
  s.alpha_composite(orig.resize((192,352),Image.Resampling.LANCZOS),(i*192,0));s.alpha_composite(Image.open(O/f'static-{d}.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS),(i*192,352))
 save(s,'source-candidate-'+bgname,'Original registered complete source atlases top row, exact candidate complete frames bottom row; common2:1 sample.')
repeat=Image.new('RGBA',(1280,1280),BG['gray'])
for q,d in enumerate(D):
 panel=Image.new('RGBA',(640,640));im=Image.open(O/f'static-{d}.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS)
 for iy in range(3):
  for ix in range(3):panel.alpha_composite(im,(192+128*ix-96,192+128*iy-248))
 repeat.alpha_composite(panel,((q%2)*640,(q//2)*640))
save(repeat,'repeated','Registered1cell pitch128logicalpx, 3x3 per facing; a readability study, no invented self-tiling claim.')
# Native full-family/open/covered/source and registered human contact views.
N=O/'native-context-v2'
for prefix in ['pair','family','family-covered','source-family']:
 size=640 if prefix=='pair' else 768;s=Image.new('RGBA',(size*4,size),BG['gray'])
 for i,d in enumerate(D):s.alpha_composite(Image.open(N/f'{prefix}-{d}.png').convert('RGBA').resize((size,size),Image.Resampling.LANCZOS),(i*size,0))
 save(s,prefix+'-all-facings','All4 native depth-tested full fixed frames, uniform2:1 sample; native family roots/actions unchanged.')
walk=Image.new('RGBA',(5*384,4*384),BG['light'])
for row,d in enumerate(D):
 for j in range(5):walk.alpha_composite(Image.open(N/f'walk-{d}-{j}.png').convert('RGBA').resize((384,384),Image.Resampling.LANCZOS),(j*384,row*384))
save(walk,'registered-human-traversal','Fixed source humanoid scale and root follows measured ground/stage/support Z; whole768logical frames uniformly reduced2:1. Visible source foot contact nearZ0; hidden attachment minimum is separately excluded in visibility audit.')
for d,a in zip(D,[math.pi,math.pi/2,0,-math.pi/2]):
 x=640+math.sin(a)*1.5*256;y=640+math.cos(a)*1.5*256-.22*179.2;box=(round(x-175),round(y-150),round(x+175),round(y+150));im=Image.open(N/f'pair-{d}.png').convert('RGBA').crop(box)
 for bgname,bg in BG.items():
  panel=Image.new('RGBA',im.size,bg);panel.alpha_composite(im);save(panel.resize((700,600),Image.Resampling.NEAREST),f'contact-{d}-{bgname}','Exact native contact/post/underside detail crop enlarged2x; RGB+alpha composited over declared background. Original complete frame retained.')
(P/'preview-manifest.json').write_text(json.dumps(records,indent=2))
print('PREVIEWS_READY',len(records))
