from pathlib import Path
from PIL import Image
import json,hashlib,os
P=Path(__file__).resolve().parents[2];OBJ=P.parent.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
write=lambda p,x:Path(p).write_text(json.dumps(x,indent=2)+'\n')
a=Image.open(P/'resources/object/inputs/original.png').convert('RGBA');b=Image.open(P/'baseline/historical-published2-S.png').convert('RGBA');high=[(x,y) for x,y in zip(a.get_flattened_data(),b.get_flattened_data()) if max(abs(x[i]-y[i]) for i in [1,2])>=200]
write(P/'historical-edge-residual.json',{'highGBDeltaThreshold':200,'pixelCount':len(high),'maximumEitherAlpha':max(max(x[3],y[3]) for x,y in high),'interpretation':'Large green/blue residuals confined to5 edge pixels with alpha<=1; no correction.'})
j=json.loads((P/'preparation-summary.json').read_text());j['inspectedNative'].append('reviews/preparation-v1/native-use-phone32.png');j['nativeImageCoverage']['native-use-phone32.png']={'inputs':['baseline-v2/original-canonical-rig/'+d+'.png' for d in 'NESW']+['baseline-v2/mixed-native/'+d+'.png' for d in 'NESW'],'transformation':'Whole complete frame native2=>cell32 nearest visualization, no fit/crop/nudge/recolor/repair; lightgraydark backgrounds'};write(P/'preparation-summary.json',j)
# Report exact required byte provenance, file bounds and parseability before signing.
files=[p for p in OBJ.joinpath('reviews').rglob('*') if p.is_file() and p.name not in ['manifest.json','seal.json','final-verification.json']]
for p in files:
 assert p.stat().st_size<100_000_000,(p,p.stat().st_size)
 assert '__pycache__' not in p.parts and p.suffix!='.pyc',p
 if p.suffix=='.json':json.loads(p.read_text())
manifest={'asset':'wreck-end','scope':'fresh independent judge preparation only','pathBase':'object','baseDescription':'wreck-end object root; all paths reviews/...','sourceSHA256':'b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6','blenderExecutable':'/opt/homebrew/bin/blender','blenderVersion':'5.2.2 LTS d13f752e3b9c','pythonExecutable':'/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3','actualConsumerVersion':'153.0.8010.12 in both prescribed modes','files':[{'path':str(p.relative_to(OBJ)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)],'status':'STOP for ROOT reconciliation/freeze BEFORE fresh editor construction; no candidate/art/family approval'}
write(P/'manifest.json',manifest)
write(P/'seal.json',{'asset':'wreck-end','scope':'preparation only, no approval','pathBase':'object','manifest':{'path':str((P/'manifest.json').relative_to(OBJ)),'sha256':sha(P/'manifest.json')},'fileCount':len(files),'totalBytes':sum(p.stat().st_size for p in files),'maxFileBytes':max(p.stat().st_size for p in files),'proposals':{n:{'path':'reviews/'+n,'sha256':sha(OBJ/'reviews'/n)} for n in ['initial.json','proposedcriteria.json','source-contract-proposal.json']},'rootFreezePending':True})
# Mark exact sealed review bytes readonly. This is local evidence hygiene, no Git action.
for p in files+[P/'manifest.json',P/'seal.json']:p.chmod(p.stat().st_mode & ~0o222)
print(json.dumps(json.loads((P/'seal.json').read_text()),indent=2))
