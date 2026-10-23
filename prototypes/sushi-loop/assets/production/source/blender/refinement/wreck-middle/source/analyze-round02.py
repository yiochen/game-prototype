"""Identity publication, exact world-pitch assembly and honest finite port comparisons."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,math,hashlib,shutil
import numpy as np
B=Path(__file__).resolve().parent.parent;O=B/'candidates/round-02';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
D=['N','E','S','W'];angles={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2};colors={'light':(238,238,238,255),'gray':(128,128,128,255),'dark':(21,25,35,255)}
fields=json.loads((O/'canonical-endpoint-fields.json').read_text());results=[]
font=ImageFont.load_default(size=16)
def text(im,xy,s,fill=(240,240,240)):ImageDraw.Draw(im).text(xy,s,font=font,fill=fill)
# Exact identity publication. No decoded-pixel transformation at any point.
for d in D:
 raw=O/'native/static'/d/'000.png'
 for dest in [O/'frames/static'/d/'000.png',O/'atlases'/('static-'+d+'.png')]:
  dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(raw,dest)
 im=Image.open(raw).convert('RGBA');vertical=d in ['E','W'];size=(384,1216) if vertical else (896,704);origin=(192,752) if vertical else (448,496)
 independent=Image.new('RGBA',size)
 for k in range(3):independent.alpha_composite(im,(0,k*256) if vertical else (k*256,0))
 path=O/'independent-repeated'/f'{d}.png';path.parent.mkdir(exist_ok=True);independent.save(path)
 native=Image.open(O/'connected-native'/f'{d}.png').convert('RGBA');assert native.size==size
 a=np.array(independent).astype(int);b=np.array(native).astype(int);diff=np.abs(a-b);rgbaMax=diff.max(axis=(0,1)).tolist();opaque=(a[:,:,3]==255)&(b[:,:,3]==255)
 # Project the actual finite canonical side quads on the two internal joints.
 mask=Image.new('L',size);dr=ImageDraw.Draw(mask);angle=angles[d];co,si=math.cos(angle),math.sin(angle)
 def px(p,module):
  x,y,z=p;x+=module;xx=x*co-y*si;yy=x*si+y*co
  return(origin[0]+256*xx,origin[1]-256*yy-179.2*z)
 for module,side in [(-1,'E'),(0,'W'),(0,'E'),(1,'W')]:
  for rail in fields['fields'].values():
   for face in rail[side]:dr.polygon([px(p,module) for p in face['vertices']],fill=255)
 mask.save(O/'independent-repeated'/f'{d}-finite-collar-mask.png');m=np.array(mask)>0
 interiorLoss=(b[:,:,3]==255)&(a[:,:,3]<255)&m;outerResidual=((a[:,:,3]>0)&(a[:,:,3]<255))&~m
 rgbaDiff=Image.fromarray(np.clip(diff*4,0,255).astype('uint8'),'RGBA');rgbaDiff.putalpha(255);rgbaDiff.save(O/'independent-repeated'/f'{d}-raw-difference-x4.png')
 hole=Image.fromarray((interiorLoss*255).astype('uint8'),'L');hole.save(O/'independent-repeated'/f'{d}-interior-alpha-defects.png')
 # Side-on S/N local seam contrast in physically continuous opaque collar rows.
 seamStats=[]
 if not vertical:
  for x in [320,576]:
   rows=m[:,max(0,x-1):x+2].all(1)&opaque[:,x-1]&opaque[:,x]
   jump=np.max(np.abs(a[:,x,:3]-a[:,x-1,:3]),axis=1)
   neighbors=np.maximum(np.max(np.abs(a[:,x-1,:3]-a[:,x-2,:3]),axis=1),np.max(np.abs(a[:,x+1,:3]-a[:,x,:3]),axis=1))
   seamStats.append({'column':x,'opaqueFiniteCollarRows':int(rows.sum()),'maximumSeamRGBStep':int(jump[rows].max()) if rows.any() else None,'maximumNeighborRGBStep':int(neighbors[rows].max()) if rows.any() else None})
 results.append({'direction':d,'independent':str(path.relative_to(B)),'nativeConnected':str((O/'connected-native'/f'{d}.png').relative_to(B)),'exactCellSpacingNative':256,'rawRGBAMaxDifference':rgbaMax,'rawDifferentPixels':int((diff>0).any(2).sum()),'finiteCollarPixelCount':int(m.sum()),'finiteCollarOpaqueRGBMax':int(diff[:,:,:3][m&opaque].max()) if (m&opaque).any() else None,'finiteCollarInteriorAlphaLossPixels':int(interiorLoss.sum()),'outerPartialAlphaPixelCount':int(outerResidual.sum()),'seamContrast':seamStats,'interpretation':'Raw finite-light/off-center and outside-silhouette precision differences are retained, not repaired or waived. Actual visible judgment is independent.'})
# All four registered heroes at logical128 on neutral gray.
sheet=Image.new('RGB',(4*212,390),(58,69,83))
for i,d in enumerate(D):
 im=Image.open(O/'native/static'/d/'000.png').convert('RGBA').resize((192,352),Image.Resampling.LANCZOS);sheet.paste(Image.new('RGB',im.size,(128,128,128)),(i*212+10,28));sheet.paste(im,(i*212+10,28),im);text(sheet,(i*212+10,6),d+' / logical128')
sheet.save(O/'four-view-sheet.png')
# Native and independent assemblies at exact same scale, all4; three backgrounds
# are covered in separate strips. All transforms below are review presentation only.
width,height=2780,2200;sheet=Image.new('RGB',(width,height),(57,68,81));y=28
for d in D:
 ia=Image.open(O/'independent-repeated'/f'{d}.png').convert('RGBA');na=Image.open(O/'connected-native'/f'{d}.png').convert('RGBA');scale=.5 if d in ['N','S'] else .375
 out=(round(ia.width*scale),round(ia.height*scale));text(sheet,(10,y),d+' independent / native connected; source2 pixels, same scale.');y+=24
 for j,(_,bg) in enumerate(colors.items()):
  for k,im in enumerate([ia,na]):
   comp=Image.alpha_composite(Image.new('RGBA',im.size,bg),im).convert('RGB').resize(out,Image.Resampling.LANCZOS)
   sheet.paste(comp,(10+j*920+k*(out[0]+8),y))
 y+=out[1]+14
sheet=sheet.crop((0,0,width,y+4));sheet.save(O/'repeated.png')
# Use-size phone32: all4 repeated facings on light/gray/dark, and individual heroes.
sheet=Image.new('RGB',(520,1100),(57,68,81));y=12
for d in D:
 text(sheet,(8,y),d+' / phone32');y+=24
 ia=Image.open(O/'independent-repeated'/f'{d}.png').convert('RGBA');hero=Image.open(O/'native/static'/d/'000.png').convert('RGBA')
 for j,(_,bg) in enumerate(colors.items()):
  comp=Image.alpha_composite(Image.new('RGBA',ia.size,bg),ia).resize((ia.width//8,ia.height//8),Image.Resampling.LANCZOS).convert('RGB');sheet.paste(comp,(8+j*172,y))
 y+=ia.height//8+8
sheet=sheet.crop((0,0,520,y+4));sheet.save(O/'phone.png')
# The exact raw difference and masks remain evidence; a single compact contact
# sheet makes all4 honest numerical residuals visible without replacing use size.
sheet=Image.new('RGB',(4*238,660),(57,68,81))
for i,d in enumerate(D):
 diff=Image.open(O/'independent-repeated'/f'{d}-raw-difference-x4.png').convert('RGB');mask=Image.open(O/'independent-repeated'/f'{d}-finite-collar-mask.png').convert('RGB');s=min(220/diff.width,550/diff.height);size=(round(diff.width*s),round(diff.height*s));sheet.paste(diff.resize(size),(i*238+8,50));text(sheet,(i*238+8,8),d+' raw abs RGBA x4');text(sheet,(i*238+8,30),'No correction applied')
sheet.save(O/'native-differences.png')
report={'asset':'wreck-middle','identityPublication':{d:{'nativeSHA256':sha(O/'native/static'/d/'000.png'),'publishedSHA256':sha(O/'frames/static'/d/'000.png'),'atlasSHA256':sha(O/'atlases'/('static-'+d+'.png'))} for d in D},'comparisons':results,'reviewPresentation':'Pillow resizing/composites only in named previews; raw captures/atlases are exact native PNG bytes. Full frames retained; preview-sheet final canvas trim removes unused layout padding only.','sourceHistoricalEvidence':'Frozen preparation native2 probe is an unedited-original source diagnostic, separate from candidate evidence. Rejected packed-normal measurements remain in source/.','allInteriorCollarsOpaqueWhereNativeOpaque':all(r['finiteCollarInteriorAlphaLossPixels']==0 for r in results)}
(O/'assembly-analysis.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
