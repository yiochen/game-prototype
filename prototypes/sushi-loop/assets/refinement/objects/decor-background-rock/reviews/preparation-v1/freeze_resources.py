"""Freeze the exact small input/code closure used by this source-only judge pass."""
from pathlib import Path
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent.parent;ASSETS=OBJ.parents[2];REPO=ASSETS.parents[2]
R=HERE/'resources';R.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
copied=[]
def copy(src,dest):
    dest=R/dest;dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():assert sha(src)==sha(dest),(src,dest)
    else:shutil.copy2(src,dest)
    copied.append({'source':str(src),'path':str(dest.relative_to(OBJ)),'sha256':sha(dest),'size':dest.stat().st_size})
copy(ASSETS/'production/library.json',Path('consumer/library.json'))
lib=json.loads((R/'consumer/library.json').read_text());ids=['decor-background-rock','submarine-yellow','creature-eel','floor-underwater'];selected=[x for x in lib['objects'] if x['id'] in ids]
(R/'consumer/selected-library.json').write_text(json.dumps({'cellSize':lib['cellSize'],'objects':selected},indent=2)+'\n')
for o in selected:
    if o['id']=='decor-background-rock':clips=o['clips'];facings='NESW'
    elif o['id']=='submarine-yellow':clips=[next(x for x in o['clips'] if x['id']=='travel')];facings='N'
    elif o['id']=='creature-eel':clips=[next(x for x in o['clips'] if x['id']=='swim')];facings='N'
    else:clips=[o['clips'][0]];facings='S'
    for clip in clips:
        for facing in facings:
            im=clip['directions'][facing]['image'];copy(ASSETS/'production'/im,Path('consumer')/im)
for p in (OBJ/'inputs').iterdir():
    if p.is_file():copy(p,Path('inputs')/p.name)
copy(OBJ/'brief.json',Path('instructions/brief.json'))
copy(OBJ/'prompts/judge.txt',Path('instructions/judge.txt'))
copy(ASSETS/'refinement/style/warm-soft-reference.png',Path('inputs/warm-soft-reference.png'))
copy(ASSETS/'production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend',Path('native/source.blend'))
for name in ['catalog_concept_decor.py','capture_runtime.py','concept_decoration_geometry.py','native_actions.py','catalog_style.py','catalog_faceted.py','publish_captures.py']:
    copy(ASSETS/'production/source/blender'/name,Path('native-code/current')/name)
own=next(o for o in selected if o['id']=='decor-background-rock')
for name in ['catalog_concept_decor.py','capture_runtime.py','concept_decoration_geometry.py','native_actions.py','catalog_style.py','catalog_faceted.py','publish_captures.py']:
    src=ASSETS/'production'/own['source']['nativeScripts'][name];copy(src,Path('native-code/registered')/name)
for facing in 'NESW':
    for name in ['guide.json','capture-fingerprint.json']:copy(ASSETS/'production/source/registered/decor-background-rock'/f'static-{facing}'/name,Path('registration')/facing/name)
for name in ['REVIEW-COVERAGE.txt','PUBLISHER-HANDOFF.txt','HEADLESS-BROWSER-CONFIGS.txt']:
    copy(ASSETS/'refinement/preparation'/name,Path('instructions')/name)
copy(ASSETS/'refinement/preparation/decor-background-rock/judge-initial-dispatch.txt',Path('instructions/actual-judge-dispatch.txt'))
for name in ['sprite-layout.js','world-sprite-raster.js','object-review.jsx','object-review.css','object-review-data.js']:
    copy(REPO/'prototypes/sushi-loop/wireframe'/name,Path('consumer')/name)
for name in ['seal_object.py','promote_object.py','audit_directions.py','acceptance_contract.py']:
    copy(ASSETS/'refinement/tools'/name,Path('instructions/tools')/name)
for src,dest in [('/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md','instructions/refine-3d-model/SKILL.md'),('/Users/yiouchen/.codex/skills/refine-3d-model/assets/judge-prompt.txt','instructions/refine-3d-model/judge-prompt.txt'),('/Users/yiouchen/.codex/skills/refine-3d-model/references/brief.md','instructions/refine-3d-model/brief.md'),('/Users/yiouchen/.codex/skills/refine-3d-model/references/blender-techniques.md','instructions/refine-3d-model/blender-techniques.md')]:
    copy(Path(src),Path(dest))
copy(REPO/'AGENTS.md',Path('instructions/AGENTS.md'));copy(REPO/'prototypes/sushi-loop/AGENTS.md',Path('instructions/sushi-loop-AGENTS.md'))
copy(REPO/'package.json',Path('consumer/package.json'));copy(REPO/'package-lock.json',Path('consumer/package-lock.json'))
copy(REPO/'node_modules/@playwright/test/package.json',Path('consumer/playwright-package.json'))
(HERE/'frozen-inputs.json').write_text(json.dumps({'pathBase':'object root','files':copied,'notes':['All copied bytes frozen before final hashes. No runtime/application package trees copied.','Entire mutable library is retained as actually read; selected-library is the bounded browser closure.','Registered historical raw native PNG paths are absent in this checkout; guides and published originals are retained, independent replay residuals are reported honestly.']},indent=2)+'\n')
print('FROZEN',len(copied),'files',sum(x['size'] for x in copied),'bytes')
