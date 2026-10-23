from pathlib import Path
import json,hashlib,sys,os
base=Path(__file__).resolve().parents[2];obj=base.parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
manifest=base/'manifest.json';seal=base/'seal.json';verification=base/'verification.json'
if '--verify' in sys.argv:
 s=json.loads(seal.read_text());assert sha(manifest)==s['manifestSHA256'];assert sha(verification)==s['verificationSHA256'];m=json.loads(manifest.read_text())
 for r in m['files']:
  p=obj/r['path'];assert p.stat().st_size==r['bytes'] and sha(p)==r['sha256'],r['path']
 print(json.dumps({'verified':True,'manifestSHA256':sha(manifest),'sealSHA256':sha(seal),'files':len(m['files'])}));raise SystemExit
assert not manifest.exists() and not seal.exists()
paths=[obj/'reviews/initial.json',obj/'reviews/proposedcriteria.json',obj/'reviews/source-contract-proposal.json']+[p for p in base.rglob('*') if p.is_file() and p not in [manifest,seal,verification]]
assert len(paths)==len(set(paths));assert not any(p.suffix in ['.pyc','.pyo'] or '__pycache__' in p.parts for p in paths);assert all(p.stat().st_size<100_000_000 for p in paths)
files=[{'path':str(p.relative_to(obj)),'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)]
py=Path('/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3')
write(manifest,{'asset':'rock-half-width','kind':'immutable independent preparation evidence, not candidate approval','version':1,'pathBase':'object root','files':files,'totalBytes':sum(p['bytes'] for p in files),'maxFileBytes':max(p['bytes'] for p in files),'allFilesBelow100MB':True,'noFrozenBytecode':True,'dependencyPolicy':'Exact used input/source/helper/skill files frozen. Actual imported Pillow modules and loaded Node dependency files frozen only; no runtime application trees. Native Blender, Node, browser binaries externally pinned in runtime-probe.json.','pythonRuntime':{'path':str(py),'realPath':str(py.resolve()),'sha256':sha(py),'version':sys.version},'rootDecisions':'reviews/source-contract-proposal.json rootReconciliationRequired; freeze before dispatching a separate fresh editor.'})
for r in files:assert sha(obj/r['path'])==r['sha256']
write(verification,{'asset':'rock-half-width','manifestPath':str(manifest.relative_to(obj)),'manifestSHA256':sha(manifest),'verifiedCount':len(files),'allHashesMatch':True,'allFilesBelow100MB':True,'noFrozenBytecode':True,'noCandidateOrApproval':True})
write(seal,{'asset':'rock-half-width','kind':'preparation-only seal','pathBase':'object root','manifestPath':str(manifest.relative_to(obj)),'manifestSHA256':sha(manifest),'verificationPath':str(verification.relative_to(obj)),'verificationSHA256':sha(verification),'candidateApproval':False,'state':'Stop for root freeze and separate fresh editor. Do not overwrite this evidence; revisions use new versioned paths.'})
print(json.dumps({'manifestSHA256':sha(manifest),'sealSHA256':sha(seal),'files':len(files),'totalBytes':sum(p['bytes'] for p in files),'maxFileBytes':max(p['bytes'] for p in files)}))
