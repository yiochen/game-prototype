from pathlib import Path
import subprocess,json,hashlib,os,datetime
P=Path(__file__).resolve().parent;O=P.parent.parent;RUN=O.parent.parent;T=RUN/'tools';ROOT=RUN.parents[3];PY='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3';HELPER=Path('/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();review=O/'reviews/round-02.json';packet=O/'candidates/round-02/packet.json';reviewsha=sha(review);packetsha=sha(packet);env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');commands=[['integrity',PY,str(HELPER),'verify','--packet',str(packet),'--review',str(review)],['direction',PY,str(T/'audit_directions.py'),'wreck-corner','--round','round-02'],['acceptance',PY,str(T/'acceptance_contract.py'),'wreck-corner','--round','round-02']];records=[]
for name,*args in commands:
 script=Path(args[1]);before=sha(script);frozen=P/'resources/gates'/script.name;assert before==sha(frozen)
 r=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True);after=sha(script);records.append({'name':name,'command':args,'exitCode':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'unchangedHelperSHA256':before,'helperUnchanged':before==after});print(name,r.returncode,r.stdout.strip());assert r.returncode==0 and before==after
assert sha(review)==reviewsha and sha(packet)==packetsha
result={'pathBase':'object-root','candidatePacketSHA256':packetsha,'review':{'path':'reviews/round-02.json','sha256':reviewsha},'allPassed':True,'gates':records,'GitOrProductionActions':False}
(P/'gate-results.json').write_text(json.dumps(result,indent=2)+'\n')
manifest=P/'independent-evidence-manifest.json';m=json.loads(manifest.read_text())
for rec in m['files']:assert sha(O/rec['path'])==rec['sha256'],rec['path']
assert m['candidatePacketSHA256']==packetsha
r=json.loads(review.read_text());assert r['supplementalEvidence']['sha256']==sha(manifest)
files=[f for f in P.rglob('*')if f.is_file()and f.name!='postseal.json']+[review]
assert all(f.stat().st_size<100_000_000 for f in files);assert not any('__pycache__'in str(f)or f.suffix=='.pyc'for f in files)
post={'asset':'wreck-corner','round':'round-02','verdict':'approve','pathBase':'object-root','candidatePacketSHA256':packetsha,'review':{'path':'reviews/round-02.json','sha256':reviewsha},'supplementalEvidenceManifest':{'path':manifest.relative_to(O).as_posix(),'sha256':sha(manifest)},'gateResults':{'path':'reviews/round-02-independent-v1/gate-results.json','sha256':sha(P/'gate-results.json')},'allSupplementalManifestMembersVerified':len(m['files']),'allGatesPassed':True,'files':[{'path':f.relative_to(O).as_posix(),'sha256':sha(f)}for f in sorted(files)],'fileCount':len(files),'maxFileBytes':max(f.stat().st_size for f in files),'acyclic':'Evidence manifest excludes review/gate/postseal. Review binds evidence manifest; gates bind immutable review+packet; this final postseal binds all completed evidence/review/gate bytes and excludes itself.','scope':'Exact candidate approval only; no family/Git/production/publish/Godot/device approval.'}
(P/'postseal.json').write_text(json.dumps(post,indent=2)+'\n');print('POSTSEAL',sha(P/'postseal.json'),'REVIEW',reviewsha,'GATES',sha(P/'gate-results.json'))
