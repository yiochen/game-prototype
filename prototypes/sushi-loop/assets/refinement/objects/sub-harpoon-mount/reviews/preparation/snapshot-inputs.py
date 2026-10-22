from pathlib import Path
import shutil,json,hashlib
W=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype');B=W/'prototypes/sushi-loop/assets/refinement/objects/sub-harpoon-mount';R=B/'reviews/preparation/resources'
files=[]
def take(s,d):
 s=Path(s);d=R/d;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s,d);files.append({'source':str(s),'snapshot':str(d.relative_to(B/'reviews')),'sha256':hashlib.sha256(d.read_bytes()).hexdigest(),'bytes':d.stat().st_size})
for s in (B/'inputs').rglob('*'):
 if s.is_file():take(s,Path('inputs')/s.relative_to(B/'inputs'))
for s in [B/'brief.json',B/'prompts/judge.txt',W/'AGENTS.md',W/'prototypes/sushi-loop/AGENTS.md']:
 take(s,Path('contracts')/('sushi-AGENTS.md' if s==W/'prototypes/sushi-loop/AGENTS.md' else s.name))
for n in ['capture_runtime.py','native_actions.py','catalog_style.py','catalog_faceted.py','publish_captures.py','production_library.py']:
 take(W/'prototypes/sushi-loop/assets/production/source/blender'/n,Path('blender-code')/n)
take(W/'prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend',Path('own-original-library.blend'))
take(W/'prototypes/sushi-loop/assets/production/source/blender/revisions/46d7e4eeabce858f/prop_builders.py',Path('blender-code/source-prop_builders.py'))
for n in ['object-review.jsx','object-review-data.js','sprite-layout.js','world-sprite-raster.js','object-review.css']:
 take(W/'prototypes/sushi-loop/wireframe'/n,Path('browser')/n)
take(W/'prototypes/sushi-loop/assets/production/library.json',Path('browser/library.json'))
lib=json.loads((R/'browser/library.json').read_text());comp=[]
for a in lib['objects']:
 if a['id'] in ['submarine-yellow','creature-eel','sub-harpoon-mount']:
  comp.append(a)
  for c in a['clips']:
   if (a['id']=='submarine-yellow' and c['id']=='upgraded-dock-ready') or (a['id']=='creature-eel' and c['id']=='swim'):
    for d,r in c['directions'].items():take(W/'prototypes/sushi-loop/assets/production'/r['image'],Path('browser')/r['image'])
(R/'browser/selected-objects.json').write_text(json.dumps(comp,indent=2)+'\n')
S=Path('/Users/yiouchen/.codex/skills/refine-3d-model')
for s in S.rglob('*'):
 if s.is_file() and '__pycache__' not in str(s):take(s,Path('skill/refine-3d-model')/s.relative_to(S))
take(W/'prototypes/sushi-loop/assets/refinement/style/warm-soft-reference.png',Path('warm-soft-reference.png'))
(R/'snapshot-manifest.json').write_text(json.dumps({'files':files,'qualification':'Immutable byte snapshots of source data/code used in this own judge preparation. Current library is consumer context only, not source authority for the harpoon.'},indent=2)+'\n')
print(len(files),sum(x['bytes'] for x in files))
