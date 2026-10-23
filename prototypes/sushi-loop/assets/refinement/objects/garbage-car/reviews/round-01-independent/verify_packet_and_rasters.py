from pathlib import Path
import json,hashlib,struct,subprocess
from PIL import Image,ImageChops,ImageDraw
import numpy as np
P=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/garbage-car')
C=P/'candidates/round-01';O=P/'reviews/round-01-independent';O.mkdir(exist_ok=True,parents=True)
packet=json.loads((C/'packet.json').read_text());delivery=json.loads((C/'delivery.snapshot.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
checks=[]
for key,rec in packet['files'].items():
 p=(C/rec['path']).resolve();got=sha(p) if p.is_file() else None;checks.append({'key':key,'path':str(p),'expected':rec['sha256'],'actual':got,'pass':got==rec['sha256']})
frames=[];raw={(x['clip'],x['direction'],x['index']):x for x in delivery['rawFrames']}
for atlas in delivery['atlases']:
 a=Image.open(P/atlas['path']).convert('RGBA');cell=[]
 for index,rect in enumerate(atlas['rects']):
  x,y,w,h=rect;r=raw[atlas['clip'],atlas['direction'],index];native=Image.open(P/r['path']).convert('RGBA');cut=a.crop((x,y,x+w,y+h));arr=np.asarray(native);mask=arr[:,:,3]>127
  cell.append({'index':index,'frame':r['path'],'RGBAEqual':cut.tobytes()==native.tobytes(),'nativeSHA256':sha(P/r['path']),'alphaBBox':native.getchannel('A').getbbox(),'alphaSum':int(arr[:,:,3].astype(np.uint64).sum()),'opaquePixelCount':int(mask.sum()),'RGBMedianOpaque':np.median(arr[:,:,:3][mask],axis=0).tolist(),'opaqueBlackFraction':float((arr[:,:,:3][mask].max(axis=1)<15).mean()),'edgeAlphaNonzero':bool(arr[0,:,3].any() or arr[-1,:,3].any() or arr[:,0,3].any() or arr[:,-1,3].any())})
 frames.append({'atlas':atlas['path'],'size':a.size,'declaredSize':atlas['size'],'columns':atlas['columns'],'rows':atlas['rows'],'cells':cell})
closure=[]
for d in ['N','E','S','W']:
 x=np.asarray(Image.open(C/f'frames/highlighted-{d}/000.png').convert('RGBA')).astype(float);y=np.asarray(Image.open(C/f'diagnostics/highlighted-{d}-key13.png').convert('RGBA')).astype(float);m=(x[:,:,3]>127)&(y[:,:,3]>127)
 closure.append({'direction':d,'meanAbsRGBInside':float(abs(x[:,:,:3]-y[:,:,:3])[m].mean()),'maxAbsRGBInside':float(abs(x[:,:,:3]-y[:,:,:3])[m].max()),'alphaMAE':float(abs(x[:,:,3]-y[:,:,3]).mean()),'sameOpaqueMask':bool(((x[:,:,3]>127)==(y[:,:,3]>127)).all())})
previews=[]
for key,rec in packet['previews'].items():
 p=C/rec['path'];im=None
 if p.suffix.lower()=='.png':
  im=Image.open(p);previews.append({'key':key,'path':str(p.relative_to(P)),'sha256':sha(p),'size':im.size,'frames':getattr(im,'n_frames',1)})
# Own verified native-frame contact sheets; fixed complete source canvas scaled uniformly.
sheetRecords=[]
for clip in ['idle','highlighted','clearance']:
 for d in ['N','E','S','W']:
  fs=[x for x in delivery['rawFrames'] if x['clip']==clip and x['direction']==d];cols=6 if len(fs)>1 else 1;sheet=Image.new('RGB',(cols*288,((len(fs)+cols-1)//cols)*440),'#808080');draw=ImageDraw.Draw(sheet)
  for i,x in enumerate(fs):
   im=Image.open(P/x['path']).convert('RGBA').resize((288,416),Image.Resampling.LANCZOS);pos=(i%cols*288,i//cols*440+24);sheet.paste(im,pos,im);draw.text((pos[0]+4,pos[1]-20),f'{clip}-{d} index{i:02}',fill='white')
  path=O/f'native-all-{clip}-{d}.png';sheet.save(path);sheetRecords.append({'path':str(path.relative_to(P)),'inputs':[x['path'] for x in fs],'sha256':sha(path),'method':'Uniform full native frame resized to288x416 and alpha composited onto gray; no crop/fitting.'})
result={'packetSHA256':sha(C/'packet.json'),'briefSHA256':sha(P/'brief.json'),'projectSHA256':sha(P/'source/round-01.blend'),'validationSHA256':sha(C/'validation.json'),'deliverySHA256':sha(C/'delivery.snapshot.json'),'fileChecks':checks,'fileFailureCount':sum(not x['pass'] for x in checks),'atlasChecks':frames,'atlasPixelFailureCount':sum(not x['RGBAEqual'] for f in frames for x in f['cells']),'frameCount':len(raw),'closureRasterChecks':closure,'previewInventory':previews,'independentContactSheets':sheetRecords}
(O/'packet-raster-audit.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k not in ['fileChecks','atlasChecks','previewInventory','independentContactSheets']},indent=2))
