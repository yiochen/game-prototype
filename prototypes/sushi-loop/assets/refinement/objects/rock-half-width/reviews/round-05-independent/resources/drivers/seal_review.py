from pathlib import Path
import json,hashlib,sys,subprocess
B=Path(__file__).resolve().parents[2];obj=B.parents[1];repo=obj.parents[5];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();M=B/'supplemental-manifest.json';R=obj/'reviews/round-05.json';S=B/'seal.json';G=B/'gate-result.json';P=obj/'candidates/round-05/packet.json'
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
def verify():
 m=json.loads(M.read_text());r=json.loads(R.read_text());s=json.loads(S.read_text());g=json.loads(G.read_text())
 assert sha(M)==r['supplementalEvidence']['sha256']==s['manifestSHA256'];assert sha(R)==s['reviewSHA256']==g['reviewSHA256'];assert sha(G)==s['gateResultSHA256'];assert sha(B/'gate.log')==s['gateLogSHA256'];assert sha(P)==m['candidatePacketSHA256']==r['candidatePacketSHA256']==s['candidatePacketSHA256']==g['candidatePacketSHA256']
 for f in m['files']:
  p=obj/f['path'];assert p.resolve().is_relative_to(obj.resolve());assert sha(p)==f['sha256'],f['path'];assert p.stat().st_size<100000000 and p.suffix not in ['.pyc','.pyo'] and '__pycache__' not in p.parts
 packet=json.loads(P.read_text());records=[v for k in ['files','candidateRenders','previews'] for v in packet[k].values()]
 for f in records:assert sha((P.parent/f['path']).resolve())==f['sha256'],f['path']
 assert sha((P.parent/packet['files']['candidateProject']['path']).resolve())==sha(B/'resources/candidate.blend')
 for check in g['postVerdictGates']:
  assert sha(Path(check['source']))==check['sourceSHA256']==sha(B/'resources/instructions'/Path(check['source']).name)
  if r['verdict']=='approve' or check['name']=='directions':assert check['exitCode']==0
  else:assert check['exitCode']!=0
 assert g['exitCode']==next(v['exitCode'] for v in g['postVerdictGates'] if v['name']=='acceptance')
 return {'allHashesMatch':True,'supplementalFiles':len(m['files']),'currentPacketRecordsVerified':len(records),'originalCandidateSourceUnchanged':True,'reviewSHA256':sha(R),'manifestSHA256':sha(M),'sealSHA256':sha(S),'gateExitCode':g['exitCode'],'postVerdictGateExitCodes':{v['name']:v['exitCode'] for v in g['postVerdictGates']},'verdict':r['verdict'],'binding':'Acyclic manifest(resources) -> review -> gates -> seal; postseal verifier references those without reverse pointers.'}
if '--verify' in sys.argv:print(json.dumps(verify()));raise SystemExit
assert not S.exists();review=json.loads(R.read_text());verdict=review['verdict'];checks=[];logs=[]
for name,source,args in [
 ('packet-with-review',Path('/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py'),['verify','--packet',str(P),'--review',str(R)]),
 ('directions',repo/'prototypes/sushi-loop/assets/refinement/tools/audit_directions.py',['rock-half-width','--round','round-05']),
 ('acceptance',repo/'prototypes/sushi-loop/assets/refinement/tools/acceptance_contract.py',['rock-half-width','--round','round-05'])]:
 assert sha(source)==sha(B/'resources/instructions'/source.name);cmd=[sys.executable,str(source)]+args;p=subprocess.run(cmd,cwd=repo,capture_output=True,text=True);checks.append({'name':name,'source':str(source),'sourceSHA256':sha(source),'command':cmd,'cwd':str(repo),'exitCode':p.returncode,'stdout':p.stdout,'stderr':p.stderr});logs.append(name+'\n'+p.stdout+p.stderr)
(B/'gate.log').write_text('\n'.join(logs));acceptance=next(v for v in checks if v['name']=='acceptance');write(G,{'candidatePacketSHA256':sha(P),'reviewSHA256':sha(R),'supplementalManifestSHA256':sha(M),'exitCode':acceptance['exitCode'],'postVerdictGates':checks,'expectedResult':'All three unchanged exact-review/integrity, measured-directions and acceptance gates must pass for approve. For revise/needs_evidence, retain actual independent-approval rejection and direction result.'})
for c in checks:
 assert (c['exitCode']==0) if verdict=='approve' or c['name']=='directions' else (c['exitCode']!=0),c
write(S,{'candidatePacketSHA256':sha(P),'pathBase':'object root','manifestPath':str(M.relative_to(obj)),'manifestSHA256':sha(M),'reviewPath':str(R.relative_to(obj)),'reviewSHA256':sha(R),'gateResultPath':str(G.relative_to(obj)),'gateResultSHA256':sha(G),'gateLogSHA256':sha(B/'gate.log'),'verdict':verdict,'state':'Immutable original independent review for this exact candidate only. Stop; no production, Git, promotion, family, publishing, Godot or device permission inferred.'})
v=verify();write(B/'postseal-verification.json',v);print(json.dumps(v))
