import json,hashlib,shutil
from pathlib import Path
P=Path(__file__).resolve().parents[1]; W=P.parents[7]; A=W/'prototypes/sushi-loop/assets'; O=P.parents[1]
def sha(x):return hashlib.sha256(x.read_bytes()).hexdigest()
files=[]
def copy(src,rel):
 dest=P/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dest);files.append({'source':str(src),'path':str(dest.relative_to(P)),'sha256':sha(dest)})
B=A/'production/source/blender'
for f in ['capture_runtime.py','native_actions.py','catalog_style.py','catalog_faceted.py','capture_worker.py','creature_fx_builders.py','publish_captures.py']:copy(B/f,'resources/native/'+f)
copy(B/'revisions/b1765262bfa897ad/sushi-loop-world-library.blend','resources/native/untouched-library.blend')
for f in ['asset.json','camera.json','rig.json']:copy(A/'production/source/records/attack-reef-fragments'/f,'resources/native/'+f)
for f in ['original.png','target.png','snapshot.json','catalog-object.json','imagegen-prompt.txt']:copy(O/'inputs'/f,'resources/inputs/'+f)
copy(A/'refinement/style/warm-soft-reference.png','resources/inputs/GLOBAL-warm-soft-reference.png')
for src,name in [(W/'AGENTS.md','AGENTS-root.md'),(W/'prototypes/sushi-loop/AGENTS.md','AGENTS-sushi-loop.md'),(Path('/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md'),'refine-3d-model-SKILL.md'),(O/'prompts/judge.txt','judge.txt'),(O/'brief.json','initial-brief.json'),(A/'refinement/preparation/attack-reef-fragments/judge-initial-dispatch.txt','judge-initial-dispatch.txt')]:copy(src,'resources/instructions/'+name)
for f in ['REVIEW-COVERAGE.txt','PUBLISHER-HANDOFF.txt','HEADLESS-BROWSER-CONFIGS.txt']:copy(A/'refinement/preparation'/f,'resources/instructions/'+f)
for f in ['world-sprite-raster.js','sprite-layout.js']:copy(W/'prototypes/sushi-loop/wireframe'/f,'resources/consumer/'+f)
lib=A/'production/library.json'; data=json.loads(lib.read_text());objects=data['objects']; current=next(o for o in objects if o['id']=='attack-reef-fragments')
(P/'resources/consumer/current-catalog-object.json').write_text(json.dumps(current,indent=2)+'\n')
for c in current['clips']:
 for d,e in c['directions'].items():copy(A/'production'/e['image'],'resources/consumer/'+e['image'])
for c in current['clips']:
 for d in c['directions']:
  f=A/'production/source/registered/attack-reef-fragments'/f"{c['id']}-{d}"/'guide.json'
  if f.exists():copy(f,'resources/native/guides/'+f"{c['id']}-{d}.json")
(P/'resources/input-provenance.json').write_text(json.dumps({'pathBase':'preparation-v1','files':files,'currentLibraryRead':{'path':str(lib),'sha256':sha(lib),'extraction':'exact object value serialized JSON; source bytes hashed'},'backupVerified':{'path':str(A/'refinement/backups/b1765262bfa897ad-sushi-loop-world-library.blend'),'sha256':sha(A/'refinement/backups/b1765262bfa897ad-sushi-loop-world-library.blend')}},indent=2)+'\n')
print(json.dumps({'frozenFiles':len(files),'clips':[{k:v for k,v in c.items() if k!='directions'} for c in current['clips']],'interactions':current.get('interactions'),'frame':current['frameSize'],'root':current['root'],'sourceScale':current['sourceScale']}))
