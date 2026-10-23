from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;O=P.parents[1];B=P.parent/'preparation-v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
base=json.loads((B/'hashmanifest.json').read_text())
for r in base['files']:assert sha(O/r['path'])==r['sha256'],r['path']
assert sha(B/'hashmanifest.json')=='dcb36f488aa3fd8af2322b020ac9b90b1b4771b6055fe551e71640a6818b6afe'
files=[p for p in sorted(P.rglob('*')) if p.is_file() and p.name not in ['hashmanifest.json','supplement-seal.json']]
for p in files:assert p.stat().st_size<100_000_000
records=[{'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size} for p in files]
deps=[B/'hashmanifest.json',B/'preparation-seal.json',B/'resources/inputs/untouched.blend',B/'resources/inputs/source-rig.json',B/'resources/inputs/source-assetRecord.json',B/'resources/native/native_actions.py']
m={'asset':'creature-fish','stage':'preparation-only-rig-supplement','pathBase':'object-root prototypes/sushi-loop/assets/refinement/objects/creature-fish','files':records,'dependencyReferences':[{'path':str(p.relative_to(O)),'sha256':sha(p)} for p in deps],'fileCount':len(records),'totalBytes':sum(r['bytes'] for r in records),'notCandidate':True}
(P/'hashmanifest.json').write_text(json.dumps(m,indent=2)+'\n')
s={'asset':'creature-fish','stage':'preparation-only-rig-supplement','status':'SEALED_AWAITING_ROOT_FREEZE','manifest':{'path':str((P/'hashmanifest.json').relative_to(O)),'sha256':sha(P/'hashmanifest.json')},'previousPreparationManifestSHA256':sha(B/'hashmanifest.json'),'previousPreparationUnchanged':True,'sourceUnchangedSHA256':sha(B/'resources/inputs/untouched.blend'),'notApproval':True,'fileCount':len(records),'totalBytes':m['totalBytes']}
(P/'supplement-seal.json').write_text(json.dumps(s,indent=2)+'\n')
for r in records:assert sha(O/r['path'])==r['sha256']
print(json.dumps(s,indent=2))
