from pathlib import Path
import hashlib,json
P=Path(__file__).resolve().parents[1];O=P.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[p for p in sorted(P.rglob('*')) if p.is_file() and p.name not in ['hashmanifest.json','preparation-seal.json']]
files.extend([O/'reviews/initial.json',O/'reviews/criteria.json'])
for p in files:
 assert p.stat().st_size<100_000_000,(str(p),p.stat().st_size)
 assert '__pycache__' not in p.parts
records=[{'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size} for p in files]
m={'asset':'creature-fish','stage':'independent-judge-preparation-only','pathBase':'object-root (prototypes/sushi-loop/assets/refinement/objects/creature-fish)','files':records,'fileCount':len(records),'totalBytes':sum(r['bytes'] for r in records),'notApproval':True}
(P/'hashmanifest.json').write_text(json.dumps(m,indent=2)+'\n')
s={'asset':'creature-fish','stage':'preparation-only','status':'SEALED_AWAITING_ROOT_RECONCILIATION_AND_FREEZE','manifest':{'path':str((P/'hashmanifest.json').relative_to(O)),'sha256':sha(P/'hashmanifest.json')},'fileCount':len(records),'totalBytes':m['totalBytes'],'sourceUnchangedSHA256':sha(P/'resources/inputs/untouched.blend'),'notCandidateApproval':True,'pending':'Root resolves design envelope/nominalheight and freezes criteria before fresh editor; no editor construction or publishing authorized by this seal.'}
(P/'preparation-seal.json').write_text(json.dumps(s,indent=2)+'\n')
for r in records:assert sha(O/r['path'])==r['sha256']
print(json.dumps(s,indent=2))
