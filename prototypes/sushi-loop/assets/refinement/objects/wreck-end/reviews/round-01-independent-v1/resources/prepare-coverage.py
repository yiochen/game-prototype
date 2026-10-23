from pathlib import Path
from PIL import Image
import json,hashlib
R=Path(__file__).resolve().parent;E=R.parent;OBJ=E.parent.parent;C=OBJ/'candidates/round-01';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();p=json.loads((R/'packet.json').read_text());coverage=[]
for name in dict.fromkeys([x['path'] for x in p['previews'].values()]):
 path=C/name;im=Image.open(path).convert('RGBA');rec={'candidatePath':name,'sha256':sha(path),'frame':list(im.size),'method':'direct original full resolution' if im.height<=1408 else 'lossless fullpixel tiles with no omitted source pixels','tiles':[]}
 if im.height>1408:
  out=E/'coverage-tiles'/name.replace('/','--');out.parent.mkdir(parents=True,exist_ok=True)
  for n,y in enumerate(range(0,im.height,1200)):
   box=[0,y,im.width,min(y+1200,im.height)];dst=out.with_name(out.stem+'--'+str(n)+'.png');tile=im.crop(box);assert tile.tobytes()==im.crop(box).tobytes();tile.save(dst);rec['tiles'].append({'path':str(dst.relative_to(OBJ)),'box':box,'sha256':sha(dst)})
 coverage.append(rec)
raw=list((C/'consumer').glob('*-independent.png'))+list((C/'consumer').glob('*-native-control.png'));groups={}
for f in sorted(raw):groups.setdefault(sha(f),[]).append(str(f.relative_to(C)))
rawCoverage=[{'sha256':h,'directRepresentative':names[0],'exactByteAliases':names,'frame':list(Image.open(C/names[0]).size)} for h,names in groups.items()]
(E/'visual-coverage-plan.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'pathBase':'object','declaredPreviews':coverage,'rawNativeConsumerExactAliases':rawCoverage,'directHeroPaths':[x['path'] for x in p['candidateRenders'].values()],'otherDirectNative':['connected-native/'+d+'.png' for d in 'NESW'],'warning':'Plan records generated files and exact hashes, not inspection; inspected tile paths must be recorded truthfully after view_image.'},indent=2)+'\n')
print('tiles',sum(len(r['tiles']) for r in coverage),'raw unique',len(rawCoverage))
for rec in rawCoverage:print(rec['directRepresentative'])
