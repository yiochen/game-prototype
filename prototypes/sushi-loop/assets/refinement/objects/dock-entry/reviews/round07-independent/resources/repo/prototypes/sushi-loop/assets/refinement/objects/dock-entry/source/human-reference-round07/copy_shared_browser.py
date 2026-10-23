"""Exact immutable companion browser closure copy; preserves Floor-relative hierarchy."""
from pathlib import Path
import json,hashlib,shutil
B=Path(__file__).resolve().parents[2];peer=B.parent/'dock-floor';manifest=peer/'candidates/round-05/shared-browser-resource-manifest-v4.json';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();assert sha(manifest)=='6ee1de95dfbc7112666d12c219b0024e67cd7a8f3f40019a10e828af12bd1e55';m=json.loads(manifest.read_text());D=B/'source/resources/paired-consumer-v4/floor-packet';D.mkdir(parents=True,exist_ok=True);rows=[]
for r in m['resources']:
 p=peer/r['path'];assert sha(p)==r['sha256'];q=D/r['path'];q.parent.mkdir(parents=True,exist_ok=True)
 if q.exists():assert sha(q)==r['sha256']
 else:shutil.copyfile(p,q)
 assert sha(q)==r['sha256'];rows.append({'originalPath':r['path'],'copy':str(q.relative_to(B)),'sha256':r['sha256'],'bytes':r['bytes']})
q=D/'candidates/round-05/shared-browser-resource-manifest-v4.json';shutil.copyfile(manifest,q)
binding={'method':'Exact immutable375file current consumer closure copied after companion declared ready. Original Floor-relative hierarchy retained, copied original JSON/scripts unedited. Adapter maps original paths to own retained paths; no sibling live dependency. No source project resave.','sharedPlanSHA256':m['sharedPlanSHA256'],'companionClosureManifest':{'path':str(q.relative_to(B)),'sha256':sha(q)},'files':rows,'browserEvidence':{'path':str((D/m['browserEvidence']).relative_to(B)),'sha256':sha(D/m['browserEvidence'])},'screenshots':m['screenshots'],'rawActualCanvases':m['rawActualCanvases'],'totalBytes':m['totalBytes'],'sourceFacingPlan':'inputs/shared-world-pose-v1/plan.json','frozenEntryBriefSHA256':sha(B/'brief-v4-human-reference.json'),'sourceMappingsRemainImmutable':True}
(B/'candidates/round-07/shared-browser-binding.json').write_text(json.dumps(binding,indent=2));print('SHARED_BROWSER_COPIED',len(rows),m['totalBytes'])
