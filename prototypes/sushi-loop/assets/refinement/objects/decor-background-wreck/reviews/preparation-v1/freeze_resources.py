from pathlib import Path
import shutil,json,hashlib
root=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
obj=root/'prototypes/sushi-loop/assets/refinement/objects/decor-background-wreck'
p=obj/'reviews/preparation-v1';res=p/'resources'
def cp(src,dst):
    dst=res/dst;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
for f in ['original.png','target.png','catalog-object.json','source-camera.json','source-assetRecord.json','source-rig.json','imagegen-prompt.txt','generation.json']:cp(obj/'inputs'/f,Path('inputs')/f)
cp(root/'prototypes/sushi-loop/assets/refinement/style/warm-soft-reference.png',Path('inputs/warm-soft-reference.png'))
cp(root/'prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend',Path('source/sushi-loop-world-library.blend'))
cp(root/'prototypes/sushi-loop/assets/refinement/backups/b1765262bfa897ad-sushi-loop-world-library.blend',Path('source/untouched-backup.blend'))
for f in ['AGENTS.md','prototypes/sushi-loop/AGENTS.md','prototypes/sushi-loop/design/art-directions/decisions.md','prototypes/sushi-loop/assets/refinement/preparation/HEADLESS-BROWSER-CONFIGS.txt','prototypes/sushi-loop/assets/refinement/preparation/REVIEW-COVERAGE.txt','prototypes/sushi-loop/assets/refinement/preparation/PUBLISHER-HANDOFF.txt','prototypes/sushi-loop/assets/refinement/preparation/decor-background-wreck/judge-initial-dispatch.txt']:cp(root/f,Path('instructions')/Path(f).name if f!='AGENTS.md' else Path('instructions/root-AGENTS.md'))
cp(Path('/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md'),Path('instructions/refine-3d-model-SKILL.md'))
cp(obj/'prompts/judge.txt',Path('instructions/judge.txt'));cp(obj/'brief.json',Path('instructions/brief-before-root-freeze.json'))
for f in ['capture_runtime.py','catalog_style.py','catalog_faceted.py']:
    cp(root/'prototypes/sushi-loop/assets/production/source/blender'/f,Path('historical')/f)
cp(root/'prototypes/sushi-loop/assets/production/source/blender/revisions/0d156c24ebd2a314/world_components.py',Path('historical/world_components.py'))
for f in ['world-sprite-raster.js','sprite-layout.js','object-review.jsx','object-review-data.js','object-review.css']:cp(root/'prototypes/sushi-loop/wireframe'/f,Path('consumer')/f)
for f in ['seal_object.py','promote_object.py','audit_directions.py','acceptance_contract.py']:cp(root/'prototypes/sushi-loop/assets/refinement/tools'/f,Path('interface')/f)
for f in ['package.json','package-lock.json','playwright.config.js']: 
    if (root/f).exists():cp(root/f,Path('consumer')/f)
print('frozen resources',len(list(res.rglob('*'))))
