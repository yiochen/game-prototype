from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,math
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-car');C=P/'candidates/round-01';O=P/'reviews/round-01-independent'
checks=[];sheets=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for clip,n in [('idle',1),('highlighted',12),('clearance',12)]:
 for d in ['N','E','S','W']:
  raw=[Image.open(C/f'frames/{clip}-{d}/{i:03}.png').convert('RGBA') for i in range(n)]
  for label,size in [('logical128',(576,832)),('phone55',(248,358))]:
   views={};alphas=[f.resize(size,Image.Resampling.LANCZOS).getchannel('A').getbbox() for f in raw];bbox=(max(0,min(b[0] for b in alphas)-5),max(0,min(b[1] for b in alphas)-5),min(size[0],max(b[2] for b in alphas)+5),min(size[1],max(b[3] for b in alphas)+5));w,h=bbox[2]-bbox[0],bbox[3]-bbox[1]
   for bg in ['f5f2e9','808080','202028']:
    path=C/f'previews/all-{clip}-{d}-{label}-{bg}.png';im=Image.open(path).convert('RGB');views[bg]=[]
    for i,f in enumerate(raw):
     expected=Image.new('RGBA',size,'#'+bg);expected.alpha_composite(f.resize(size,Image.Resampling.LANCZOS));actual=im.crop((i%6*size[0],24+i//6*size[1],i%6*size[0]+size[0],24+i//6*size[1]+size[1]));checks.append({'path':str(path.relative_to(P)),'index':i,'expectedRasterEqual':expected.convert('RGB').tobytes()==actual.tobytes(),'size':size});views[bg].append(actual.crop(bbox))
   group=1 if n==1 else 3 if label=='logical128' and clip=='clearance' else 6 if label=='logical128' else 12
   for start in range(0,n,group):
    indices=list(range(start,min(n,start+group)));cols=min(3 if label=='logical128' else 6,len(indices));rows=math.ceil(len(indices)/cols);sheet=Image.new('RGB',(cols*w,3*(rows*(h+20)+24)),'#444444');draw=ImageDraw.Draw(sheet)
    for k,bg in enumerate(views):
     block=k*(rows*(h+20)+24);draw.text((4,block+5),f'{clip} {d} {label} #{bg} | fixed union crop; actual use-size pixels',fill='white')
     for j,i in enumerate(indices):
      x=(j%cols)*w;y=block+24+(j//cols)*(h+20);sheet.paste(views[bg][i],(x,y));draw.text((x+4,y+h+4),f'index{i:02}',fill='white')
    path=O/f'present-{clip}-{d}-{label}-{start:02}.png';sheet.save(path);sheets.append({'path':str(path.relative_to(P)),'sha256':sha(path),'inputs':[str((C/f'previews/all-{clip}-{d}-{label}-{bg}.png').relative_to(P)) for bg in views],'indices':indices,'crop':bbox,'scale':'None after native128/55px-cell presentation; fixed clip/view union crop removes empty margins for independent diagnostic only.'})
(O/'presentation-audit.json').write_text(json.dumps({'checks':checks,'failures':[x for x in checks if not x['expectedRasterEqual']],'contactSheets':sheets},indent=2)+'\n')
print('presentations',len({x['path'] for x in checks}),'phase-background-size checks',len(checks),'failures',sum(not x['expectedRasterEqual'] for x in checks),'sheets',len(sheets))
