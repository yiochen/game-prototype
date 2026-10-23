import json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parents[1];C=B/'candidates/round-03'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
v=json.loads((C/'validation.json').read_text());v['nativeReopenAudit']='candidates/round-03/native-audit.json';v['geometry']['weldedInsideTurn']=True;v['geometry']['topologyInterpretation']='Each continuous main surface has only the two source terminal boundary loops: panel288 (=2x144); each timber bead/cap24 (=2x12); blue26 (=2x13). Zero-area faces 0. Separate exact original source cut closures remain intentionally camera-ray surfaces.'
assert all(p['zeroAreaFaces']==0 for p in v['geometry']['topology'])
v['roundSequence']={'round-01':'Initial native reconstruction; collapsed inner-turn crown produced a small fold. Retained as diagnostic.','round-02':'Removed inner-turn fold with constant construction coordinate on the sharp inside miter.','round-03':'Welded coincident inside-turn vertices into continuous native topology; actual final candidate. Earlier rounds were not independently reviewed.'}
(C/'validation.json').write_text(json.dumps(v,indent=2))
rig=json.loads((C/'native-rig.json').read_text());rig['originalGroundRootObject']=rig['groundRootObject'];rig['groundRootObject']='wall-outer-corner__root';rig['status']='native-static-candidate';rig['refinement']={'round':'round-03','staticFrames':1,'fps':12,'loop':False,'nativeModel':True};(C/'native-rig.json').write_text(json.dumps(rig,indent=2))
asset=json.loads((C/'native-assetRecord.json').read_text());asset['refinement']={'round':'round-03','family':'restaurant-wall-wood-blue-v2','familySettings':'inputs/family-settings.json','sourceArtStylePreservedAsHistoricalMetadata':True,'actualStyleAndCapture':'candidates/round-03/validation.json'};(C/'native-assetRecord.json').write_text(json.dumps(asset,indent=2))
cam=json.loads((C/'native-camera.json').read_text());cam['refinement']={'actualStyleAndCapture':'candidates/round-03/validation.json','sourceArtStylePreservedAsHistoricalMetadata':True};(C/'native-camera.json').write_text(json.dumps(cam,indent=2))
delivery=json.loads((B/'delivery.json').read_text());delivery['projectSHA256']=sha(B/delivery['project']);delivery['recipeSHA256']=sha(B/delivery['recipe']);delivery['supportingRecipes']+=['source/audit-native.py','source/finalize-delivery.py']
for name,p in [('native-reopen-audit',C/'native-audit.json'),('source-geometry-inspection',B/'source/source-inspection.json'),('native-camera',C/'native-camera.json'),('native-assetRecord',C/'native-assetRecord.json'),('native-rig',C/'native-rig.json')]:
 delivery['resources'].append({'name':name,'path':str(p.relative_to(B)),'sha256':sha(p)})
for name in ('native-joins','sprite-joins'):
 for p in sorted((C/name).glob('*.png')):delivery['resources'].append({'name':name+'-'+p.stem,'path':str(p.relative_to(B)),'sha256':sha(p)})
for p in delivery['supportingRecipes']:
 delivery['resources'].append({'name':'recipe-'+Path(p).stem,'path':p,'sha256':sha(B/p)})
(B/'delivery.json').write_text(json.dumps(delivery,indent=2))
print(json.dumps({'projectSHA256':delivery['projectSHA256'],'capture':v['capture']['calibration'],'profilesPass':all(p['passed']for p in v['geometry']['boundaryChecks']),'profileMaxError':max(p['maxDistanceToSourceProfile']for p in v['geometry']['boundaryChecks']),'resources':len(delivery['resources']),'previews':len(delivery['previews'])},indent=2))

