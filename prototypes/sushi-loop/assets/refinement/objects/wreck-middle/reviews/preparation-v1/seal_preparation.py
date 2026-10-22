"""Seal this preparation once; --verify checks the retained bytes read-only."""
from pathlib import Path
import hashlib, json, sys, platform
import PIL, numpy
OUT=Path(__file__).resolve().parent
OBJECT=OUT.parent.parent
ROOT=OBJECT.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def record(p,role):
    p=p.resolve()
    if p.stat().st_size>=100_000_000:raise ValueError('File exceeds 100MB: '+str(p))
    try:rel=p.relative_to(ROOT);base='worktree';name=str(rel)
    except ValueError:base='absolute';name=str(p)
    return {'pathBase':base,'path':name,'sha256':sha(p),'bytes':p.stat().st_size,'role':role}
def resolve(r):return ROOT/r['path'] if r['pathBase']=='worktree' else Path(r['path'])
manifest=OUT/'manifest.json';seal=OUT/'seal.json'
if '--verify' in sys.argv:
    seal_data=json.loads(seal.read_text())
    assert sha(manifest)==seal_data['manifestSHA256']
    data=json.loads(manifest.read_text())
    for r in data['files']:
        p=resolve(r);assert p.is_file() and sha(p)==r['sha256'],str(p)
    print(json.dumps({'status':'verified-preparation-only','files':len(data['files']),'manifestSHA256':sha(manifest),'sealSHA256':sha(seal)}))
    raise SystemExit(0)
if manifest.exists() or seal.exists():raise RuntimeError('Do not overwrite an existing preparation seal')
resources=[]
for p in sorted(OUT.rglob('*')):
    if p.is_file():
        if '__pycache__' in p.parts or p.suffix=='.pyc':raise ValueError('Unexpected bytecode dependency '+str(p))
        resources.append(record(p,'actual preparation driver/imported module, retained diagnostic output or proposed handoff'))
for name in ['initial.json','criteria.json']:resources.append(record(OUT.parent/name,'independent first observations or proposed visible criteria'))
external={
 'prototypes/sushi-loop/assets/production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend':'actual evaluated and rendered original source; no external wreck texture dependency',
 'prototypes/sushi-loop/assets/production/source/blender/revisions/0d156c24ebd2a314/world_components.py':'consulted authored profile/path/role reference; not imported by replay',
 'prototypes/sushi-loop/assets/refinement/style/warm-soft-reference.png':'independently inspected fixed style pixels',
 'prototypes/sushi-loop/wireframe/world-sprite-raster.js':'consulted unchanged actual consumer helper for future evidence plan; not executed here',
 'prototypes/sushi-loop/wireframe/sprite-layout.js':'consulted unchanged registration/ordering helper for future evidence plan; not executed here',
 'prototypes/sushi-loop/assets/refinement/preparation/REVIEW-COVERAGE.txt':'consulted future exact visual coverage rules',
 'prototypes/sushi-loop/assets/refinement/preparation/PUBLISHER-HANDOFF.txt':'consulted future delivery schema',
 'prototypes/sushi-loop/assets/refinement/preparation/HEADLESS-BROWSER-CONFIGS.txt':'consulted actual headless modes; browser work remains pending',
 'prototypes/sushi-loop/assets/refinement/preparation/wreck-middle/judge-dispatch.txt':'exact preparation task dispatch',
 'prototypes/sushi-loop/assets/refinement/tools/seal_object.py':'consulted future candidate interface, not executed',
 'prototypes/sushi-loop/assets/refinement/tools/promote_object.py':'consulted future publisher interface, not executed',
 'prototypes/sushi-loop/assets/refinement/tools/audit_directions.py':'consulted future actual-matrix validation, not executed',
 'AGENTS.md':'applicable repository instructions',
 'prototypes/sushi-loop/AGENTS.md':'applicable game instructions'
}
for name in ['brief.json','prompts/judge.txt']:
    external[str((OBJECT/name).relative_to(ROOT))]='own actual brief or judge instruction'
for p in (OBJECT/'inputs').iterdir():
    if p.name in ['original.png','target.png','catalog-object.json','source-camera.json','source-assetRecord.json','source-rig.json']:
        external[str(p.relative_to(ROOT))]='own fixed original/target/catalog/native metadata input actually inspected'
for d in 'NESW':
    external[f'prototypes/sushi-loop/assets/production/sprites/wreck-middle/static-{d}.png']='original all4 atlas byte comparison reference'
    for name in ['guide.json','capture-fingerprint.json']:
        external[f'prototypes/sushi-loop/assets/production/source/registered/wreck-middle/static-{d}/{name}']='registered historical camera/publication/raw-hash evidence'
for p,role in external.items():resources.append(record(ROOT/p,role))
resources.append(record(Path('/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md'),'applicable preparation-only skill instructions'))
data={'version':1,'asset':'wreck-middle','scope':'immutable independent preparation; no candidate or family approval',
 'pathBases':{'worktree':str(ROOT),'absolute':'literal absolute path'},
 'toolchain':{'blenderExecutable':'/opt/homebrew/bin/blender','blenderVersion':'5.2.2 LTS','blenderBuildHash':'d13f752e3b9c',
    'pythonExecutable':sys.executable,'pythonVersion':platform.python_version(),'pillowVersion':PIL.__version__,'numpyVersion':numpy.__version__,
    'runtimePolicy':'Toolchain binaries/libraries remain installed external runtimes; do not copy application or Python trees. PYTHONDONTWRITEBYTECODE=1. Three actual imported capture helper modules are retained in dependencies/.'},
 'files':resources,'limits':['No connected-native candidate assembly or browser fixture executed.','No geometry/material candidate construction, target/brief/source edits, Git/live Blender/device/production actions.','Historical raw PNGs absent; original atlas PNG bytes reproduce exactly all4.']}
manifest.write_text(json.dumps(data,indent=2)+'\n')
sealed={'version':1,'asset':'wreck-middle','status':'sealed-preparation-only','manifestPath':'manifest.json','manifestSHA256':sha(manifest),
 'rootAction':'Reconcile and freeze criteria/capture/envelope before a separate fresh editor.','approval':False,
 'fileCount':len(resources),'largestFileBytes':max(r['bytes'] for r in resources)}
seal.write_text(json.dumps(sealed,indent=2)+'\n')
for r in resources:
    p=resolve(r)
    if p.is_relative_to(OBJECT/'reviews'):p.chmod(0o444)
manifest.chmod(0o444);seal.chmod(0o444)
print(json.dumps({'status':'sealed-preparation-only','files':len(resources),'manifestSHA256':sha(manifest),'sealSHA256':sha(seal)}))
