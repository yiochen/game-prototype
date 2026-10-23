from pathlib import Path
import json,hashlib,subprocess,sys
R=Path(__file__).resolve().parent;Q=R.parent;O=Q.parent.parent;W=O.parents[6];C=O/'candidates/round-01';tool=O/'../../tools/acceptance_contract.py'
# Derive worktree from exact existing toolpath, not a guessed parent count.
W=tool.resolve().parents[5]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def rec(p):return {'path':str(p.relative_to(O)),'sha256':sha(p),'bytes':p.stat().st_size}
def save(p,j):p.write_text(json.dumps(j,indent=2)+'\n')
review=O/'reviews/round-01.json';manifest=Q/'supplemental-manifest.json';reviewsha=sha(review);j=json.loads(review.read_text());m=json.loads(manifest.read_text());assert j['verdict']=='approve' and j['blockers']==[] and j['independentReview'] is True
assert j['supplementalEvidence']['sha256']==sha(manifest);assert m['candidatePacketSHA256']==sha(C/'packet.json')==j['candidatePacketSHA256']
for r in m['files']:assert sha(O/r['path'])==r['sha256'],r['path']
assert sha(tool)==sha(R/'acceptance_contract.py')=='e229a0706dad88f3e45a192811fa741ac8ad13ca6c1af6d1ce88c1e10063f44d'
command=['python3',str(tool.resolve()),'decor-foreground-coral','--round','round-01'];result=subprocess.run(command,cwd=str(W),capture_output=True,text=True)
stdout=Q/'final-gate.stdout.txt';stdout.write_text(result.stdout+result.stderr)
assert sha(review)==reviewsha,'Final review changed duringgate'
gate={'candidatePacketSHA256':j['candidatePacketSHA256'],'reviewSHA256':reviewsha,'manifestSHA256':sha(manifest),'command':command,'cwd':str(W),'toolSHA256':sha(tool),'frozenTool':rec(R/'acceptance_contract.py'),'returnCode':result.returncode,'stdout':rec(stdout),'stdoutText':result.stdout,'stderrText':result.stderr,'reviewUnchangedThroughGate':True};save(Q/'final-gate.json',gate)
if result.returncode:raise SystemExit('Acceptancegate failed; review/gate preserved withoutseal.')
packet=json.loads((C/'packet.json').read_text());checks=0
for group in ['files','candidateRenders','previews']:
 for r in packet[group].values():assert sha(C/r['path'])==r['sha256'];checks+=1
assert sha(O/'source/round01/round-01.blend')=='6a3359e2b0621b04f5247696369c10d57bb1fba3013f6e1bb9c867c0afc7bb73'
seal={'asset':'decor-foreground-coral','round':'round-01','status':'EXACT_CANDIDATE_INDEPENDENT_APPROVAL_SEALED','candidatePacketSHA256':sha(C/'packet.json'),'projectSHA256':sha(O/'source/round01/round-01.blend'),'review':rec(review),'supplementalEvidence':rec(manifest),'finalGate':rec(Q/'final-gate.json'),'finalGateStdout':rec(stdout),'gateDriver':rec(Path(__file__).resolve()),'allPacketResourceRecordsReverifiedAfterReview':checks,'reviewUnchangedAfterFinalGate':True,'scope':'This exactobject/candidateonly; noproduction/family/Godot/deviceapproval. STOP. No postreviewart/source mutations.'};save(Q/'post-review-seal.json',seal)
print(json.dumps({'review':rec(review),'manifest':rec(manifest),'gate':rec(Q/'final-gate.json'),'seal':rec(Q/'post-review-seal.json'),'acceptanceStdout':result.stdout,'packetRecordsReverified':checks},indent=2))
