"""Honest diagnostic sheets, replay comparisons and projected local contact masks."""
from pathlib import Path
import hashlib,json,math
from PIL import Image,ImageDraw,ImageFont
import numpy as np
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;OUT=BASE/'candidates/round-01';CON=OUT/'consumer';PRE=OUT/'previews';PRE.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
write=lambda p,j:Path(p).write_text(json.dumps(j,indent=2)+'\n')
font=ImageFont.load_default(size=16)
def canvas(size):return Image.new('RGB',size,(43,48,57))
def paste(dst,src,xy,scale=1,bg=(128,128,128)):
 im=Image.open(src).convert('RGBA') if not isinstance(src,Image.Image) else src.convert('RGBA')
 if scale!=1:im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.LANCZOS)
 back=Image.new('RGBA',im.size,bg+(255,));back.alpha_composite(im);dst.paste(back.convert('RGB'),xy)
def text(im,xy,label):ImageDraw.Draw(im).text(xy,label,fill='white',font=font)
sheet=canvas((1536,736))
for i,d in enumerate('NESW'):
 text(sheet,(384*i+8,6),d+' / exact native2 frame')
 paste(sheet,OUT/f'heroes/{d}.png',(384*i,32))
sheet.save(PRE/'four-view-sheet.png')
use=canvas((1184,1224))
for row,(bg,bgn) in enumerate([((238,238,238),'light'),((128,128,128),'gray'),((21,25,35),'dark')]):
 for i,d in enumerate('NESW'):
  x=i*296;text(use,(x+8,row*400+6),d+' / '+bgn+' / cell128 + cell32')
  paste(use,OUT/f'heroes/{d}.png',(x+8,row*400+32),.5,bg)
  paste(use,OUT/f'heroes/{d}.png',(x+216,row*400+32),.125,bg)
text(use,(8,1204),'Uniform whole-frame scales only; published frames/atlas are unchanged exact native PNGs.')
use.save(PRE/'single-use.png')
replay=[]
for d in 'NESW':
 for folder,path in [('single',Path('native/static')/d/'000.png'),('actual-chain',Path('connected-native')/(d+'.png'))]:
  original=OUT/path;rep=OUT/'replay'/path;a=np.array(Image.open(original).convert('RGBA')).astype(np.int16);b=np.array(Image.open(rep).convert('RGBA')).astype(np.int16)
  replay.append({'kind':folder,'direction':d,'original':str(original.relative_to(BASE)),'originalSHA256':sha(original),'replay':str(rep.relative_to(BASE)),'replaySHA256':sha(rep),'byteIdentical':sha(original)==sha(rep),'decodedRGBAIdentical':bool(np.array_equal(a,b)),'maxChannelDelta':int(abs(a-b).max())})
assert all(r['decodedRGBAIdentical'] for r in replay if r['kind']=='single')
write(OUT/'replay-comparison.json',{'sourceSHA256':sha(HERE/'round-01.blend'),'command':'/opt/homebrew/bin/blender --factory-startup --background source/round-01.blend --python source/reproduce-round01.py -- --recapture --output candidates/round-01/replay','records':replay,'scope':'Replay from exact saved editable source; all4 single native frames decoded-exact. Native chain comparison is retained honestly, including any finite GPU/EEVEE residual; no source save or raster repair'})
results=json.loads((CON/'results.json').read_text());assembly=json.loads((OUT/'native-assembly-records.json').read_text())['captureRecords'];record_by_dir={r['direction']:r for r in assembly}
maskdir=OUT/'contact-masks';maskdir.mkdir(exist_ok=True);diffdir=OUT/'differences';diffdir.mkdir(exist_ok=True)
sections=[(-.18,.18,.04,.2),(-.09,.09,.6,.74),(.2,.26,.16,.35)]
def hull(points):
 points=sorted(set(points));cross=lambda a,b,c:(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);halves=[]
 for arr in [points,points[::-1]]:
  h=[]
  for p in arr:
   while len(h)>=2 and cross(h[-2],h[-1],p)<=0:h.pop()
   h.append(p)
  halves.append(h[:-1])
 return halves[0]+halves[1]
def stats(a,b,mask=None):
 a=a.astype(float);b=b.astype(float);alpha=abs(a[:,:,3]-b[:,:,3]);premul=abs(a[:,:,:3]*a[:,:,3,None]/255-b[:,:,:3]*b[:,:,3,None]/255).max(2)
 select=np.ones(alpha.shape,dtype=bool) if mask is None else mask
 occupied=select&((a[:,:,3]>0)|(b[:,:,3]>0));aa=alpha[select];pp=premul[select]
 return {'maskPixels':int(select.sum()),'occupiedPixels':int(occupied.sum()),'alphaMax':float(aa.max(initial=0)),'alphaMean':float(aa.mean()) if len(aa) else 0,'alphaNonzeroPixels':int((aa>0).sum()),'premultipliedRGBMax':float(pp.max(initial=0)),'premultipliedRGBMean':float(pp.mean()) if len(pp) else 0,'premultipliedRGBMeanOnOccupied':float(premul[occupied].mean()) if occupied.any() else 0,'coverageLossPixels':int((select&(a[:,:,3]==0)&(b[:,:,3]>0)).sum()),'coverageGainPixels':int((select&(a[:,:,3]>0)&(b[:,:,3]==0)).sum())}
comparisons=[]
for case in results['cases']:
 assert case['browserVersion']=='153.0.8010.12' and not case['errors']
 assert case['evidence']['actualDPR']==case['deviceScaleFactor']
 assert all(f['nativeNearestRestoredAfterResize'] and all(c['wholeCSSImageRendering']=='auto' for c in f['actualDisplayChecks']) for f in case['evidence']['fixtures'])
 prefix=case['mode']+'-'+case['id']
 for d in 'NESW':
  p=CON/(prefix+'-'+d+'-independent.png');q=CON/(prefix+'-'+d+'-native-control.png');a=np.array(Image.open(p).convert('RGBA'));b=np.array(Image.open(q).convert('RGBA'));assert a.shape==b.shape
  f=next(v for v in case['evidence']['fixtures'] if v['direction']==d);r=record_by_dir[d];cal=r['camera']['calibration'];c=f['referencePlan']['sprites'][0];plan=f['referencePlan'];scale=plan['scale'];offset=[(c['x']-plan['x'])*scale,(c['y']-plan['y'])*scale]
  angle={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[d]
  def project(x,y,z):
   X=x*math.cos(angle)-y*math.sin(angle);Y=x*math.sin(angle)+y*math.cos(angle)
   return tuple(cal['root'][i]+cal['unitX'][i]*X-cal['unitDepth'][i]*Y+cal['unitHeight'][i]*z+offset[i] for i in [0,1])
  local=[]
  for name,x in [('own-W',-.5),('canonical-middle-edge',-1.5)]:
   mask=Image.new('L',(a.shape[1],a.shape[0]),0);dr=ImageDraw.Draw(mask)
   polygons=[]
   for y0,y1,z0,z1 in sections:
    poly=hull([project(xx,yy,zz) for xx in [x-.018,x+.018] for yy in [y0,y1] for zz in [z0,z1]])
    polygons.append(poly);dr.polygon(poly,fill=255)
   mpath=maskdir/(prefix+'-'+d+'-'+name+'.png');mask.save(mpath);boolean=np.array(mask)>0
   local.append({'port':name,'planeAuthoredX':x,'bandHalfWidthWorld':.018,'method':'Convex projection of each actual canonical finite rectangle extruded by ±.018 world X; proper root rotation and measured native camera calibration, then actual consumer control draw offset. No alpha-derived fitting.','projectedPolygons':polygons,'mask':str(mpath.relative_to(BASE)),'maskSHA256':sha(mpath),'statistics':stats(a,b,boolean)})
  delta=abs(a.astype(float)-b.astype(float));premul=abs(a[:,:,:3]*a[:,:,3,None]/255-b[:,:,:3]*b[:,:,3,None]/255).max(2)
  heat=np.zeros_like(a);heat[:,:,0]=delta[:,:,3].clip(0,255);heat[:,:,1]=(premul*4).clip(0,255);heat[:,:,3]=255
  dp=diffdir/(prefix+'-'+d+'.png');Image.fromarray(heat).save(dp)
  comparisons.append({'mode':case['mode'],'case':case['id'],'direction':d,'independent':str(p.relative_to(BASE)),'independentSHA256':sha(p),'nativeControl':str(q.relative_to(BASE)),'nativeControlSHA256':sha(q),'wholeStatistics':stats(a,b),'localContacts':local,'differenceImage':str(dp.relative_to(BASE)),'differenceSHA256':sha(dp),'differenceEncoding':'R=absolute alpha residual, G=4×max absolute premultiplied RGB residual, opaque diagnostic black field; native art bytes untouched','interpretation':'Includes genuine finite-light translation and outer raster coverage differences. Numerical/material equivalence is not a waiver for visible local defects; independent judge must inspect actual images.'})
write(OUT/'consumer-comparison.json',{'asset':'wreck-end','cases':8,'comparisons':comparisons,'media':'Actual native canvases and CSS screenshots retained; 4 cases ×2 Chromium153 modes; all4×light/gray/dark within every case','scope':'Diagnostic measurements, no art verdict'})
repeat=canvas((1368,2576))
for row,d in enumerate('NESW'):
 c=next(x for x in comparisons if x['mode']=='full-chromium' and x['case']=='logical128-integer' and x['direction']==d)
 for col,(label,p) in enumerate([('Actual native3D chain',OUT/'connected-native'/(d+'.png')),('Actual570/099 independent frames',BASE/c['independent']),('Raw difference: alpha R, RGB×4 G',BASE/c['differenceImage'])]):
  x=col*456;y=row*644;text(repeat,(x+8,y+6),d+' / '+label)
  paste(repeat,p,(x,y+28),.5)
repeat.save(PRE/'repeated.png')
aliases={'four-view-sheet':str((PRE/'four-view-sheet.png').relative_to(BASE)),'single-use':str((PRE/'single-use.png').relative_to(BASE)),'repeated':str((PRE/'repeated.png').relative_to(BASE)),'phone':str((CON/'full-chromium-phone32-fractional-css.png').relative_to(BASE))}
for case in results['cases']:
 aliases['browser-'+case['mode']+'-'+case['id']]=str((CON/case['cssScreenshot']).relative_to(BASE))
repeat_aliases=[]
for row,d in enumerate('NESW'):
 c=next(x for x in comparisons if x['mode']=='full-chromium' and x['case']=='logical128-integer' and x['direction']==d)
 for col,path in enumerate([OUT/'connected-native'/(d+'.png'),BASE/c['independent'],BASE/c['differenceImage']]):
  size=Image.open(path).size;repeat_aliases.append({'path':str(path.relative_to(BASE)),'sha256':sha(path),'sheetRect':[col*456,row*644+28,round(size[0]*.5),round(size[1]*.5)],'method':'complete image, common uniform .5 scale; no fitting/cropping or alpha loss'})
write(OUT/'preview-aliases.json',{'previews':aliases,'sourceAliases':{'four-view-sheet':[{'path':str((OUT/f'heroes/{d}.png').relative_to(BASE)),'sha256':sha(OUT/f'heroes/{d}.png'),'sheetRect':[i*384,32,384,704],'method':'exact full native frame pasted 1:1 on uniform gray; alpha composition only'} for i,d in enumerate('NESW')],'single-use':'Full published frames at uniform .5 and .125 scales on light/gray/dark; intended cell128 andcell32. No silhouette fitting.','repeated':repeat_aliases},'coverageNote':'Every preview alias is an exact candidate-relative path for ROOT packet/judge direct coverage; phone is a truthful exact hash alias of its full-chromium bounded case screenshot.'})
print(json.dumps({'replayAllDecodedEqual':all(r['decodedRGBAIdentical'] for r in replay),'replayAllBytesEqual':all(r['byteIdentical'] for r in replay),'comparisons':len(comparisons),'maxOwnContactAlpha':max(c['localContacts'][0]['statistics']['alphaMax'] for c in comparisons),'maxOwnContactPremultipliedRGB':max(c['localContacts'][0]['statistics']['premultipliedRGBMax'] for c in comparisons),'previewAliases':aliases},indent=2))
