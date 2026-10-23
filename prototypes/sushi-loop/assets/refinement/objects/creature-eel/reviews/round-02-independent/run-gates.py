from pathlib import Path
import subprocess,json,hashlib,sys,os
J=Path(__file__).resolve().parent;O=J.parent.parent;W=O.parents[5];C=O/'candidates/round-02';review=O/'reviews/round-02.json';supp=J/'supplemental-evidence.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def desc(p):return {'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size}
env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1');D=J/'gates';D.mkdir(exist_ok=True)
checks=[('candidate_packet',Path('/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py'),['verify','--packet',str(C/'packet.json'),'--review',str(review)]),('audit_directions',W/'prototypes/sushi-loop/assets/refinement/tools/audit_directions.py',['creature-eel','--round','round-02']),('acceptance_contract',W/'prototypes/sushi-loop/assets/refinement/tools/acceptance_contract.py',['creature-eel','--round','round-02'])]
rows=[]
for name,helper,args in checks:
 copied=J/'resources'/helper.name;prior=O/'reviews/round-01-independent/resources'/helper.name;assert sha(helper)==sha(copied)==sha(prior)
 cmd=[sys.executable,str(helper),*args];p=subprocess.run(cmd,cwd=W,env=env,text=True,capture_output=True);out=D/(name+'.stdout.txt');err=D/(name+'.stderr.txt');out.write_text(p.stdout);err.write_text(p.stderr);rows.append({'name':name,'command':cmd,'workingDirectory':str(W),'helperSource':str(helper),'helperSHA256':sha(helper),'helperPrivateCopy':desc(copied),'unchangedFromRound01PrivateHelper':desc(prior),'exitCode':p.returncode,'stdout':desc(out),'stderr':desc(err)});print(name,p.returncode,p.stdout.strip(),p.stderr.strip(),flush=True)
gates={'candidatePacketSHA256':sha(C/'packet.json'),'review':desc(review),'supplementalEvidence':desc(supp),'checks':rows,'allPassed':all(r['exitCode']==0 for r in rows),'limits':'Compact audit_directions gate samples one measured capture per facing. Own exact round01 all528phase native evaluation/fullpixel visual/currentconsumer playback proof is reused after independent round02 equivalence verification. No new render or playback claim.'};gp=J/'gates.json';gp.write_text(json.dumps(gates,indent=2)+'\n')
s=json.loads(supp.read_text());failures=[]
for r in s['files']:
 p=O/r['path']
 if not p.is_file() or sha(p)!=r['sha256']:failures.append(r['path'])
for r in s['externalIdenticalAliases']:
 if sha(O/r['path'])!=r['sha256'] or sha(O/r['privateEquivalent'])!=r['sha256']:failures.append(r['path'])
assert not failures,failures
post={'asset':'creature-eel','round':'round-02','candidatePacketSHA256':sha(C/'packet.json'),'candidateProjectSHA256':sha(O/'source/round-01.blend'),'verdict':json.loads(review.read_text())['verdict'],'supplementalEvidence':desc(supp),'review':desc(review),'gates':desc(gp),'gateOutputs':[r[k] for r in rows for k in ['stdout','stderr']],'allGatesPassed':gates['allPassed'],'supplementalFileCount':len(s['files']),'allSupplementalHashesStillExact':True,'externalIdenticalAliasesStillExact':True,'priorRound01ReviewAndProofStillExact':True,'helpersStillExact':True,'acyclicOrder':['supplemental-evidence.json','../round-02.json','gates.json','postseal.json'],'authority':'Exact metadata-corrected round02 eel BODY candidate verdict only; original01 approval remains immutable. No promotion, publishing, source/art/effect modification or broader approval.'};pp=J/'postseal.json';pp.write_text(json.dumps(post,indent=2)+'\n');assert gates['allPassed'];print(json.dumps({'review':desc(review),'supplemental':desc(supp),'gates':desc(gp),'postseal':desc(pp)},indent=2))
