"""Normalize delivery metadata only after finalize-delivery.py; never changes art/manifests."""
from pathlib import Path
from PIL import Image
import json,hashlib
BASE=Path(__file__).resolve().parent.parent
DP=BASE/'delivery.json';MP=BASE/'candidates/round-04/resources.json';D=['N','E','S','W']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record(path,**fields):
 p=BASE/path;value={**fields,'path':path,'sha256':sha(p)}
 if p.suffix.lower()=='.png':
  with Image.open(p) as im:value['size']=list(im.size)
 return value
original=json.loads(DP.read_text());manifest=json.loads(MP.read_text())
# Snapshot all already-present candidate/source art, inputs and manifests for unchanged-byte proof.
protected={str(p.relative_to(BASE)):sha(p) for folder in ['inputs','candidates','source'] for p in (BASE/folder).rglob('*') if p.is_file() and p.name!='delivery.snapshot.json'}
delivery=dict(original);delivery['round']='round-04';delivery['projectSHA256']=sha(BASE/delivery['project'])
delivery['heroes']=[record(f'candidates/round-04/heroes/{d}.png',direction=d) for d in D]
delivery['rawFrames']=[record(f'candidates/round-04/frames/static-{d}.png',clip='static',direction=d,index=0) for d in D]
delivery['nativeCaptures']=[record(f'candidates/round-04/raw/static-{d}/000.png',clip='static',direction=d,index=0) for d in D]
delivery['atlases']=[record(f'candidates/round-04/atlases/static-{d}.png',clip='static',direction=d,columns=1,rows=1,rects=[[0,0,384,1024]],frameOrder=[0],fps=12,loop=False,static=True) for d in D]
previewPaths=original['previews'] if isinstance(original['previews'],dict) else {r['id']:r['path'] for r in original['previews']}
delivery['previews']=[record(path,id=name,kind='independent-runtime-alpha-composition' if name=='repeated' else 'registered-native-four-facing-sheet') for name,path in previewPaths.items()]
delivery['resourceManifest']='candidates/round-04/resources.json'
resourcePaths=[delivery['resourceManifest']]+[r['path'] for r in manifest['resources'].values()]
resourcePaths += list(delivery['nativeRecords'].values())+list(delivery['guides'].values())+['candidates/round-04/replay-native-audit.json','candidates/round-04/image-validation.json','source/initial-observations.json','source/criteria-acknowledgement.json','source/normalize-delivery.py']
delivery['resources']=[dict(record(path,name=path.replace('/','__')),bytes=(BASE/path).stat().st_size) for path in dict.fromkeys(resourcePaths)]
delivery['supportingRecipes']=['source/finalize-delivery.py','source/normalize-delivery.py','source/publish-previews.py','source/verify-native.py']
delivery['deliveryMetadata']={'schema':'Frame/atlas/hero/preview/resource record lists compatible with shared sealer/promoter','publicationFrames':'rawFrames are four published384x1024 static index0 records; nativeCaptures hold768x2048 frames','resourceManifestUnchangedSHA256':sha(MP),'closedReplayEvidence':'candidates/round-04/replay-validation.json','normalizationScript':'source/normalize-delivery.py'}
# Verify source closure hashes and exact replay evidence without rerendering or altering artifacts.
for r in manifest['resources'].values():assert sha(BASE/r['path'])==r['sha256'],r['path']
replay=json.loads((BASE/'candidates/round-04/replay-validation.json').read_text());assert replay['allRGBAEqual'] and all(r['rgbaEqual'] and r['maximumChannelDifference']==0 for r in replay['directions'].values())
assert len(delivery['rawFrames'])==len(delivery['nativeCaptures'])==len(delivery['atlases'])==4
assert all(r['size']==[384,1024] for r in delivery['rawFrames']+delivery['atlases'])
assert all(r['size']==[768,2048] for r in delivery['nativeCaptures'])
assert all(not Path(r['path']).is_absolute() and '..' not in Path(r['path']).parts for r in delivery['resources'])
DP.write_text(json.dumps(delivery,indent=2)+'\n')
assert all(sha(BASE/p)==digest for p,digest in protected.items()),'Protected file changed'
print(json.dumps({'delivery':'delivery.json','rawFrames':len(delivery['rawFrames']),'nativeCaptures':len(delivery['nativeCaptures']),'atlases':len(delivery['atlases']),'resources':len(delivery['resources']),'resourceManifestSHA256':sha(MP),'protectedFilesByteUnchanged':len(protected),'existingClosedReplayExactRGBA':True},indent=2))
