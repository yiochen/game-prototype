"""Compact calibrated pixel evidence. No bodyRGB-invariance or pure-radiance claim."""
import sys,json,hashlib
sys.dont_write_bytecode=True
from pathlib import Path
from PIL import Image,ImageChops,ImageDraw,ImageFilter
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round03';PRE=OUT/'previews';PRE.mkdir(exist_ok=True)
A=json.loads((OUT/'controls/approved-source-old/index.json').read_text());B=json.loads((OUT/'controls/candidate-restored-old/index.json').read_text());V=json.loads((OUT/'validation.json').read_text());lookup={(r['clip'],r['direction'],r['index']):r for r in V['renders']}
assert len(A['samples'])==len(B['samples'])==18
for k in ['oldPackedSHA256','renderSettingsHash','seed','animatedSeed','renderSamples','denoise','device','view','look','exposure','gamma']:
 assert A[k]==B[k],k
assert A['samples'] and A['samples']!=B['samples']
def metrics(a,b,mask):
 diff=ImageChops.difference(a.convert('RGB'),b.convert('RGB'));n=tot=changed=over2=over8=maximum=0
 for rgb,m in zip(diff.getdata(),mask.getdata()):
  if not m:continue
  n+=1;tot+=sum(rgb);z=max(rgb);maximum=max(maximum,z);changed+=z>0;over2+=z>2;over8+=z>8
 return {'pixels':n,'meanAbsChannelDelta8bit':tot/(3*n) if n else 0,'maxChannelDelta8bit':maximum,'pixelsAnyDelta':changed,'pixelsOver2':over2,'pixelsOver8':over8}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for a,b in zip(A['samples'],B['samples']):
 key=(a['clip'],a['direction'],a['index']);assert key==(b['clip'],b['direction'],b['index']);r=lookup[key];ap=OBJ/a['path'];bp=OBJ/b['path'];cp=OBJ/r['path'];ims=[Image.open(p).convert('RGBA') for p in [ap,bp,cp]]
 mask=Image.new('L',(384,640),255)
 for im in ims:mask=ImageChops.multiply(mask,im.getchannel('A').point(lambda x:255 if x>=128 else 0))
 if r['visible']:
  exclude=Image.new('L',(384,640));ed=ImageDraw.Draw(exclude)
  for q in [a['foodQuadProjected'],r['foodQuadProjected']]:ed.polygon([tuple(p) for p in q],fill=255)
  exclude=exclude.filter(ImageFilter.MaxFilter(9));mask=ImageChops.multiply(mask,ImageChops.invert(exclude))
 cal=metrics(ims[0],ims[1],mask);actual=metrics(ims[1],ims[2],mask);alpha=ImageChops.difference(ims[0].getchannel('A'),ims[1].getchannel('A')).getextrema()[1]
 rows.append({'clip':key[0],'direction':key[1],'index':key[2],'sourceOldPath':a['path'],'restoredCandidateOldPath':b['path'],'canonicalCandidatePath':r['path'],'sourceOldSHA256':sha(ap),'restoredOldSHA256':sha(bp),'canonicalSHA256':sha(cp),'sameInputCalibration':cal,'sameInputAlphaMaxDelta':alpha,'canonicalActualRGBDelta':actual})
def aggregate(name):
 q=[r[name] for r in rows];n=sum(x['pixels'] for x in q)
 return {'measuredPixels':n,'weightedMeanAbsChannelDelta8bit':sum(x['meanAbsChannelDelta8bit']*x['pixels'] for x in q)/n,'maxChannelDelta8bit':max(x['maxChannelDelta8bit'] for x in q),'pixelsAnyDelta':sum(x['pixelsAnyDelta'] for x in q),'pixelsOver2':sum(x['pixelsOver2'] for x in q),'pixelsOver8':sum(x['pixelsOver8'] for x in q)}
report={'scope':'18representative fresh calibrated pairs: two hidden-state poses and two hold/load poses in each facing. Actual native body/material/light/render settings remain frozen in all192samples.','method':'A exact approved source old food; B unsaved candidate restored old image/restquad/UV; C actual canonical candidate native frame. A/B calibrates identical-input render repeatability. C/B reports observed canonical-food RGB change including any calibrated renderer noise; no exact bodyRGB-invariance claim and no global regrade.','mask':'Intersection of alpha>=128 in A/B/C, excluding union of entire projected old/canonical food quads dilated4native pixels for visible states. This conservative opaque nonfood screen mask is not a semantic per-material mask.','identicalSettings':{'hash':A['renderSettingsHash'],'seed':A['seed'],'animatedSeed':A['animatedSeed'],'samples':A['renderSamples'],'denoise':A['denoise'],'device':A['device'],'view':A['view'],'look':A['look'],'exposure':A['exposure'],'gamma':A['gamma']},'sameInputCalibration':aggregate('sameInputCalibration'),'canonicalActualRGBDelta':aggregate('canonicalActualRGBDelta'),'sameInputAlphaMaximumDelta8bit':max(r['sameInputAlphaMaxDelta'] for r in rows),'foodRayBehavior':'Original emissive source material participates in noncamera rays and is unchanged. Food texture radiance legitimately changes, and observed local bodyRGB is assessed separately from immutable native data.','sourceControlIndex':'candidates/round03/controls/approved-source-old/index.json','restoredControlIndex':'candidates/round03/controls/candidate-restored-old/index.json','rows':rows}
(OUT/'calibrated-radiance-validation.json').write_text(json.dumps(report,indent=2)+'\n')
# Unaltered pixel comparisons; neutral gray compositing only.
sheet=Image.new('RGB',(384*3,672*4),'#b6bbc0');d=ImageDraw.Draw(sheet)
for y,di in enumerate(['N','E','S','W']):
 row=next(r for r in rows if r['clip']=='hold' and r['direction']==di and r['index']==0)
 for x,(label,k) in enumerate([('A approved source / oldfood','sourceOldPath'),('B candidate restored / oldfood','restoredCandidateOldPath'),('C actual canonical / newfood','canonicalCandidatePath')]):
  im=Image.open(OBJ/row[k]).convert('RGBA');bg=Image.new('RGBA',im.size,'#b6bbc0');bg.alpha_composite(im);sheet.paste(bg.convert('RGB'),(x*384,y*672+32));d.text((x*384+6,y*672+10),di+' / '+label,fill='#18212b')
sheet.save(PRE/'calibrated-radiance-comparison.png');print(json.dumps({k:report[k] for k in ['sameInputCalibration','canonicalActualRGBDelta','sameInputAlphaMaximumDelta8bit']}))
