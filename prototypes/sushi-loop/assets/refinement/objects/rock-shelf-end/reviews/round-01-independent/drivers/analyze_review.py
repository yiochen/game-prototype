from pathlib import Path
from PIL import Image,ImageDraw
import json,hashlib,numpy as np
R=Path(__file__).resolve().parents[1];O=R.parent.parent;C=O/'candidates/round-01';metrics={'singleReplay':{},'nativeFamilyReplay':{},'consumerRawAgainstPacket':{},'crossModeRaw':{},'seams':[]};mapping=[]
def compare(a,b):
 a=np.array(a.convert('RGBA')).astype(int);b=np.array(b.convert('RGBA')).astype(int);return {'pixelsDifferent':int(np.any(a!=b,axis=-1).sum()),'maxRGBAComponent':int(abs(a-b).max()),'meanAbsRGBA':abs(a-b).mean((0,1)).tolist()}
for d in 'NESW':
 im=Image.open(R/f'captures/native/single-{d}-4x.png');pub=im.resize((384,704),Image.Resampling.BOX);pub.save(R/f'captures/native/single-{d}-2x.png');metrics['singleReplay'][d]=compare(pub,Image.open(C/f'frames/static/{d}/000.png'))
for kind in ['pair','closedRun']:
 sheet=Image.new('RGB',(1248,1984),'#eee8dc');draw=ImageDraw.Draw(sheet)
 for row,d in enumerate('NESW'):
  im=Image.open(R/f'captures/native/{kind}-{d}-4x.png');pub=im.resize((896,1216),Image.Resampling.BOX);pub.save(R/f'captures/native/{kind}-{d}-2x.png');metrics['nativeFamilyReplay'][kind+'-'+d]=compare(pub,Image.open(C/f'family-published/{kind}-{d}.png'))
  modes={mode:Image.open(R/f'captures/consumer/{mode}-raw-{kind}-{d}.png') for mode in ['fullChrome','shell']}
  for mode,ima in modes.items():metrics['consumerRawAgainstPacket'][f'{mode}-{kind}-{d}']=compare(ima,Image.open(C/f'consumer/{mode}/common-{kind}-{d}.png'))
  metrics['crossModeRaw'][kind+'-'+d]=compare(modes['fullChrome'],modes['shell'])
  for col,(label,image) in enumerate([('native',pub),('fullChrome',modes['fullChrome']),('shell',modes['shell'])]):
   common=image.resize((448,608),Image.Resampling.BOX).crop((16,128,432,608));bg=Image.new('RGBA',common.size,'#eee8dc');bg.alpha_composite(common.convert('RGBA'));sheet.paste(bg.convert('RGB'),(col*416,row*496+16));draw.text((col*416+2,row*496+2),f'{kind} {d} {label} · cell128 common crop',fill='black')
  aa=np.array(modes['fullChrome'].convert('RGBA')).astype(int);nn=np.array(pub.convert('RGBA')).astype(int);yy,xx=np.indices(aa.shape[:2]);mask=np.zeros(aa.shape[:2],bool)
  if d in 'NS':
   joins=[160 if d=='S' else 288] if kind=='pair' else [160,288]
   for j in joins:mask|=(abs(xx-2*j)<=4)&(yy>550)&(yy<870)
  else:
   joins=[(440 if d=='E' else 312)-.43*89.6] if kind=='pair' else [312-.43*89.6,440-.43*89.6]
   for j in joins:mask|=(abs(yy-2*j)<=4)&(xx>340)&(xx<555)
  opaque=(nn[:,:,3]==255)&mask;deficit=nn[:,:,3]-aa[:,:,3];diff=abs(nn[:,:,:3]-aa[:,:,:3]);region=(nn[:,:,3]==255)&(aa[:,:,3]==255)
  loc=np.unravel_index(np.argmax(np.where(opaque[:,:,None],diff,-1)),diff.shape)
  metrics['seams'].append({'kind':kind,'direction':d,'opaqueJoinSamples':int(opaque.sum()),'alphaDeficitCount':int(((deficit>0)&opaque).sum()),'alphaDeficitMax':int(deficit[opaque].max()),'localRGBMax':int(diff[opaque].max()),'localRGBMean':float(diff[opaque].mean()),'localMaxCoordinateXY':[int(loc[1]),int(loc[0])],'broadRGBMax':int(diff[region].max()),'broadRGBMean':float(diff[region].mean()),'alphaDifferenceGlobalPixels':int((nn[:,:,3]!=aa[:,:,3]).sum())})
 sheet.save(R/f'captures/{kind}-native-consumer-cell128.png')
for mode in ['fullChrome','shell']:
 raw=Image.open(R/f'captures/consumer/{mode}-128-both-dpr1.png');sheet=Image.new('RGB',(832,1984),'#eee8dc');dr=ImageDraw.Draw(sheet)
 for row,d in enumerate('NESW'):
  for col,kind in enumerate(['pair','closedRun']):
   x=8+col*456;y=8+row*616;box=(x+16,y+128,x+432,y+608);crop=raw.crop(box);sheet.paste(crop,(col*416,row*496+16));dr.text((col*416+2,row*496+2),f'{mode} {kind} {d}128 p.5 finalCSS',fill='black');mapping.append({'source':f'captures/consumer/{mode}-128-both-dpr1.png','crop':list(box),'output':f'captures/{mode}-128-css-controls.png','position':[col*416,row*496+16],'scale':1})
 sheet.save(R/f'captures/{mode}-128-css-controls.png')
 for kind in ['pair','closedRun']:
  for dpr in [1,2]:
   raw=Image.open(R/f'captures/consumer/{mode}-32-{kind}-dpr{dpr}.png');raw=raw.crop((0,0,488*dpr,1928*dpr))
   if dpr==2:raw=raw.resize((488,1928),Image.Resampling.BOX)
   raw.save(R/f'captures/{mode}-32-{kind}-dpr{dpr}-css.png')
(R/'measurements/independent-image-comparison.json').write_text(json.dumps(metrics,indent=2)+'\n');(R/'measurements/control-crop-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
print(json.dumps({'singleReplay':metrics['singleReplay'],'nativeFamilyReplay':metrics['nativeFamilyReplay'],'seams':metrics['seams'],'crossModeRaw':metrics['crossModeRaw']},indent=2))
