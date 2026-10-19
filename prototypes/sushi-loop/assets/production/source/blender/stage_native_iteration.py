"""Copy immutable native iteration evidence only; never touch the sprite manifest."""
from pathlib import Path
import json,hashlib,shutil,datetime,os

BASE=Path('/private/tmp/sushi33-production')
REPO=Path('/Users/yiouchen/.codex/worktrees/sushi-loop-33-art-catalog/game-prototype')
DEST=REPO/'prototypes/sushi-loop/assets/production/source'
MODELS=DEST/'blender'
NATIVE=BASE/'export/source'

def sha(path):
 digest=hashlib.sha256()
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
 return digest.hexdigest()

def atomic_copy(source,destination):
 destination=Path(destination);destination.parent.mkdir(parents=True,exist_ok=True)
 temporary=destination.with_name(destination.name+'.native-stage-tmp')
 shutil.copy2(source,temporary);os.replace(temporary,destination)

def preserve(path):
 digest=sha(path);version=MODELS/'revisions'/digest[:16]/path.name
 version.parent.mkdir(parents=True,exist_ok=True)
 if not version.exists():atomic_copy(path,version)
 if sha(version)!=digest:raise ValueError('Immutable revision mismatch: '+str(version))
 return digest,str(version.relative_to(DEST))

MODELS.mkdir(parents=True,exist_ok=True)
# Preserve the already-published authoring scripts before replacing current copies.
for path in sorted(MODELS.glob('*.py')):preserve(path)
for path in sorted(BASE.glob('*.py')):
 if path.name in ['stage_native_iteration.py','repair_revision_links.py'] or '-before-' in path.name:continue
 preserve(path)
 atomic_copy(path,MODELS/path.name)

blend=NATIVE/'sushi-loop-world-library.blend';export=NATIVE/'sushi-loop-world-library.export.json'
report=json.loads(export.read_text())
if sha(blend)!=report['sha256']:raise ValueError('Native blend differs from native export report')
for path in [blend,export]:
 preserve(path);atomic_copy(path,MODELS/path.name)

records=DEST/'native-records';records.mkdir(parents=True,exist_ok=True)
index={'version':1,'status':'native-models-and-actions-baked-capture-and-user-review-pending',
 'capturedAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'editableProject':'blender/sushi-loop-world-library.blend',
 'nativeExportReport':'blender/sushi-loop-world-library.export.json',
 'sourceBlendSHA256':report['sha256'],'assetIds':report['assetIds'],
 'records':{},'bakedSourceHashAvailability':{},
 'scope':'Native model/action provenance only. No raw frames, runtime sheets, manifest changes or final visual grade.'}
required_sources={}
for aid in report['assetIds']:
 source=NATIVE/aid;target=records/aid;target.mkdir(parents=True,exist_ok=True);index['records'][aid]={}
 for name in ['asset.json','camera.json','rig.json']:
  path=source/name
  data=json.loads(path.read_text())
  atomic_copy(path,target/name)
  index['records'][aid][name]={'path':str((target/name).relative_to(DEST)),'sha256':sha(target/name)}
  if name=='rig.json':
   for filename,digest in data.get('sourceFiles',{}).items():required_sources[(filename,digest)]=True
for filename,digest in sorted(required_sources):
 candidates=list((MODELS/'revisions').glob(digest[:16]+'/'+filename))
 index['bakedSourceHashAvailability'][filename+'@'+digest]={'status':'retained' if candidates and sha(candidates[0])==digest else 'hash-recorded-source-version-not-located',
 'path':str(candidates[0].relative_to(DEST)) if candidates else None}
(records/'index.json').write_text(json.dumps(index,indent=2)+'\n')
atomic_copy(BASE/'native-coverage-comparison.json',records/'native-coverage-comparison.json')
print(json.dumps({'nativeAssets':len(index['records']),'recordFiles':sum(len(v) for v in index['records'].values()),'blendBytes':blend.stat().st_size,'blendSHA256':report['sha256'],'unlocatedBakedSourceVersions':[key for key,value in index['bakedSourceHashAvailability'].items() if value['status']!='retained'],'index':str(records/'index.json')},indent=2))
