import pathlib,json,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageChops
b=pathlib.Path('prototypes/sushi-loop/assets/refinement/objects/chef-rowan').resolve();c=b/'candidates/round-01';r=b/'reviews/round01-independent';packet=json.loads((c/'packet.json').read_text());checks=[]
for section in ['files','candidateRenders','previews']:
 for k,v in packet[section].items():
  p=(c/v['path']).resolve();checks.append({'path':v['path'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'matches':hashlib.sha256(p.read_bytes()).hexdigest()==v['sha256']})
parity=[]
for clip,facing,ix in [('idle','S',0),('hold','N',0),('load','S',5)]:
 a=Image.open(r/f'reopened-{clip}-{facing}-{ix:02}.png').convert('RGBA');z=Image.open(c/f'frames/{clip}-{facing}-{ix:02}.png').convert('RGBA');delta=np.abs(np.array(a).astype(int)-np.array(z).astype(int));parity.append({'frame':f'frames/{clip}-{facing}-{ix:02}.png','sameRGBA':bool(np.array_equal(np.array(a),np.array(z))),'maximumChannelError':int(delta.max()),'changedPixels':int(np.any(delta,axis=-1).sum())})
allmatches=[];alpha=[]
for facing in ['N','E','S','W']:
 sheet=Image.new('RGB',(6*128,8*224),(146,150,155));d=ImageDraw.Draw(sheet)
 for ci,clip in enumerate(['idle','work','hold','load']):
  a=Image.open(c/f'atlases/{clip}-{facing}.png').convert('RGBA')
  for ix in range(12):
   im=Image.open(c/f'frames/{clip}-{facing}-{ix:02}.png').convert('RGBA');rect=((ix%6)*384,(ix//6)*640,(ix%6+1)*384,(ix//6+1)*640);p=a.crop(rect);allmatches.append(np.array_equal(np.array(im),np.array(p)));alpha.append(im.getbbox())
   # Uniform logical scale then same fixed diagnostic crop for every frame.
   im=im.resize((192,320),Image.Resampling.LANCZOS).crop((32,64,160,272));x=(ix%6)*128;y=(ci*2+ix//6)*224;sheet.paste(im,(x,y+16),im);d.text((x+2,y+2),f'{clip} {facing} {ix:02}',fill=(25,30,35))
 sheet.save(r/f'all48-{facing}-logical-crops.png')
old=json.loads((b/'reviews/source_native_audit.json').read_text());new=json.loads((r/'source_native_audit.json').read_text());dif=[]
for o,n in zip(old['frames'],new['frames']):
 for k in ['rootLocation','rootScale','rootYaw','handsWorld','foodRootWorld','foodPlaneWorldMatrix','foodVisible','knifeVisible','feetBoneWorld','headBoneWorld','knifeBounds']:
  if o[k]!=n[k]:dif.append({'clip':o['clip'],'facing':o['facing'],'index':o['index'],'key':k})
clear=[]
for o,n in zip(old['frames'],new['frames']):
 for i in range(3):
  if n['bodyBounds']['min'][i]<o['bodyBounds']['min'][i]-1e-6 or n['bodyBounds']['max'][i]>o['bodyBounds']['max'][i]+1e-6:clear.append({'clip':o['clip'],'facing':o['facing'],'index':o['index'],'axis':i})
summary={'packetSHA256':hashlib.sha256((c/'packet.json').read_bytes()).hexdigest(),'fileHashCount':len(checks),'hashFailures':[x for x in checks if not x['matches']],'rerenderParity':parity,'atlasFramesExact':all(allmatches),'atlasFrameCount':len(allmatches),'nativeContactsAndStateDifferences':dif,'restSkeletonEqual':old['rest']['bones']==new['rest']['bones'],'rootScaleEqual':old['rest']['rootScale']==new['rest']['rootScale'],'phaseSpecificEnvelopeViolations':clear,'alphaBoundsWithinFrame':all(x[0]>0 and x[1]>0 and x[2]<384 and x[3]<640 for x in alpha)}
(r/'independent-checks.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary,indent=2))
