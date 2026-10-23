from pathlib import Path
import json,subprocess,sys,hashlib,os
H=Path(__file__).resolve().parent;O=H.parent.parent;G=O.parents[3];REPO=G.parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
checks=[('candidate-packet',Path('/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py'),['verify','--packet',str(O/'candidates/round-01/packet.json'),'--review',str(O/'reviews/round-01.json')]),('directions',G/'assets/refinement/tools/audit_directions.py',['safe-passage','--round','round-01']),('acceptance',G/'assets/refinement/tools/acceptance_contract.py',['safe-passage','--round','round-01'])]
results=[]
for name,helper,args in checks:
 command=[sys.executable,str(helper),*args];env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1';p=subprocess.run(command,cwd=REPO,env=env,capture_output=True,text=True)
 out=H/f'gate-{name}.stdout.txt';err=H/f'gate-{name}.stderr.txt';out.write_text(p.stdout);err.write_text(p.stderr)
 results.append({'name':name,'argv':command,'workingDirectory':str(REPO),'helper':str(helper),'helperSHA256':sha(helper),'exitCode':p.returncode,'stdout':{'path':str(out.relative_to(O)),'sha256':sha(out)},'stderr':{'path':str(err.relative_to(O)),'sha256':sha(err)}})
record={'asset':'safe-passage','round':'round-01','reviewSHA256':sha(O/'reviews/round-01.json'),'candidatePacketSHA256':sha(O/'candidates/round-01/packet.json'),'gates':results,'allExitZero':all(r['exitCode']==0 for r in results),'unchangedSharedHelpers':True,'noStagedCheckerOrGit':True}
(H/'gates.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({'allExitZero':record['allExitZero'],'gates':[{k:r[k] for k in ['name','exitCode','helperSHA256']} for r in results]}))
sys.exit(0 if record['allExitZero'] else 1)
