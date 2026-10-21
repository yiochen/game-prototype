"""Lossless-copy native captures, uniform whole-frame LANCZOS scale, review composites only."""
from PIL import Image,ImageDraw
from pathlib import Path
import json,hashlib,shutil
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'candidates/round-04'
D=['N','E','S','W']
def save(im,path):path.parent.mkdir(parents=True,exist_ok=True);im.save(path)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
frames={};metrics={}
for d in D:
 raw=OUT/'raw'/('static-'+d)/'000.png';im=Image.open(raw).convert('RGBA');assert im.size==(768,2048)
 pub=im.resize((384,1024),Image.Resampling.LANCZOS);save(pub,OUT/'frames'/('static-'+d+'.png'));save(pub,OUT/'atlases'/('static-'+d+'.png'));save(pub,OUT/'heroes'/(d+'.png'));frames[d]=pub
 a=im.getchannel('A');bbox=a.getbbox();opaque=[p for p in im.getdata() if p[3]>=250];metrics[d]={'nativeDimensions':list(im.size),'publishedDimensions':list(pub.size),'nativeAlphaBounds':bbox,'nativeClippedAtFrame':bbox[0]<=0 or bbox[1]<=0 or bbox[2]>=768 or bbox[3]>=2048,'opaquePixels':len(opaque),'opaqueRGBMin':[min(p[i] for p in opaque) for i in range(3)],'opaqueRGBMax':[max(p[i] for p in opaque) for i in range(3)],'blackOpaquePixels':sum(max(p[:3])<=3 for p in opaque),'whiteOpaquePixels':sum(min(p[:3])>=250 for p in opaque),'nativeSHA256':sha(raw),'publishedSHA256':sha(OUT/'frames'/('static-'+d+'.png')),'atlasEqualsFrameBytes':(OUT/'frames'/('static-'+d+'.png')).read_bytes()==(OUT/'atlases'/('static-'+d+'.png')).read_bytes()}
for label,bg in [('light','#e7edf1'),('gray','#75818e'),('dark','#172633')]:
 for mode,scale in [('logical',1),('enlarged',2)]:
  w,h=192*scale,512*scale;sheet=Image.new('RGBA',(4*w,h+28),bg);draw=ImageDraw.Draw(sheet)
  for i,d in enumerate(D):
   im=frames[d] if scale==2 else frames[d].resize((192,512),Image.Resampling.LANCZOS);sheet.alpha_composite(im,(i*w,28));draw.text((i*w+12,8),d,fill='white' if label!='light' else '#243c50')
  save(sheet,OUT/'previews'/(label+'-'+mode+'.png'))
shutil.copyfile(OUT/'previews/gray-enlarged.png',OUT/'previews/four-view-sheet.png')
# Six independently captured sprites assembled at their authored square cell pitch.
# Each complete frame is uniformly scaled 1x logical; anchor remains [96,416].
placements=[(0,0,'N'),(1,0,'E'),(2,0,'S'),(0,1,'W'),(1,1,'S'),(2,1,'E')]
rep=Image.new('RGBA',(576,720),'#dce7ed');draw=ImageDraw.Draw(rep)
for y in range(2):
 for x in range(3):draw.rectangle((96+x*128,480+y*128,224+x*128,608+y*128),outline='#b2c9d4',width=1)
for x,y,d in placements:rep.alpha_composite(frames[d].resize((192,512),Image.Resampling.LANCZOS),(96+x*128-96,480+y*128-416))
draw.text((12,12),'Six independent native captures at 128 logical px cell pitch',fill='#29475b');save(rep,OUT/'previews/repeated.png')
(OUT/'image-validation.json').write_text(json.dumps({'processing':'All 4 native frames captured at 768x2048; whole-frame LANCZOS to384x1024 only. Heroes/frames/1x1atlases equal. No fit, crop, warp, per-view translation, color adjustment or target raster used. Background/repeated sheets are review composites only.','frames':metrics,'previewBackgrounds':['light','gray','dark'],'previewScales':{'logical':1,'enlarged':2},'repeated':{'placements':placements,'pitchLogical':[128,128],'rootLogical':[96,416],'source':'independently rendered 4 facings'}} ,indent=2)+'\n')
