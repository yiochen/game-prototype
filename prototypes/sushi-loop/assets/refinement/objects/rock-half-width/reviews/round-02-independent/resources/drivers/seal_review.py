from pathlib import Path
import json,hashlib,sys,subprocess
B=Path(__file__).resolve().parents[2];obj=B.parents[1];repo=obj.parents[5];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();M=B/'supplemental-manifest.json';R=obj/'reviews/round-02.json';S=B/'seal.json';G=B/'gate-result.json'
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def verify():
 m=json.loads(M.read_text());r=json.loads(R.read_text());s=json.loads(S.read_text());assert sha(M)==r['supplementalEvidence']['sha256']==s['manifestSHA256'];assert sha(R)==s['reviewSHA256'];assert sha(G)==s['gateResultSHA256'];assert sha(B/'gate.log')==s['gateLogSHA256'];assert sha(obj/'candidates/round-02/packet.json')==m['candidatePacketSHA256']==r['candidatePacketSHA256'];
 for f in m['files']:
  p=obj/f['path'];assert sha(p)==f['sha256'],f['path'];assert p.stat().st_size<100000000;assert p.suffix not in ['.pyc','.pyo']
 return {'allHashesMatch':True,'supplementalFiles':len(m['files']),'reviewSHA256':sha(R),'manifestSHA256':sha(M),'sealSHA256':sha(S),'gateExitCode':json.loads(G.read_text())['exitCode'],'verdict':r['verdict'],'binding':'Acyclic manifest(resources) -> review -> gate -> seal; postseal verifier points to these without reverse references.'}
if '--verify' in sys.argv:print(json.dumps(verify()));raise SystemExit
assert not S.exists();gate=repo/'prototypes/sushi-loop/assets/refinement/tools/acceptance_contract.py';assert sha(gate)==sha(B/'resources/instructions/acceptance_contract.py')
cmd=[sys.executable,str(gate),'rock-half-width','--round','round-02'];p=subprocess.run(cmd,cwd=repo,capture_output=True,text=True);(B/'gate.log').write_text(p.stdout+p.stderr);write(G,{'command':cmd,'cwd':str(repo),'gateSourceSHA256':sha(gate),'candidatePacketSHA256':sha(obj/'candidates/round-02/packet.json'),'reviewSHA256':sha(R),'supplementalManifestSHA256':sha(M),'exitCode':p.returncode,'expectedResult':'Rejected because verdict is revise and blockers remain. This is not an approval or weakened-gate pass.','stdout':p.stdout,'stderr':p.stderr})
assert p.returncode!=0 and json.loads(R.read_text())['verdict']=='revise'
write(S,{'candidatePacketSHA256':sha(obj/'candidates/round-02/packet.json'),'pathBase':'object root','manifestPath':str(M.relative_to(obj)),'manifestSHA256':sha(M),'reviewPath':str(R.relative_to(obj)),'reviewSHA256':sha(R),'gateResultPath':str(G.relative_to(obj)),'gateResultSHA256':sha(G),'gateLogSHA256':sha(B/'gate.log'),'verdict':'revise','state':'Immutable review and evidence; stop for root relay to the same fresh editor. No production/Git action.'})
v=verify();write(B/'postseal-verification.json',v);print(json.dumps(v))
