from pathlib import Path
import json,hashlib,datetime
P=Path(__file__).resolve().parents[1];O=P.parent.parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
exclude={P/'manifest.json',P/'seal.json'}
files=sorted([f for f in P.rglob('*')if f.is_file()and f not in exclude]+[O/'reviews/initial.json',O/'reviews/initial-before-depsgraph-correction.json',O/'reviews/initial-before-source-link-correction.json',O/'reviews/initial-before-source-visibility-correction.json',O/'reviews/proposedcriteria.json',O/'reviews/source-contract-proposal.json'])
assert not any('__pycache__'in str(f)or f.suffix=='.pyc'for f in files)
assert all(f.stat().st_size<100_000_000 for f in files)
assert len(files)==len(set(files))
manifest={'asset':'wreck-corner','stage':'preparation-only-for-root-freeze','pathBase':'object-root','createdAtUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'independentInitial':'reviews/initial.json','proposedCriteria':'reviews/proposedcriteria.json','sourceContractProposal':'reviews/source-contract-proposal.json','evidencePlan':'reviews/preparation-v1/evidence-plan.json','rawAuthoringBudget':'reviews/preparation-v1/raw-authoring-envelope.json','finiteSupport':'reviews/preparation-v1/finite-support-outline.json','canonicalApprovalBinding':'reviews/preparation-v1/canonical-approval-binding.json','files':[{'path':f.relative_to(O).as_posix(),'sha256':sha(f),'bytes':f.stat().st_size}for f in files],'fileCount':len(files),'totalBytes':sum(f.stat().st_size for f in files),'candidateApproval':False,'familyApproval':False,'remaining':'Root reconciles/freezes own RAW13point envelope and finite10point support, canonical properN fields/rig/capture, visible criteria and bounded L evidence plan before fresh editor construction.'}
(P/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
seal={'asset':'wreck-corner','stage':'preparation-only','pathBase':'object-root','manifest':{'path':'reviews/preparation-v1/manifest.json','sha256':sha(P/'manifest.json')},'fileCount':len(files),'totalBytes':manifest['totalBytes'],'maxFileBytes':max(f.stat().st_size for f in files),'candidateApproval':False,'rootFreezeRequired':True,'verify':'Hash every manifest.files record from object-root and manifest bytes against this seal. Canonical individual approvals are technical evidence only; no corner/family approval.'}
(P/'seal.json').write_text(json.dumps(seal,indent=2)+'\n')
for f in manifest['files']:assert sha(O/f['path'])==f['sha256']
print(json.dumps(seal,indent=2));print('sealSHA256',sha(P/'seal.json'))
