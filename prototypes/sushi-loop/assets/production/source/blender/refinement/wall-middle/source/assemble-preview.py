import json,sys,hashlib,shutil
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
B=Path(__file__).resolve().parents[1];ROUND=sys.argv[1]if len(sys.argv)>1 else 'round-01';C=B/'candidates'/ROUND
out=C/'previews';out.mkdir(exist_ok=True);assembly=C/'sprite-joins';assembly.mkdir(exist_ok=True);atlas=C/'atlases';atlas.mkdir(exist_ok=True)
angles={'N':180,'E':90,'S':0,'W':-90};backgrounds={'light':(242,238,228),'gray':(122,126,132),'dark':(24,29,39)}
frames={d:Image.open(C/'raw'/f'static-{d}-0000.png').convert('RGBA')for d in angles};previews={};metrics={};placements={}
def backing(im,bg):
 a=Image.new('RGBA',im.size,bg+(255,));a.alpha_composite(im);return a.convert('RGB')
def save(im,name):im.save(out/name);previews[name.removesuffix('.png')]=str((out/name).relative_to(B))
# Full logical frames, unchanged registration, one row each background.
sheet=Image.new('RGB',(4*192,3*380),(255,255,255));draw=ImageDraw.Draw(sheet)
for row,(name,bg)in enumerate(backgrounds.items()):
 for col,d in enumerate(angles):
  sheet.paste(backing(frames[d],bg).resize((192,352),Image.Resampling.LANCZOS),(col*192,row*380+28));draw.text((col*192+10,row*380+8),d+' · '+name,fill=(0,0,0))
save(sheet,'four-view-logical-backgrounds.png')
# Non-downsampled 2x frames strip.
sheet=Image.new('RGB',(4*384,732),backgrounds['gray']);draw=ImageDraw.Draw(sheet)
for n,d in enumerate(angles):sheet.paste(backing(frames[d],backgrounds['gray']),(n*384,28));draw.text((n*384+8,8),d,fill='white')
save(sheet,'four-view-sheet.png')
for d in angles:
 shutil.copy2(C/'raw'/f'static-{d}-0000.png',atlas/f'static-{d}.png')
 native=Image.open(C/'native-joins'/f'static-{d}-3modules.png').convert('RGBA');im=Image.new('RGBA',native.size)
 # Source publisher ports: x local maps to x ±256 for N/S, y ±256 for E/W.
 offsets={'N':[(256,0),(0,0),(-256,0)],'E':[(0,256),(0,0),(0,-256)],'S':[(-256,0),(0,0),(256,0)],'W':[(0,-256),(0,0),(0,256)]}[d]
 # Furthest module first, nearest to camera last. Root depth becomes screen Y.
 positions=sorted([(256+dx,256+dy)for dx,dy in offsets],key=lambda p:p[1]);placements[d]=[{'frame':f'raw/static-{d}-0000.png','frameOrigin':list(p),'root':[p[0]+192,p[1]+512]}for p in positions]
 for p in positions:im.alpha_composite(frames[d],p)
 im.save(assembly/f'static-{d}-3modules.png')
 a=np.asarray(native).astype(float);b=np.asarray(im).astype(float);mask=(a[:,:,3]>0)|(b[:,:,3]>0);full=(a[:,:,3]>250)&(b[:,:,3]>250)
 rgbdiff=np.abs(a[:,:,:3]-b[:,:,:3]);metrics[d]={'alphaMaxDelta':float(np.abs(a[:,:,3]-b[:,:,3]).max()),'alphaMeanDeltaOnUnion':float(np.abs(a[:,:,3]-b[:,:,3])[mask].mean()),'opaqueRGBMeanDelta':float(rgbdiff[full].mean()),'opaqueRGBP99Delta':float(np.percentile(rgbdiff[full],99)),'opaqueRGBMaxDelta':float(rgbdiff[full].max()),'unionPixels':int(mask.sum()),'pixelsOpaqueRGBDeltaOver10':int((rgbdiff.max(axis=2)[full]>10).sum())}
 # Both actual assembled methods on three backgrounds, display at logical pitch.
 compare=Image.new('RGB',(896,3*640),backgrounds['light']);draw=ImageDraw.Draw(compare)
 for i,(name,bg)in enumerate(backgrounds.items()):
  for j,(title,img)in enumerate([('Native 3 modules',native),('Independent RGBA sprites',im)]):
   compare.paste(backing(img,bg).resize((448,608),Image.Resampling.LANCZOS),(j*448,i*640+28));draw.text((j*448+8,i*640+8),d+' · '+title+' · '+name,fill='black')
 save(compare,f'join-{d}-logical-backgrounds.png')
 # Native/independent boundary crop, raw source pixels enlarged 2x.
 if d in 'NS':boxes=[(304,530,336,810),(560,530,592,810)]
 else:boxes=[(390,428,506,490),(390,684,506,746)]
 crops=Image.new('RGB',(2*max((r-l)*2 for l,t,r,b in boxes),sum((b-t)*2+28 for l,t,r,b in boxes)),backgrounds['gray']);draw=ImageDraw.Draw(crops);yy=0
 for k,box in enumerate(boxes):
  for j,(title,img)in enumerate([('Native',native),('Independent',im)]):
   cr=backing(img,backgrounds['gray']).crop(box);cr=cr.resize((cr.width*2,cr.height*2),Image.Resampling.NEAREST);crops.paste(cr,(j*crops.width//2,yy+28));draw.text((j*crops.width//2+3,yy+6),title+' seam '+str(k+1),fill='white')
  yy+=(box[3]-box[1])*2+28
 save(crops,f'join-{d}-boundary-crops.png')
 # Alpha/RGB difference for troubleshooting, no correction to candidate sprites.
 diff=np.zeros(a.shape,dtype=np.uint8);diff[:,:,:3]=np.clip(rgbdiff*8,0,255);diff[:,:,3]=(mask*255).astype('uint8');Image.fromarray(diff).save(out/f'join-{d}-difference-x8.png');previews[f'join-{d}-difference-x8']=str((out/f'join-{d}-difference-x8.png').relative_to(B))
(C/'assembly-validation.json').write_text(json.dumps({'method':'Exact source roots and projected port pitch; alpha-over exported native RGBA frames in depth order; no pixel adjustment or seam patch.','root':[448,768],'frame':[896,1216],'pitch':256,'placements':placements,'nativeIndependentComparison':metrics},indent=2))
(C/'previews-map.json').write_text(json.dumps(previews,indent=2));print(json.dumps(metrics,indent=2))
