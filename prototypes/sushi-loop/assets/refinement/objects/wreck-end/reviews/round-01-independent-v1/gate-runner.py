from pathlib import Path
import subprocess,sys,os,json,hashlib
E=Path(__file__).resolve().parent;OBJ=E.parent.parent;WT=next(p for p in OBJ.parents if (p/'prototypes.json').is_file());R=E/'resources';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();G=E/'gates';G.mkdir(exist_ok=True)
helper=Path('/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py');audit=WT/'prototypes/sushi-loop/assets/refinement/tools/audit_directions.py';accept=WT/'prototypes/sushi-loop/assets/refinement/tools/acceptance_contract.py'
for src,copy in [(helper,R/'candidate_packet.py'),(audit,R/'audit_directions.py'),(accept,R/'acceptance_contract.py')]:assert sha(src)==sha(copy)
commands=[('integrity',[sys.executable,str(helper),'verify','--packet',str(OBJ/'candidates/round-01/packet.json'),'--review',str(OBJ/'reviews/round-01.json')]),('directions',[sys.executable,str(audit),'wreck-end','--round','round-01']),('acceptance',[sys.executable,str(accept),'wreck-end','--round','round-01'])]
results=[]
for name,cmd in commands:
 run=subprocess.run(cmd,cwd=WT,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},text=True,capture_output=True);path=G/(name+'.log');path.write_text(run.stdout+run.stderr);results.append({'name':name,'command':cmd,'exitCode':run.returncode,'log':str(path.relative_to(OBJ)),'logSHA256':sha(path)});print(name,run.returncode,run.stdout[-700:],run.stderr[-300:])
(G/'results.json').write_text(json.dumps({'candidatePacketSHA256':sha(OBJ/'candidates/round-01/packet.json'),'reviewSHA256':sha(OBJ/'reviews/round-01.json'),'unchangedHelpers':{'candidate_packet.py':sha(helper),'audit_directions.py':sha(audit),'acceptance_contract.py':sha(accept)},'results':results,'allPassed':all(r['exitCode']==0 for r in results)},indent=2)+'\n')
