"""Post-verdict gates and acyclic integrity seal; no index or production work."""
from pathlib import Path
import json,hashlib,subprocess,os
P=Path(__file__).resolve().parent;O=P.parents[1];REPO=Path.cwd();C=O/'candidates/round-01';python='/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):Path(p).write_text(json.dumps(d,indent=2)+'\n')
review=O/'reviews/round-01.json';manifest=P/'supplemental-evidence.json';data=json.loads(manifest.read_text());receipt=json.loads(review.read_text());assert receipt['supplementalEvidence']['sha256']==sha(manifest)
assert not (P/'gates.json').exists() and not (P/'post-review-seal.json').exists()
reviewSHA=sha(review);manifestSHA=sha(manifest);packetSHA=sha(C/'packet.json');assert packetSHA==receipt['candidatePacketSHA256']==data['candidatePacketSHA256']
helpers={
'candidate_packet':Path('/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py'),
'audit_directions':REPO/'prototypes/sushi-loop/assets/refinement/tools/audit_directions.py',
'acceptance_contract':REPO/'prototypes/sushi-loop/assets/refinement/tools/acceptance_contract.py'}
for name,p in helpers.items():assert sha(p)==sha(P/'resources/checkers'/(name+'.py'))
commands=[('candidate_packet',[python,str(helpers['candidate_packet']),'verify','--packet',str(C/'packet.json'),'--review',str(review)]),('audit_directions',[python,str(helpers['audit_directions']),'portal-rim','--round','round-01']),('acceptance_contract',[python,str(helpers['acceptance_contract']),'portal-rim','--round','round-01'])]
results=[]
for name,argv in commands:
 r=subprocess.run(argv,cwd=REPO,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},capture_output=True,text=True)
 stdout=P/'logs'/f'gate-{name}.stdout.txt';stderr=P/'logs'/f'gate-{name}.stderr.txt';stdout.write_text(r.stdout);stderr.write_text(r.stderr)
 results.append({'name':name,'argv':argv,'cwd':str(REPO),'exitCode':r.returncode,'currentHelperSHA256':sha(helpers[name]),'retainedHelperCopy':{'path':str((P/'resources/checkers'/(name+'.py')).relative_to(O)),'sha256':sha(P/'resources/checkers'/(name+'.py'))},'stdout':{'path':str(stdout.relative_to(O)),'sha256':sha(stdout),'bytes':stdout.stat().st_size},'stderr':{'path':str(stderr.relative_to(O)),'sha256':sha(stderr),'bytes':stderr.stat().st_size}})
 print(name,'EXIT',r.returncode,r.stdout.strip(),r.stderr.strip(),flush=True)
write(P/'gates.json',{'asset':'portal-rim','round':'round-01','reviewSHA256':reviewSHA,'candidatePacketSHA256':packetSHA,'supplementSHA256':manifestSHA,'gates':results,'allPassed':all(r['exitCode']==0 for r in results),'scope':'Only read-only integrity/review-binding, direction and independent acceptance gates executed. No staged/index checker, Git, promotion or deployment command.'})
changed=[r['path'] for r in data['files'] if sha((O/r['path']).resolve())!=r['sha256']]
assert not changed,changed;assert sha(review)==reviewSHA and sha(manifest)==manifestSHA and sha(C/'packet.json')==packetSHA
assert all(sha(p)==sha(P/'resources/checkers'/(n+'.py')) for n,p in helpers.items())
newfiles=[P/'run_gates.py',P/'gates.json',*[P/'logs'/f'gate-{n}.{stream}.txt' for n in helpers for stream in ['stdout','stderr']]]
seal={'asset':'portal-rim','round':'round-01','verdict':receipt['verdict'],'status':'exact-candidate-approved-and-all-three-unchanged-gates-passed' if all(r['exitCode']==0 for r in results) else 'gate-failure-requires-root-attention','candidatePacketSHA256':packetSHA,'candidateSourceSHA256':sha(O/'source/round-01.blend'),'review':{'path':str(review.relative_to(O)),'sha256':reviewSHA},'supplement':{'path':str(manifest.relative_to(O)),'sha256':manifestSHA,'verifiedMembers':len(data['files']),'changedMembers':changed},'postReviewFiles':[{'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size} for p in newfiles],'acyclicBinding':'supplement -> review -> gates -> post-review-seal; no back references by content hash','scopeNotes':['The helper-identities.json field executedOriginal records the canonical helper origin path. verify_staged_object.py was inspected read-only for supplemental manifest schema and was never executed. Only the three gate helpers listed here were executed.','All candidate, target, source, frozen criteria, brief, media and helper bytes remain unchanged. Approval is candidate-specific; no production/family/Godot/device/publishing approval.']}
write(P/'post-review-seal.json',seal)
print(json.dumps({'reviewSHA256':reviewSHA,'supplementSHA256':manifestSHA,'postReviewSealSHA256':sha(P/'post-review-seal.json'),'gatesPassed':all(r['exitCode']==0 for r in results),'supplementVerifiedMembers':len(data['files'])},indent=2))
raise SystemExit(0 if all(r['exitCode']==0 for r in results) else 1)
