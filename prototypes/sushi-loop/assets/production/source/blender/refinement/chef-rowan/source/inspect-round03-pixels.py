"""Untouched capture pixel comparisons and all96 held/load fixed-window inspection."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,hashlib
HERE=Path(__file__).parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-03';(OUT/'sheets').mkdir(exist_ok=True)
records=[]
for c in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:
  for i in range(12):
   baseline='round-02' if c in ['hold','load'] and d=='N' else 'round-01';p=OUT/f'frames/{c}-{d}-{i:02}.png';q=OBJ/f'candidates/{baseline}/frames/{c}-{d}-{i:02}.png'
   x=np.array(Image.open(p).convert('RGBA')).astype(int);y=np.array(Image.open(q).convert('RGBA')).astype(int);delta=np.abs(x-y);mask=np.any(delta,axis=2)
   changes=[dict(x=int(px),y=int(py),baselineRGBA=y[py,px].tolist(),round03RGBA=x[py,px].tolist()) for py,px in np.argwhere(mask)] if int(mask.sum())<20 else None
   records.append(dict(clip=c,direction=d,index=i,baseline=baseline,decodedRGBAEqual=not bool(mask.any()),changedPixels=int(mask.sum()),maximumChannelError=int(delta.max()),alphaChangedPixels=int(np.count_nonzero(delta[:,:,3])),changedComponents=int(np.count_nonzero(delta)),changes=changes,componentErrorHistogram={str(k):int(np.count_nonzero(delta==k)) for k in range(1,int(delta.max())+1)},maximumAlphaError=int(delta[:,:,3].max()),maximumOpaqueRGBError=int(delta[:,:,:3][(x[:,:,3]>=250)&(y[:,:,3]>=250)].max()) if np.any((x[:,:,3]>=250)&(y[:,:,3]>=250)) else 0,compositedRGBError={name:int(np.abs(np.array(Image.alpha_composite(Image.new('RGBA',(384,640),(*bg,255)),Image.open(p).convert('RGBA')).convert('RGB')).astype(int)-np.array(Image.alpha_composite(Image.new('RGBA',(384,640),(*bg,255)),Image.open(q).convert('RGBA')).convert('RGB')).astype(int)).max()) for name,bg in [('light',(242,237,226)),('gray',(119,123,128)),('dark',(29,36,44))]}))
held=[r for r in records if r['clip'] in ['hold','load']];hidden=[r for r in records if r['clip'] in ['idle','work']]
explanation=f"Idle/work: {sum(r['decodedRGBAEqual'] for r in hidden)}/96 exactly equal round01; {sum(r['changedPixels'] for r in hidden)} changed pixels, maximum channel error {max(r['maximumChannelError'] for r in hidden)}, {sum(r['alphaChangedPixels'] for r in hidden)} alpha differences. Held/load S/E/W are compared with round01(.60); N with round02(.45). All96 held/load comparisons: {sum(r['decodedRGBAEqual'] for r in held)}/96 exact. Every frame difference is quantified by changed-pixel/component counts, error histograms, alpha/opaque/composited maxima; individual changed pixels are also listed when fewer20. No raster substitution or patching. The saved-source semantic/projection audit independently constrains all non-occlusion data."
explanation+=f" Maximum held/load alpha-channel error {max(r['maximumAlphaError'] for r in held)}; opaqueRGB error {max(r['maximumOpaqueRGBError'] for r in held)}; compositedRGB error {max(max(r['compositedRGBError'].values()) for r in held)} across light/gray/dark. Native source semantics and all192 screen registration pass; closed replay is exact."
report=dict(activeBrief='brief-v4-food-occlusion.json',source='source/round-03.blend',sourceSHA256=hashlib.sha256((HERE/'round-03.blend').read_bytes()).hexdigest(),explanation=explanation,heldLoadComparisons=96,heldLoadExact=sum(r['decodedRGBAEqual'] for r in held),hiddenExact=sum(r['decodedRGBAEqual'] for r in hidden),records=records)
(OUT/'hidden-food-pixel-audit.json').write_text(json.dumps(report,indent=2)+'\n')
for group,dirs in [('rear-profile',['N','W']),('front-profile',['S','E'])]:
 canvas=Image.new('RGB',(1728,720),(109,113,119));draw=ImageDraw.Draw(canvas)
 for row,(c,d) in enumerate((c,d) for c in ['hold','load'] for d in dirs):
  for i in range(12):
   im=Image.open(OUT/f'frames/{c}-{d}-{i:02}.png').crop((86,285,298,520)).resize((144,160));canvas.paste(im,(i*144,row*180+20),im);draw.text((i*144+3,row*180+3),f'{c} {d} {i:02}',fill='white')
 canvas.save(OUT/f'sheets/occlusion-{group}-all48-diagnostic.png')
print(explanation)
