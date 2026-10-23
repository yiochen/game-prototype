"""Read-only RGBA comparisons with exact source texture alpha projected via audited plane.
Masks are analysis artifacts, never used to modify native render pixels.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,hashlib
P=Path(__file__).parent;O=P.parent;C=O/'candidates/round-03';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();audit=json.loads((C/'semantic-parity.json').read_text());oldImage=P/'dependencies/dish-salmon.png';newImage=C/'resources/dish-salmon.png';assert sha(oldImage)=='5de7475813a133bb643fa9de09adbef104c7bd20a572514a297cba54846ceafe';assert sha(newImage)=='4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4'
oldA=np.array(Image.open(oldImage).convert('RGBA'))[:,:,3].astype(np.float32);newRGBA=Image.open(newImage).convert('RGBA');newA=np.array(newRGBA)[:,:,3].astype(np.float32);oldRows={(r['clip'],r['direction'],r['index']):r for r in audit['sourceRows']};newRows=audit['rows'];Y,X=np.mgrid[0:640,0:384].astype(np.float64);grid=np.stack((X+.5,Y+.5),axis=-1)
(C/'pixel-masks').mkdir(exist_ok=True);(C/'paired').mkdir(exist_ok=True)
def mask(f,a):
 if not f['visible']:return np.zeros((640,384),dtype=np.bool_)
 c=np.array(f['pixelCorners']);M=np.stack((c[1]-c[0],c[3]-c[0]),axis=1);st=(grid-c[0])@np.linalg.inv(M).T;s=st[:,:,0];t=st[:,:,1];uv=np.array(f['uv']);u=uv[0,0]+s*(uv[1,0]-uv[0,0])+t*(uv[3,0]-uv[0,0]);v=uv[0,1]+s*(uv[1,1]-uv[0,1])+t*(uv[3,1]-uv[0,1]);tx=u*a.shape[1]-.5;ty=(1-v)*a.shape[0]-.5;x0=np.floor(tx).astype(int);y0=np.floor(ty).astype(int);fx=tx-x0;fy=ty-y0;al=np.zeros_like(tx)
 for dx,dy,w in [(0,0,(1-fx)*(1-fy)),(1,0,fx*(1-fy)),(0,1,(1-fx)*fy),(1,1,fx*fy)]:
  xx=x0+dx;yy=y0+dy;valid=(xx>=0)&(xx<a.shape[1])&(yy>=0)&(yy<a.shape[0]);al[valid]+=a[yy[valid],xx[valid]]*w[valid]
 return (al>0)&(s>=0)&(s<=1)&(t>=0)&(t<=1)
def bbox(m):
 y,x=np.nonzero(m)
 return [int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1] if len(x) else None
def metrics(diff,m):
 dd=diff[m];return {'pixels':int(m.sum()),'changedPixels':int(np.any(dd>0,axis=1).sum()) if len(dd) else 0,'overOneStepPixels':int(np.any(dd>1,axis=1).sum()) if len(dd) else 0,'maxRGBA':dd.max(axis=0).tolist() if len(dd) else [0,0,0,0],'meanRGBA':dd.mean(axis=0).tolist() if len(dd) else [0,0,0,0],'changedBounds':bbox(m & np.any(diff>0,axis=2)),'overOneStepBounds':bbox(m & np.any(diff>1,axis=2))}
rows=[];clipStats={};backgrounds={'light':'#EFEBE1','gray':'#7C7C7C','dark':'#191D24'}
def flat(im,bg):
 o=Image.new('RGBA',im.size,bg);o.alpha_composite(im);return o.convert('RGB')
for r in newRows:
 clip,d,i=r['clip'],r['direction'],r['index'];old=oldRows[(clip,d,i)];op=O/f'candidates/round-02/frames/{clip}-{d}/{i:03d}.png';npth=C/f'frames/{clip}-{d}/{i:03d}.png';oi=Image.open(op).convert('RGBA');ni=Image.open(npth).convert('RGBA');a=np.array(oi);b=np.array(ni);diff=np.abs(a.astype(np.int16)-b.astype(np.int16));om=mask(old['food'],oldA);nm=mask(r['food'],newA);union=om|nm;dilated=np.array(Image.fromarray((union*255).astype('uint8')).filter(ImageFilter.MaxFilter(3)))>0
 row={'clip':clip,'direction':d,'index':i,'sourcePath':str(op.relative_to(O)),'sourceSHA256':sha(op),'candidatePath':str(npth.relative_to(O)),'candidateSHA256':sha(npth),'sourceFoodProjection':old['food']['pixelCorners'],'candidateFoodProjection':r['food']['pixelCorners'],'sourceFoodAlphaPixels':int(om.sum()),'candidateFoodAlphaPixels':int(nm.sum()),'maskPolicy':'Union of both full projected texture alpha silhouettes, bilinear source alpha sampled at native pixel centers; no rectangular exemption. Separate one-pixel dilation reports native pixel-filter/AA fringe. Projection includes naturally body-occluded food positions, never forces visibility.','allPixels':metrics(diff,np.ones((640,384),bool)),'outsideExactAlphaUnion':metrics(diff,~union),'outsideAlphaUnionPlusOnePixel':metrics(diff,~dilated),'alphaChangedOutsideUnionPlusOnePixel':int(((diff[:,:,3]>0)&~dilated).sum())}
 if clip in ['hold','load']:
  mpath=C/'pixel-masks'/f'{clip}-{d}-{i:03d}.png';Image.fromarray((union*255).astype('uint8')).save(mpath);row['maskPath']=str(mpath.relative_to(O));row['maskSHA256']=sha(mpath)
 rows.append(row)
 # Complete paired full-frame sheets for all192 phases, displayed at logical size.
for clip in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:
  sh=Image.new('RGB',(1152,1376),backgrounds['gray']);dr=ImageDraw.Draw(sh)
  for i in range(12):
   for side,roundn in enumerate(['round-02','round-03']):
    im=Image.open(O/f'candidates/{roundn}/frames/{clip}-{d}/{i:03d}.png').convert('RGBA').resize((192,320),Image.Resampling.LANCZOS);x=(i%6)*192;y=(i//6)*688+side*344;sh.paste(flat(im,backgrounds['gray']),(x,y+24));dr.text((x+4,y+5),f'{roundn} {clip}-{d} {i:02d}',fill='white')
  sh.save(C/'paired'/f'all12-{clip}-{d}.png')
# Detailed native contact comparisons at every held/load extreme; same crop per pair, no fitting.
contactRows=[]
for bg,color in backgrounds.items():
 for clip in ['hold','load']:
  for d in ['N','E','S','W']:
   sh=Image.new('RGB',(1152,530),color);dr=ImageDraw.Draw(sh)
   for j,i in enumerate([0,5,11]):
    corners=np.array(newRows[next(k for k,v in enumerate(newRows) if v['clip']==clip and v['direction']==d and v['index']==i)]['food']['pixelCorners']);cx=float(corners[:,0].mean());cy=float(corners[:,1].mean());left=max(0,min(192,int(cx)-96));top=max(0,min(400,int(cy)-170));box=(left,top,left+192,top+240)
    for side,roundn in enumerate(['round-02','round-03']):
     im=Image.open(O/f'candidates/{roundn}/frames/{clip}-{d}/{i:03d}.png').convert('RGBA');crop=flat(im.crop(box),color).resize((384,480),Image.Resampling.NEAREST);x=j*384;y=26;# overlay source/candidate separately as two compact contact sheets
     # each canvas will be assembled below; source on top in separate exported full pair per phase
     pair=Image.new('RGB',(768,514),color);pd=ImageDraw.Draw(pair)
     if side==0:sourcecrop=crop;continue
     pair.paste(sourcecrop,(0,26));pair.paste(crop,(384,26));pd.text((8,5),f'Approved02 {clip} {d} {i:02d}',fill='#ddd' if bg=='dark' else '#263342');pd.text((392,5),f'Canonical03 {clip} {d} {i:02d}',fill='#ddd' if bg=='dark' else '#263342');path=C/'paired'/f'contact-{clip}-{d}-{i:02d}-{bg}.png';pair.save(path);contactRows.append({'clip':clip,'direction':d,'index':i,'background':bg,'path':str(path.relative_to(O)),'sha256':sha(path),'sameNativeCrop':list(box),'magnification':2,'resampling':'nearest, preview only'})
for clip in ['idle','work','hold','load']:
 rr=[r for r in rows if r['clip']==clip];clipStats[clip]={'frames':len(rr),'maxRGBA':np.max([r['allPixels']['maxRGBA'] for r in rr],axis=0).tolist(),'outsideOnePixelAlphaUnionMaxRGBA':np.max([r['outsideAlphaUnionPlusOnePixel']['maxRGBA'] for r in rr],axis=0).tolist(),'outsideOnePixelAlphaUnionOverOneStepPixelsTotal':sum(r['outsideAlphaUnionPlusOnePixel']['overOneStepPixels'] for r in rr),'alphaChangedOutsideOnePixelUnionTotal':sum(r['alphaChangedOutsideUnionPlusOnePixel'] for r in rr)}
report={'schemaVersion':1,'canonicalPNG_SHA256':sha(newImage),'canonicalDecodedRGBA_SHA256':hashlib.sha256(newRGBA.tobytes()).hexdigest(),'canonicalDecodedSize':list(newRGBA.size),'sourcePackedFoodSHA256':sha(oldImage),'auditedNativeSource':audit['sourceSHA256'],'auditedNativeCandidate':audit['candidateSHA256'],'frameCount':192,'clipSummary':clipStats,'rows':rows,'contactPreviews':contactRows,'interpretation':'Physical semantic parity is independent native evidence. Difference analysis reports all changes, including RGB variation outside exact food silhouettes; projected masks do not edit or excuse shipping pixels. Existing one-step pathtrace noise is measured separately. Canonical emission/alpha/plane geometry may also change native indirect light or denoiser context; any larger residual is quantified for independent review.'};(C/'pixel-comparison.json').write_text(json.dumps(report,indent=2));print(json.dumps(clipStats,indent=2))
