from pathlib import Path
import json,subprocess,hashlib,os
H=Path(__file__).resolve().parent;O=H.parent.parent;ROOT=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype');PY=Path('/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3');out=H/'gates';out.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
packet=O/'candidates/round-01/packet.json';review=O/'reviews/round-01.json'
commands=[('candidate-packet',Path('/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py'),['verify','--packet',str(packet),'--review',str(review)]),('directions',ROOT/'prototypes/sushi-loop/assets/refinement/tools/audit_directions.py',['portal-entry','--round','round-01']),('acceptance',ROOT/'prototypes/sushi-loop/assets/refinement/tools/acceptance_contract.py',['portal-entry','--round','round-01'])]
report={'asset':'portal-entry','round':'round-01','candidatePacketSHA256':sha(packet),'reviewSHA256':sha(review),'supplementalManifestSHA256':sha(H/'supplemental-evidence.json'),'commands':[]}
for name,helper,args in commands:
 assert sha(helper)==sha(H/'resources/gates'/helper.name)
 cmd=[str(PY),str(helper),*args];result=subprocess.run(cmd,cwd=ROOT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True);stdout=out/f'{name}.stdout.txt';stderr=out/f'{name}.stderr.txt';stdout.write_text(result.stdout);stderr.write_text(result.stderr)
 report['commands'].append({'name':name,'argv':cmd,'workingDirectory':str(ROOT),'helper':{'path':str(helper),'sha256':sha(helper),'frozenCopy':str((H/'resources/gates'/helper.name).relative_to(O))},'exitCode':result.returncode,'stdout':{'path':str(stdout.relative_to(O)),'sha256':sha(stdout)},'stderr':{'path':str(stderr.relative_to(O)),'sha256':sha(stderr)}})
 print(name,'exit',result.returncode,result.stdout.strip(),result.stderr.strip())
report['allExitZero']=all(r['exitCode']==0 for r in report['commands']);(H/'gates.json').write_text(json.dumps(report,indent=2)+'\n')
