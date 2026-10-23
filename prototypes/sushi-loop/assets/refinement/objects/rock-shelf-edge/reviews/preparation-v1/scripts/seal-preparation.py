from pathlib import Path
import json,hashlib,sys
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parent.parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inputs=json.loads((BASE/'input-manifest.json').read_text())
assert len({i['path'] for i in inputs})==len(inputs)==34
for i in inputs:
 assert sha(Path(i['source']))==i['sha256']
 assert sha(BASE/'resources'/i['path'])==i['sha256']
comp=json.loads((BASE/'captures/historical/comparison.json').read_text())
assert all(v['exactPngByteMatch'] and v['pixelsDifferent']==0 for v in comp['results'].values())
assert len(comp['results'])==4
assert not list(BASE.rglob('__pycache__'))
paths=sorted([p for p in BASE.rglob('*') if p.is_file() and p.name not in {'hash-manifest.json','seal.json'}]+[BASE.parent/'initial.json',BASE.parent/'criteria.json'])
assert all(p.stat().st_size<100000000 for p in paths)
(BASE/'logs/seal.log').write_text('Preparation preflight: 34 distinct retained input hashes verified against original current paths. All4 historical replay PNG bytes exact. No bytecode directories or files >=100MB. No candidate approval.\n')
paths=sorted([p for p in BASE.rglob('*') if p.is_file() and p.name not in {'hash-manifest.json','seal.json'}]+[BASE.parent/'initial.json',BASE.parent/'criteria.json'])
rows=[{'path':str(p.relative_to(BASE)) if p.is_relative_to(BASE) else '../'+p.name,'bytes':p.stat().st_size,'sha256':sha(p)} for p in paths]
manifest={'schema':'preparation-evidence-hash-manifest-v1','asset':'rock-shelf-edge','status':'sealed-preparation-only-root-freeze-pending','files':rows}
(BASE/'hash-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
seal={'asset':'rock-shelf-edge','scope':'bounded independent source-feasibility and contract proposal only','status':'sealed; stop for root freeze before fresh editor','candidateApproval':False,'familyApproval':False,'manifestSHA256':sha(BASE/'hash-manifest.json'),'fileCount':len(rows),'totalBytes':sum(i['bytes'] for i in rows),'initialSHA256':sha(BASE.parent/'initial.json'),'criteriaSHA256':sha(BASE.parent/'criteria.json'),'contractSHA256':sha(BASE/'proposed-root-contract.json'),'compatibilitySHA256':sha(BASE/'compatibility.json'),'assemblyPlanSHA256':sha(BASE/'assembly-evidence-plan.json'),'canonicalBlendSHA256':sha(BASE/'resources/canonical/round-03.blend'),'canonicalPacketSHA256':sha(BASE/'resources/canonical/packet.json'),'historicalReplayAll4Exact':True,'originalInputHashesStillUnchanged':True,'candidateStage':'pending root freeze and fresh editor'}
(BASE/'seal.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps({'sealSHA256':sha(BASE/'seal.json'),**seal},indent=2))
