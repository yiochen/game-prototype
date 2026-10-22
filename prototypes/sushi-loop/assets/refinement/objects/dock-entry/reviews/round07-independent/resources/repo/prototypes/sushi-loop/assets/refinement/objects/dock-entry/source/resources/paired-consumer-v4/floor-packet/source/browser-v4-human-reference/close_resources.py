from pathlib import Path
import json,hashlib
B=Path(__file__).resolve().parents[2];O=B/'candidates/round-05';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();ev=json.loads((O/'browser-v4-human-reference/consumer-evidence.json').read_text());assert not ev['errors']and ev['allActualIntermediateSmoothingDisabled']and ev['actualFramesVerified'];paths=[]
for folder in[B/'source/resources/browser-v3-native-sampling',B/'source/browser-v4-human-reference',O/'browser-v4-human-reference']:
 paths += [p for p in folder.rglob('*')if p.is_file()and'__pycache__'not in p.parts]
paths += list((B/'candidates/round-04/atlases').glob('*.png'))
paths += list((O/'native-human-context').glob('current-b176-*.png'))
paths += [O/'shared-world-pose-plan.json',B/'brief-v4-human-reference.json',B/'inputs/shared-world-pose-v1/root-adoption.json']
resources=[{'path':str(p.relative_to(B)),'sha256':sha(p),'bytes':p.stat().st_size}for p in sorted(set(paths))];assert all(r['bytes']<100000000 for r in resources)
for rec in ev['records']+ev['rawCurrentCanvas']:
 p=B/rec['path'];assert sha(p)==rec['sha256']
manifest={'schema':'exact-shared-browser-evidence-closure-v4','scope':'Exact current consumer evidence for adopted nine representative static source poses. No continuous locomotion or door traversal assertion. Primary35degree published character, current published b176 companions, unchanged04floor/06entry art, explicit actual supportedBy. Native55degree reference images separate.','sharedPlanSHA256':ev['sharedWorldPlanSHA256'],'frozenFloorBriefSHA256':ev['frozenBriefSHA256'],'browserEvidence':'candidates/round-05/browser-v4-human-reference/consumer-evidence.json','screenshots':len(ev['records']),'rawActualCanvases':len(ev['rawCurrentCanvas']),'resources':resources,'totalBytes':sum(r['bytes']for r in resources),'allResourceHashesVerified':True,'allIndividualResourcesBelow100MB':True};p=O/'shared-browser-resource-manifest-v4.json';assert not p.exists();p.write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'path':str(p),'sha256':sha(p),'resources':len(resources),'bytes':manifest['totalBytes'],'evidenceSHA256':sha(O/'browser-v4-human-reference/consumer-evidence.json')},indent=2))
