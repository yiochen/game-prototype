from pathlib import Path
import json,hashlib,subprocess,os
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent.parent;RUN=OBJ.parent.parent;REPO=RUN.parents[3]
PY='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
REVIEW=OBJ/'reviews/round-01.json';MANIFEST=HERE/'supplemental-manifest.json';PACKET=OBJ/'candidates/round-01/packet.json'
assert not (HERE/'postseal.json').exists(),'Do not overwrite a final gate seal'
expectedReview='5fdffad9ac20abb61802e920e358c49041b462f22793e744f05faaae27a432aa';expectedManifest='501ccb27fb2cd83d41f0ebec6e0c6c0d60f1042c37a09dbd30e593de3e0bc759';expectedPacket='20f3fe4297877ecc50affda4574c2ade50482e7068bd9d457fbfb3e6ff2bc54c'
assert sha(REVIEW)==expectedReview and sha(MANIFEST)==expectedManifest and sha(PACKET)==expectedPacket
helpers=[(Path('/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py'),HERE/'resources/instructions/refine-3d-model/scripts/candidate_packet.py'),(RUN/'tools/audit_directions.py',HERE/'resources/instructions/tools/audit_directions.py'),(RUN/'tools/acceptance_contract.py',HERE/'resources/instructions/tools/acceptance_contract.py')]
helperRecords=[]
for src,frozen in helpers:
    assert sha(src)==sha(frozen),(src,'helper changed')
    helperRecords.append({'source':str(src),'frozenPath':str(frozen.relative_to(OBJ)),'sha256':sha(src)})
commands=[('candidate-packet-verify',[PY,str(helpers[0][0]),'verify','--packet',str(PACKET),'--review',str(REVIEW)]),('audit-directions',[PY,str(helpers[1][0]),'decor-background-rock','--round','round-01']),('acceptance-contract',[PY,str(helpers[2][0]),'decor-background-rock','--round','round-01'])]
gateDir=HERE/'gates';gateDir.mkdir(exist_ok=True);results=[];env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
for name,args in commands:
    done=subprocess.run(args,cwd=REPO,env=env,text=True,capture_output=True)
    stdout=gateDir/(name+'.stdout.txt');stderr=gateDir/(name+'.stderr.txt');stdout.write_text(done.stdout);stderr.write_text(done.stderr)
    results.append({'name':name,'command':args,'workdir':str(REPO),'returncode':done.returncode,'stdout':{'path':str(stdout.relative_to(OBJ)),'sha256':sha(stdout)},'stderr':{'path':str(stderr.relative_to(OBJ)),'sha256':sha(stderr)}})
    print(name,'RETURN_CODE',done.returncode,done.stdout.strip(),done.stderr.strip())
for r in helperRecords:assert sha(Path(r['source']))==r['sha256']
gateRecord={'asset':'decor-background-rock','round':'round-01','candidatePacketSHA256':expectedPacket,'review':{'path':str(REVIEW.relative_to(OBJ)),'sha256':expectedReview},'supplementalEvidence':{'path':str(MANIFEST.relative_to(OBJ)),'sha256':expectedManifest},'python':PY,'helpers':helperRecords,'results':results,'allPassed':all(r['returncode']==0 for r in results),'scope':'Unchanged exact approval binding, facing and acceptance validators; no helper/candidate/art mutation.'}
gates=HERE/'gates.json';gates.write_text(json.dumps(gateRecord,indent=2)+'\n')
members=load(MANIFEST)['files']
for rec in members:assert sha(OBJ/rec['path'])==rec['sha256'],rec['path']
assert sha(REVIEW)==expectedReview and sha(MANIFEST)==expectedManifest and sha(PACKET)==expectedPacket
assert sha(OBJ/'source/round-01.blend')=='f59fbb1aa5e6d45ea0dde0c916ab523d60bf63c748ccf650813072d4c46efd4d'
postseal={'asset':'decor-background-rock','round':'round-01','verdict':load(REVIEW)['verdict'],'candidatePacketSHA256':expectedPacket,'pathBase':'object root','review':{'path':str(REVIEW.relative_to(OBJ)),'sha256':sha(REVIEW)},'supplementalEvidence':{'path':str(MANIFEST.relative_to(OBJ)),'sha256':sha(MANIFEST),'verifiedMembers':len(members)},'gates':{'path':str(gates.relative_to(OBJ)),'sha256':sha(gates),'allPassed':gateRecord['allPassed']},'gateRunner':{'path':str(Path(__file__).resolve().relative_to(OBJ)),'sha256':sha(Path(__file__).resolve())},'gateOutputs':[r[k] for r in results for k in ['stdout','stderr']],'sourceSHA256':sha(OBJ/'source/round-01.blend'),'integrityAfterGates':True,'acyclic':'Review points to supplemental manifest; supplement covers pre-verdict evidence only. Gates bind review+supplement; this postseal binds all three. No reverse reference.','approvalScope':'This exact object/candidate only. No family/production/publishing/Git/Godot/device authorization.'}
post=HERE/'postseal.json';post.write_text(json.dumps(postseal,indent=2)+'\n')
for p in [Path(__file__),gates,post,*gateDir.iterdir()]:os.chmod(p,0o444)
print('GATES_SHA256',sha(gates));print('POSTSEAL_SHA256',sha(post));print('REVIEW_SHA256',sha(REVIEW));print('SUPPLEMENTAL_SHA256',sha(MANIFEST));print('ALL_PASSED',gateRecord['allPassed'])
assert gateRecord['allPassed'],'A failing gate is not approval handoff'
