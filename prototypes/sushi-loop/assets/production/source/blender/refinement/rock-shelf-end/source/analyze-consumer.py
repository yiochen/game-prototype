from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,json,sys
B=Path(__file__).resolve().parent;O=B.parent/'candidates/round-01';MODE=sys.argv[1] if len(sys.argv)>1 else 'fullChrome';C=O/'consumer'/MODE;res=[]
# True join strip in common registered coordinates. Native RGB residuals retained.
for kind in ['pair','closedRun']:
 for d in 'NESW':
  a=np.array(Image.open(C/f'common-{kind}-{d}.png').convert('RGBA')).astype(int);b=np.array(Image.open(O/f'family-published/{kind}-{d}.png').convert('RGBA')).astype(int)
  assert a.shape==b.shape
  yy,xx=np.indices(a.shape[:2]);mask=np.zeros(a.shape[:2],bool)
  if d in 'NS':
   joins=[160 if d=='S' else 288] if kind=='pair' else [160,288]
   for j in joins:mask|=(abs(xx-j*2)<=4)&(yy>550)&(yy<870)
  else:
   joins=[(440 if d=='E' else 312)-.43*89.6] if kind=='pair' else [312-.43*89.6,440-.43*89.6]
   for j in joins:mask|=(abs(yy-j*2)<=4)&(xx>340)&(xx<555)
  interior=(b[:,:,3]==255)&mask;deficit=(b[:,:,3]-a[:,:,3])
  opaque=(a[:,:,3]==255)&(b[:,:,3]==255);diff=np.abs(a[:,:,:3]-b[:,:,:3]);local=diff[interior]
  result={'kind':kind,'direction':d,'opaqueNativeJoinSamples':int(interior.sum()),'joinAlphaDeficitCount':int(((deficit>0)&interior).sum()),'joinAlphaDeficitMax':int(deficit[interior].max()) if interior.any() else None,'localRGBMeanAbsoluteDifference':float(local.mean()) if len(local) else None,'localRGBMaxAbsoluteDifference':int(local.max()) if len(local) else None,'broadOpaqueRGBMeanAbsoluteDifference':float(diff[opaque].mean()),'broadOpaqueRGBMaxAbsoluteDifference':int(diff[opaque].max()),'alphaDifferenceAllPixels':int((a[:,:,3]!=b[:,:,3]).sum()),'note':'RGB residual includes independently centered finite-area lights and source extents. Not a seam waiver; native/consumer actual views remain judge evidence.'};res.append(result)
  # Common-coordinate diagnostics retain whole pair/run with native left / independent right.
  canvas=Image.new('RGB',(896*2,1216),(238,232,220))
  for i,im in enumerate([Image.fromarray(b.astype('uint8'),'RGBA'),Image.fromarray(a.astype('uint8'),'RGBA')]):canvas.paste(im,(896*i,0),im)
  ImageDraw.Draw(canvas).text((10,10),f'{kind} {d}  |  connected native left  /  independent current consumer right',fill='black');canvas.save(C/f'comparison-{kind}-{d}.png')
(C/'seam-metrics.json').write_text(json.dumps({'registeredCommonFrame':[448,608],'scale':2,'metrics':res,'interpretation':'Measured evidence only. No local visible line/crack/band/alpha loss waived.'},indent=2)+'\n')
print(json.dumps(res,indent=2))
# Useful intended-size contact previews cropped in shared registered coordinates, not fitted per asset.
for kind in ['single','pair','closedRun']:
 for size in [128,32]:
  # screenshot grid retains all4 x3 backgrounds x4 phases; preserve full original as evidence.
  im=Image.open(C/f'{kind}-cell{size}-dpr1.png').convert('RGB');scale=size/128;tilew=448*scale;tileh=608*scale;startY=im.height-(12*tileh+13*8)
  # Derive sheet from browser screenshot pixels at exact fixed tiles; no sprite manipulation.
  cw,ch=(420,335) if size==128 else (120,163)
  sheet=Image.new('RGB',(cw*4,ch*12),(238,232,220));dr=ImageDraw.Draw(sheet)
  for row in range(12):
   for col in range(4):
    x=8+col*(tilew+8);y=startY+8+row*(tileh+8)
    tile=im.crop((int(x),int(y),int(x+tilew),int(y+tileh)))
    if size==128:tile=tile.crop((8,125,440,565));tile.thumbnail((cw,ch-18),Image.Resampling.LANCZOS)
    sheet.paste(tile,(col*cw+(cw-tile.width)//2,row*ch+18));dr.text((col*cw+3,row*ch+2),f'{kind} {"NESW"[row//3]} {list(["light","gray","dark"])[row%3]} phase{col} cell{size}',fill='black')
  sheet.save(O/f'consumer-{MODE}-{kind}-{size}-sheet.png')
# Long runs: complete phone/landscape viewport screenshots in a single compact visual index.
paths=sorted(C.glob('long-*-dpr1.png'));w=430;h=420;sheet=Image.new('RGB',(w*4,h*6),(238,232,220));dr=ImageDraw.Draw(sheet)
for i,p in enumerate(paths):
 im=Image.open(p).convert('RGB');im.thumbnail((w,h-24));x=i%4*w;y=i//4*h;sheet.paste(im,(x+(w-im.width)//2,y+24));dr.text((x+4,y+4),p.stem,fill='black')
sheet.save(O/f'consumer-{MODE}-long-run-sheet.png')
