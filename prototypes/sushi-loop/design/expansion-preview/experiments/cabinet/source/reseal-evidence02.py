"""Reseal hash-identical native art following coordinator's brief-path metadata correction."""
import json,hashlib,subprocess,sys
from pathlib import Path
E=Path(__file__).resolve().parent.parent;oldpath=E/'candidates/round-01/packet.json';old=json.loads(oldpath.read_text());O=E/'candidates/evidence-02';O.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
resolve=lambda r:(oldpath.parent/r['path']).resolve()
art={**{'candidateProject':old['files']['candidateProject']},**{f'render:{k}':v for k,v in old['candidateRenders'].items()},**{f'preview:{k}':v for k,v in old['previews'].items()}}
assert all(sha(resolve(r))==r['sha256'] for r in art.values())
continuity={'submissionType':'evidence-only','previousPacket':str(oldpath),'previousPacketSHA256':sha(oldpath),'previousReview':str(E/'reviews/round-01.json'),'previousReviewSHA256':sha(E/'reviews/round-01.json'),'reason':'Coordinator corrected the brief style-reference relative path after round-01 was sealed. Capture, qualityCriteria and art unchanged.','oldBriefSHA256':old['files']['brief']['sha256'],'currentBriefSHA256':sha(E/'brief.json'),'unchangedArt':{k:{'path':str(resolve(v)),'sha256':v['sha256']} for k,v in art.items()},'artRerendered':False}
(E/'candidates/evidence-02/art-continuity.json').write_text(json.dumps(continuity,indent=2)+'\n')
cmd=[sys.executable,'/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py','create','--brief',str(E/'brief.json'),'--project',str(resolve(old['files']['candidateProject'])),'--validation',str(resolve(old['files']['nativeValidation'])),'--output',str(O/'packet.json')]
for key,record in old['candidateRenders'].items():cmd+=['--render',key+'='+str(resolve(record))]
for key,record in old['previews'].items():cmd+=['--preview',key+'='+str(resolve(record))]
for key,record in old['files'].items():
 if key.startswith('candidateResource:'):cmd+=['--resource',key.split(':',1)[1]+'='+str(resolve(record))]
cmd+=['--resource','art-continuity='+str(O/'art-continuity.json'),'--resource','evidence-reseal-recipe='+str(Path(__file__).resolve())]
subprocess.run(cmd,check=True)
new=json.loads((O/'packet.json').read_text());assert new['capture']==old['capture'] and new['qualityCriteria']==old['qualityCriteria'];assert new['files']['candidateProject']['sha256']==old['files']['candidateProject']['sha256'];assert all(new['candidateRenders'][k]['sha256']==v['sha256'] for k,v in old['candidateRenders'].items());assert all(new['previews'][k]['sha256']==v['sha256'] for k,v in old['previews'].items())
subprocess.run([sys.executable,'/Users/yiouchen/.codex/skills/refine-3d-model/scripts/candidate_packet.py','verify','--packet',str(O/'packet.json')],check=True)
print('EVIDENCE_ONLY_PACKET',str(O/'packet.json'),sha(O/'packet.json'))
