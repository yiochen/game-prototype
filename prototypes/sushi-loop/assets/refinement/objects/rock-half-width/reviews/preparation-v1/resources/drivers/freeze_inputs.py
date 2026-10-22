from pathlib import Path
import shutil,hashlib,json
repo=Path.cwd();obj=repo/'prototypes/sushi-loop/assets/refinement/objects/rock-half-width';res=obj/'reviews/preparation-v1/resources'
files={
'resource-inputs/brief.json':obj/'brief.json',
'original-library.blend':repo/'prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend',
'instructions/root-AGENTS.md':repo/'AGENTS.md','instructions/sushi-loop-AGENTS.md':repo/'prototypes/sushi-loop/AGENTS.md',
'instructions/refine-3d-model-SKILL.md':Path('/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md'),
'instructions/judge.txt':obj/'prompts/judge.txt',
'instructions/dispatch.txt':repo/'prototypes/sushi-loop/assets/refinement/preparation/rock-half-width/judge-dispatch.txt',
'instructions/REVIEW-COVERAGE.txt':repo/'prototypes/sushi-loop/assets/refinement/preparation/REVIEW-COVERAGE.txt',
'instructions/PUBLISHER-HANDOFF.txt':repo/'prototypes/sushi-loop/assets/refinement/preparation/PUBLISHER-HANDOFF.txt',
'instructions/HEADLESS-BROWSER-CONFIGS.txt':repo/'prototypes/sushi-loop/assets/refinement/preparation/HEADLESS-BROWSER-CONFIGS.txt',
'consumer/sprite-layout.js':repo/'prototypes/sushi-loop/wireframe/sprite-layout.js','consumer/world-sprite-raster.js':repo/'prototypes/sushi-loop/wireframe/world-sprite-raster.js',
'references/world_components.py':repo/'prototypes/sushi-loop/assets/production/source/blender/revisions/0d156c24ebd2a314/world_components.py',
'references/capture_runtime.py':repo/'prototypes/sushi-loop/assets/production/source/blender/capture_runtime.py',
'references/publish_captures.py':repo/'prototypes/sushi-loop/assets/production/source/blender/publish_captures.py',
'resource-inputs/warm-soft-reference.png':repo/'prototypes/sushi-loop/assets/refinement/style/warm-soft-reference.png'}
for p in (obj/'inputs').iterdir():
 if p.is_file():files['resource-inputs/'+p.name]=p
for d,s in files.items():
 dst=res/d;dst.parent.mkdir(parents=True,exist_ok=True)
 if dst.exists():assert dst.read_bytes()==s.read_bytes()
 else:shutil.copy2(s,dst)
records=[{'path':str((res/d).relative_to(obj)),'sha256':hashlib.sha256((res/d).read_bytes()).hexdigest(),'bytes':(res/d).stat().st_size,'originalPath':str(s)} for d,s in files.items()]
(obj/'reviews/preparation-v1/evidence/frozen-inputs.json').write_text(json.dumps({'pathBase':'object root','files':records},indent=2)+'\n')
print(len(records),'frozen files; source',next(r['sha256'] for r in records if r['path'].endswith('.blend')))
