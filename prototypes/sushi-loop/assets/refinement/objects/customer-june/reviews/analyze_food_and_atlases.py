import json,hashlib,math
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
P=Path(__file__).parent;O=P.parent;AS=O.parents[2];B=json.loads((O/'brief.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def alpha_measure(path):
 im=Image.open(path).convert('RGBA');a=np.asarray(im)[:,:,3];rows={}
 for t in [1,64,128,192]:
  ys,xs=np.where(a>=t);rows[str(t)]={'bboxEdgesTopOrigin':[int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1],'widthPixels':int(xs.max()-xs.min()+1),'bottommostRowIndex':int(ys.max()),'bottomEdgeRow':int(ys.max())+1,'bottomCenterRow':float(ys.max())+.5,'bottomRowSupportX':float((np.where(a[ys.max()]>=t)[0].min()+np.where(a[ys.max()]>=t)[0].max()+1)/2)}
 return {'path':str(path),'sha256':sha(path),'dimensions':list(im.size),'thresholds':rows}
output={}
for mode,food in [('main','dish-cucumber'),('runtime','dish-salmon')]:
 static=json.loads((P/(mode+'-source-static.json')).read_text());original=alpha_measure(P/(mode+'-packed-food.png'));canonicalpath=(O/B['foodDependencies'][food]['artwork']).resolve();canonical=alpha_measure(canonicalpath);uv=static['food']['uvs'];w,h=original['dimensions'];u0,v0=uv['0'];u1,v1=uv['2'];quadwidth=.35;scale=quadwidth/((u1-u0)*w)
 # World length per original source pixel after effective UV mapping; edge convention.
 maps={}
 for t in [64,128,192]:
  old=original['thresholds'][str(t)];new=canonical['thresholds'][str(t)];occup=old['widthPixels']*scale;s=occup/new['widthPixels'];cw,ch=canonical['dimensions'];x0,y0,x1,y1=new['bboxEdgesTopOrigin'];center=(x0+x1)/2;source_support_x=(old['bottomRowSupportX']-u0*w)*scale-quadwidth/2;new_left=source_support_x-new['bottomRowSupportX']*s
  # Full UV (0..1) plane local unscaled by native1.25. y is source screen-up.
  old_bottom_uv=1-old['bottomEdgeRow']/h;support_above_origin=(old_bottom_uv-v0)*h*scale
  proposed={'threshold':t,'originalOccupiedWidthWorld':occup,'sourceWorldPerPixel':scale,'canonicalWorldPerPixel':s,'canonicalFullQuadWorld':[cw*s,ch*s],'canonicalOccupiedCenterFromLeftPixels':center,'preserveSourceSupportOffsetAboveFoodRoot':support_above_origin,'newFullQuadLeftWorld':new_left,'sourceBottomRowSupportXWorld':source_support_x,'canonicalBottomRowSupportXPixel':new['bottomRowSupportX'],'newFullQuadBottomWorld':support_above_origin-(ch-new['bottomEdgeRow'])*s,'pointConvention':'pixel boundary edges: occupied x extent [xmin,xmax+1], support y at bottom edge ymax+1; pixel-center alternative documented separately','pixelCenterSupportDeltaWorld':.5*(s-scale)}
  proposed['canonicalFullQuadNativeVertices']=[[proposed['newFullQuadLeftWorld']/1.25,proposed['newFullQuadBottomWorld']/1.25,0],[(proposed['newFullQuadLeftWorld']+cw*s)/1.25,proposed['newFullQuadBottomWorld']/1.25,0],[(proposed['newFullQuadLeftWorld']+cw*s)/1.25,(proposed['newFullQuadBottomWorld']+ch*s)/1.25,0],[proposed['newFullQuadLeftWorld']/1.25,(proposed['newFullQuadBottomWorld']+ch*s)/1.25,0]]
  maps[str(t)]=proposed
 output[food]={'original':original,'canonical':canonical,'measuredSourceUV':uv,'effectiveSourceUVWidthPixels':(u1-u0)*w,'measuredNativeQuadVertices':static['food']['vertices'],'nominalQuadWorldWidth':.35,'isotropicFullUVMappingByThreshold':maps,'recommendedThreshold':128,'sourceImageBytesIndependentlyVerified':original['sha256']==static['food']['packedSHA256'],'originalSourceMatchesBackup':original['sha256']==('dd6d82508f72b2d9019f1619e5f1fe878a5ad22935ab8c86d7a79b4434f64776' if mode=='main' else '5de7475813a133bb643fa9de09adbef104c7bd20a572514a297cba54846ceafe')}
(P/'food-mapping-proposal.json').write_text(json.dumps(output,indent=2)+'\n')
# Native-cardinal registration vs original atlas labels: four first frames, no fitting.
atlas=AS/'production/sprites/customer-june';backs=AS/'refinement/backups/godot-before-warm-soft/assets/catalog/sprites/customer-june'
frames=[];raw=[]
for d in ['N','E','S','W']:
 p=backs/('stand-'+d+'.png');im=Image.open(p).convert('RGBA').crop((0,0,384,640));raw.append((d,p,im));frames.append(('legacy '+d,im))
for d in ['S','E','N','W']:
 p=P/('native-stand-'+d+'.png')
 if p.exists():frames.append(('native '+d,Image.open(p).convert('RGBA')))
canvas=Image.new('RGB',(192*4,350*2),(195,190,180));draw=ImageDraw.Draw(canvas)
for i,(name,im) in enumerate(frames):
 x=(i%4)*192;y=(i//4)*350;im=im.resize((192,320),Image.Resampling.LANCZOS);canvas.paste(im,(x,y+24),im);draw.text((x+10,y+6),name,fill='black')
canvas.save(P/'original-native-cardinal-sheet.png')
# Original atlas inventory/alpha bounds for all 480 original frames and 96 runtime frames.
metrics=[]
for mode,folder,clips in [('main',backs,list(json.loads((O/'inputs/source-rig.json').read_text())['clips'])),('runtime',AS/'refinement/backups/godot-before-warm-soft/assets/recipe-variants/sprites/customer-june',['eat-salmon','seated-wait-empty'])]:
 for clip in clips:
  clip=clip.replace('_','-')
  sheet=Image.new('RGB',(192*6,344*8),(192,190,184));draw=ImageDraw.Draw(sheet)
  for di,d in enumerate(['N','E','S','W']):
   path=folder/(clip+'-'+d+'.png');path=path if path.exists() else AS/'production/sprites/customer-june'/(clip+'-'+d+'.png');im=Image.open(path).convert('RGBA');metrics.append({'mode':mode,'clip':clip,'direction':d,'path':str(path),'sha256':sha(path),'size':list(im.size),'frames':[]})
   for frame in range(12):
    x=(frame%6)*384;y=(frame//6)*640;fr=im.crop((x,y,x+384,y+640));a=np.asarray(fr)[:,:,3];ys,xs=np.where(a>=128);metrics[-1]['frames'].append({'frame':frame,'bbox':[int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1]});fr=fr.resize((192,320),Image.Resampling.LANCZOS);sx=frame%6*192;sy=(di*2+frame//6)*344;sheet.paste(fr,(sx,sy+20),fr);draw.text((sx+6,sy+4),f'{clip} {d} f{frame}',fill='black')
  sheet.save(P/('original-'+clip+'-all48.png'))
(P/'original-atlas-measurements.json').write_text(json.dumps(metrics,indent=2)+'\n')
print(json.dumps({k:{'source':v['original'],'canonical':v['canonical'],'map128':v['isotropicFullUVMappingByThreshold']['128']} for k,v in output.items()},indent=2))
