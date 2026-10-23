from pathlib import Path
import json,shutil,hashlib
B=Path(__file__).resolve().parents[2];C=B/'candidates/round-02';R=B/'reviews/round-02-independent';R.mkdir(exist_ok=True);S=R/'resources';S.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=json.loads((C/'packet.json').read_text());verified={};aliases={};bad=[]
for group in ['files','candidateRenders','previews']:
 for k,v in p[group].items():
  f=(C/v['path']).resolve()
  if f not in verified:verified[f]=sha(f) if f.is_file() else None
  if verified[f]!=v['sha256']:bad.append([group,k,v['path']])
  aliases.setdefault(v['sha256'],[]).append({'group':group,'key':k,'path':v['path']})
rows=[]
def copy(f,d):
 f=Path(f);d=S/d;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,d);rows.append({'source':str(f),'path':str(d.relative_to(R)),'sha256':sha(d),'bytes':d.stat().st_size})
for f,d in [(C/'packet.json','packet.json'),(C/'delivery.snapshot.json','delivery.snapshot.json'),(B/'source/round-02/project.blend','project.blend'),(B/'inputs/frozen-main-v1/project.blend','main.blend'),(B/'inputs/source-camera.json','source-camera.json'),(B/'inputs/root-native-contract.json','native-contract.json'),(B/'brief.json','brief.json'),(B/'inputs/frozen-main-v1/body-freeze.json','body-freeze.json'),(B/'reviews/proposedcriteria.json','criteria.json'),(B/'reviews/initial.json','initial.json')]:copy(f,d)
for f in (B/'source/round-02').glob('*'):
 if f.is_file() and f.suffix in ['.py','.mjs','.js','.html','.json']:copy(f,Path('source')/f.name)
for f in (B/'source/round-02/resources/browser').glob('*'):
 if f.is_file() and f.suffix in ['.js','.jsx','.css','.json']:copy(f,Path('browser')/f.name)
W=B.parents[5]
# Snapshot relevant instructions and unchanged acceptance tool.
for f,d in [(W/'AGENTS.md','instructions/AGENTS.md'),(B.parents[3]/'AGENTS.md','instructions/sushi-AGENTS.md'),(B.parents[1]/'tools/acceptance_contract.py','tooling/acceptance_contract.py'),(B.parents[1]/'preparation/REVIEW-COVERAGE.txt','instructions/REVIEW-COVERAGE.txt')]:
 if f.exists():copy(f,d)
SK=Path('/Users/yiouchen/.codex/skills/refine-3d-model')
for f in SK.rglob('*'):
 if f.is_file() and '__pycache__' not in str(f):copy(f,Path('skill')/f.relative_to(SK))
(R/'input-snapshots.json').write_text(json.dumps({'pathBase':'reviews/round-02-independent/','files':rows},indent=2)+'\n')
(R/'packet-verification.json').write_text(json.dumps({'packetSHA256':sha(C/'packet.json'),'uniqueFiles':len(verified),'records':sum(len(p[g]) for g in ['files','candidateRenders','previews']),'bad':bad,'verifiedSHA256Aliases':{k:v for k,v in aliases.items() if len(v)>1}},indent=2)+'\n')
print('VERIFY',len(verified),'bad',bad,'snapshot bytes',sum(x['bytes'] for x in rows))
