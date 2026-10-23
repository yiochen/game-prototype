from PIL import Image,ImageDraw
from pathlib import Path
import json,hashlib,math
import numpy as np
OUT=Path(__file__).resolve().parent;A=OUT.parents[3]/'production'
# OUT parents: dock-floor, objects, refinement, assets
A=OUT.parents[3]/'production'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
lib=json.loads((A/'library.json').read_text());objs=lib.get('objects',[]);by={a['id']:a for a in objs};D=['N','E','S','W']
report={'productionLibrary':{'path':str(A/'library.json'),'sha256':sha(A/'library.json')},'inputs':{},'objects':{a:by[a] for a in ['dock-floor','dock-entry','workshop-hut','submarine-yellow','dock-cover','dock-post-rope']},'rasterMetrics':{},'assembled':[]}
def image(a,d,clip='static'):
 o=by[a];c=next((c for c in o['clips'] if c['id']==clip),o['clips'][0]);e=c['directions'][d];p=A/e['image'];im=Image.open(p).convert('RGBA');r=e.get('rects',[[0,0,*im.size]])[0];im=im.crop((r[0],r[1],r[0]+r[2],r[1]+r[3]));report['inputs'][str(p)]={'sha256':sha(p),'size':list(Image.open(p).size),'frame0Rect':r};return im,o
# Baseline per-facing at logical use size; native/published are unwarped whole frames.
sheet=Image.new('RGB',(448*4,510*2),'#a7a7a7');draw=ImageDraw.Draw(sheet)
for i,d in enumerate(D):
 for row,name in enumerate(['published','native']):
  p=A/f'sprites/dock-floor/static-{d}.png' if name=='published' else OUT/f'native-floor-{d}.png';im=Image.open(p).convert('RGBA');a=np.asarray(im);mask=a[:,:,3]>0;solid=a[:,:,3]>=250;coords=np.argwhere(mask);metric={'sha256':sha(p),'size':list(im.size),'alphaBBox':list(im.getbbox()),'transparentRGBNonzeroPixels':int(np.count_nonzero((a[:,:,3]==0)&np.any(a[:,:,:3]>0,axis=2))),'partialAlphaPixels':int(np.count_nonzero(mask&~solid)),'opaqueDarkPixelsRGBAllBelow12':int(np.count_nonzero(solid&np.all(a[:,:,:3]<12,axis=2)))};report['rasterMetrics'][str(p)]=metric
  bg=Image.new('RGBA',(448,480),'#a7a7a7');bg.alpha_composite(im.resize((448,480),Image.Resampling.LANCZOS));sheet.paste(bg.convert('RGB'),(448*i,510*row+25));draw.text((448*i+10,510*row+6),f'{name} {d}',fill='black')
sheet.save(OUT/'source-facings-logical.png')
# Exact registered scene composition at 2px/logical px. Fractional placements use affine resampling rather than per-sprite snapping.
def compose(items,d,mode):
 canvas=Image.new('RGBA',(1152,1280));angle={'S':0,'E':math.pi/2,'N':math.pi,'W':-math.pi/2}[d]
 for aid,p,clip in items:
  im,o=image(aid,d,clip);x,y,z=p;x,y=math.cos(angle)*x-math.sin(angle)*y,math.sin(angle)*x+math.cos(angle)*y
  root=(576+256*x,704-256*y-179.2*z);r=o.get('root',[96,248]);pos=(root[0]-2*r[0],root[1]-2*r[1]);
  # honor full-frame native sourceScale then resample whole frame to2x, never alpha-fit.
  want=tuple(2*v for v in o['frameSize']);im=im.resize(want,Image.Resampling.LANCZOS) if im.size!=want else im
  layer=im.transform(canvas.size,Image.Transform.AFFINE,(1,0,-pos[0],0,1,-pos[1]),Image.Resampling.BICUBIC);canvas=Image.alpha_composite(canvas,layer)
 p=OUT/f'published-{mode}-{d}.png';canvas.save(p);report['assembled'].append({'path':p.name,'sha256':sha(p),'facing':d,'mode':mode,'logicalFrame':[576,640],'logicalRoot':[288,352],'placements':items,'method':'whole-frame source atlas, uniform2x; affine fractional translation, straight RGBA alpha composite; no fitting or gap-hiding'})
 return canvas
for d in D:
 compose([('dock-floor',(0,0,0),'static'),('dock-entry',(0,-1.5,0),'static')],d,'entry-join')
 compose([('dock-floor',(0,0,0),'static'),('workshop-hut',(.78,.35,.23),'static'),('submarine-yellow',(-.70,-.42,.23),'dock-ready'),('dock-entry',(0,-1.5,0),'static')],d,'full-context')
# Join sheets gray logical resolution, all4native + assembled at same registration.
sheet=Image.new('RGB',(576*4,680*2),'#a7a7a7');draw=ImageDraw.Draw(sheet)
for i,d in enumerate(D):
 for row,mode in enumerate(['native','published']):
  im=Image.open(OUT/f'{mode}-entry-join-{d}.png').convert('RGBA');bg=Image.new('RGBA',im.size,'#a7a7a7');bg.alpha_composite(im);sheet.paste(bg.resize((576,640),Image.Resampling.LANCZOS).convert('RGB'),(576*i,680*row+30));draw.text((576*i+8,680*row+7),f'{mode} joined entry {d}',fill='black')
sheet.save(OUT/'source-entry-joins-logical.png')
# Single S source join detail, unscaled pixel crops across the actual connection region.
for mode in ['native','published']:
 im=Image.open(OUT/f'{mode}-entry-join-S.png');im.crop((420,1010,735,1225)).resize((945,645),Image.Resampling.NEAREST).save(OUT/f'{mode}-entry-join-S-detail.png')
# Four-facing full context at phone and logical zoom, light/gray/dark.
sheet=Image.new('RGB',(576*4,680*3),'white');draw=ImageDraw.Draw(sheet)
for row,bgcol in enumerate(['#f2f0e6','#a7a7a7','#20242a']):
 for i,d in enumerate(D):
  im=Image.open(OUT/f'published-full-context-{d}.png');bg=Image.new('RGBA',im.size,bgcol);bg.alpha_composite(im);sheet.paste(bg.resize((576,640),Image.Resampling.LANCZOS).convert('RGB'),(i*576,row*680+30));draw.text((i*576+8,row*680+5),f'published context {d} {bgcol}',fill='black' if row<2 else 'white')
sheet.save(OUT/'source-context-backgrounds-logical.png')
phone=sheet.resize((1152,1020),Image.Resampling.LANCZOS);phone.save(OUT/'source-context-backgrounds-phone.png')
(OUT/'published-raster-evidence.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'objects':list(by),'metrics':report['rasterMetrics'],'assemblyCount':len(report['assembled'])},indent=2))
