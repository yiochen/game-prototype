"""Close current source/frame integrity; never modifies native projects or retained packets."""
from pathlib import Path
import json,hashlib
from PIL import Image
import numpy as np
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-06';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();read=lambda p:json.loads(Path(p).read_text())
old=read(B/'delivery.json');changed=[r['path'] for r in old['resources'].values() if not (B/r['path']).exists() or sha(B/r['path'])!=r['sha256']];assert not changed,changed
study=read(B/'candidates/alpha-filter-study/study-report.json');changedStudy=[r['path'] for r in study['resources'] if sha(B/r['path'])!=r['sha256']];assert not changedStudy
native=read(O/'native-validation.json');paired=read(O/'paired-native-validation.json');human=read(O/'approved-human-native-validation.json');records=[]
for phase in native['renders']+paired['renders']+human['renders']:
 p=B/phase['path'];assert sha(p)==phase['sha256'];im=Image.open(p).convert('RGBA');a=np.array(im.getchannel('A'));edges=int((a[0]>0).sum()+(a[-1]>0).sum()+(a[:,0]>0).sum()+(a[:,-1]>0).sum());assert edges==0,(p,edges);records.append({'path':phase['path'],'sha256':phase['sha256'],'size':list(im.size),'alphaBounds':im.getchannel('A').getbbox(),'nontransparentBorderPixels':edges})
paths={'entry':('source/round-06.blend','22bd2b05201567c22d9dabcf767a3daf0639342e5522c43900ff4b777f5f3b37'),'pairedFloor':('source/resources/paired-native-v3/dock-floor-round-04.blend','94b509984dc442547602f32feada987c5119e3b9031eb1bd65a6a07769880418'),'approvedHuman':('source/resources/approved-human-v3/customer-rosa-approved.blend','a6fe68fa07f3930c3d8e88ae6df992fefe447a9ef18935e322daf6f4bbc28253'),'ownOriginalCopy':('source/resources/original-library.blend','b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6')}
r={}
for key,(path,expected) in paths.items():
 p=B/path;actual=sha(p);assert actual==expected;r[key]={'path':path,'sha256':actual,'expected':expected,'bytes':p.stat().st_size}
for key in ['project','backup']:
 v=read(B/'candidates/round-05/source-integrity.json')[key];p=Path(v['path']);assert p.exists() and sha(p)==v['expected'];r[key]={**v,'sha256':sha(p)}
r.update({'oldDelivery':{'path':'delivery.json','sha256':sha(B/'delivery.json'),'resourceCount':len(old['resources']),'changedResources':changed},'scopedStudy':{'path':'candidates/alpha-filter-study/study-report.json','sha256':sha(B/'candidates/alpha-filter-study/study-report.json'),'resourceCount':len(study['resources']),'changedResources':changedStudy},'sourceHashesAfterAllCaptureStagesUnchanged':native['savedSourceUnchangedAfterCaptures'] and paired['sourceBytesUnchanged'] and human['sourceBytesUnchanged'] and human['approvedHumanSourceUnchanged']})
(O/'source-integrity.json').write_text(json.dumps(r,indent=2));(O/'native-frame-clipping.json').write_text(json.dumps({'method':'All current standalone4/nativepair-family40/approvedhuman36 native fullframes hash and RGBA border inspection. No crop/fitting.','records':records,'all80NoBorderClipping':len(records)==80 and all(x['nontransparentBorderPixels']==0 for x in records)},indent=2));print('NATIVE_CLOSURE',len(records),'old',len(old['resources']),'study',len(study['resources']),'unchanged')
