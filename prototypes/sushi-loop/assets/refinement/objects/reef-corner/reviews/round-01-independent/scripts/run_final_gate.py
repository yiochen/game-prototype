from pathlib import Path
import json,hashlib,subprocess,os
p=Path(__file__).resolve().parents[1];obj=p.parents[1];repo=Path.cwd();tool=repo/'prototypes/sushi-loop/assets/refinement/tools/acceptance_contract.py';review=obj/'reviews/round-01.json';manifest=p/'supplemental-manifest.json'
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
assert sha(tool)==sha(p/'resources/acceptance_contract.py')
cmd=['/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3',str(tool),'reef-corner','--round','round-01']
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');r=subprocess.run(cmd,cwd=repo,env=env,text=True,capture_output=True)
gate={'command':cmd,'acceptanceContractSHA256':sha(tool),'candidatePacketSHA256':sha(obj/'candidates/round-01/packet.json'),'reviewSHA256':sha(review),'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'passed':r.returncode==0}
(p/'final-gate.json').write_text(json.dumps(gate,indent=2)+'\n');assert r.returncode==0,gate
m=json.loads(manifest.read_text());bad=[x['path'] for x in m['files'] if sha((obj/x['path']).resolve())!=x['sha256']];assert not bad,bad
seal={'schemaVersion':1,'asset':'reef-corner','round':1,'verdict':'approve','candidatePacketSHA256':sha(obj/'candidates/round-01/packet.json'),'reviewPath':'reviews/round-01.json','reviewSHA256':sha(review),'supplementalManifestPath':'reviews/round-01-independent/supplemental-manifest.json','supplementalManifestSHA256':sha(manifest),'gatePath':'reviews/round-01-independent/final-gate.json','gateSHA256':sha(p/'final-gate.json'),'unchangedAcceptanceContractSHA256':sha(tool),'gatePassed':True,'verifiedSupplementalFiles':len(m['files']),'acyclic':'supplemental evidence→manifest→review→gate→postseal; no upstream file contains downstream hashes','scope':'Exact reef-corner round01 independent visual/native approval; no family/production/Godot/publish permission inferred','status':'SEALED; STOP'}
(p/'postreview-seal.json').write_text(json.dumps(seal,indent=2)+'\n');print(json.dumps({**seal,'postreviewSealSHA256':sha(p/'postreview-seal.json')},indent=2))
