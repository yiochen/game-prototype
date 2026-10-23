import sys
sys.dont_write_bytecode = True
from pathlib import Path
import shutil, hashlib, json, platform, subprocess
import PIL
B=Path(__file__).resolve().parents[1]
R=B.parents[7]
O=B.parents[1]
M=O.parent/'reef-middle'
sources={
 'object/brief.json':O/'brief.json',
 **{'object/'+p.name:p for p in (O/'inputs').iterdir() if p.name in ['original.png','target.png','snapshot.json','source-camera.json','source-assetRecord.json','source-rig.json','catalog-object.json']},
 'object/judge-prompt.txt':O/'prompts/judge.txt',
 'object/warm-soft-reference.png':O.parents[1]/'style/warm-soft-reference.png',
 'source/original.blend':O.parents[1]/'backups/b1765262bfa897ad-sushi-loop-world-library.blend',
 'canonical/round-02.blend':M/'source/round-02.blend',
 'canonical/packet.json':M/'candidates/round-02/packet.json',
 'canonical/review.json':M/'reviews/round-02.json',
 'canonical/root-native-contract.json':M/'inputs/root-native-contract.json',
 'canonical/technical-capture-recipe.py':M/'source/reproduce-round-02.py',
 'canonical/source-extent-interpretation.json':M/'reviews/preparation-v3/interpretation.json',
 'canonical/source-extent-procedure.cjs':M/'reviews/preparation-v3/equal_extents_calibration.cjs',
 'instructions/root-AGENTS.md':R/'AGENTS.md',
 'instructions/sushi-loop-AGENTS.md':R/'prototypes/sushi-loop/AGENTS.md',
 'instructions/refine-SKILL.md':Path('/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md'),
 'instructions/dispatch.txt':O.parents[1]/'preparation/reef-edge/judge-dispatch.txt',
 'instructions/HEADLESS-BROWSER-CONFIGS.txt':O.parents[1]/'preparation/HEADLESS-BROWSER-CONFIGS.txt',
 **{'native/'+name:R/'prototypes/sushi-loop/assets/production/source/blender'/name for name in ['capture_runtime.py','catalog_style.py','catalog_faceted.py']},
 **{'consumer/'+name:R/'prototypes/sushi-loop/wireframe'/name for name in ['world-sprite-raster.js','sprite-layout.js']}
}
records=[]
for dest,src in sources.items():
    dst=B/'resources'/dest
    if dst.exists(): raise FileExistsError(dst)
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    records.append({'source':str(src),'frozen':str(dst.relative_to(B)),'sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'bytes':dst.stat().st_size})
(B/'resource-index.json').write_text(json.dumps(records,indent=2)+'\n')
v={'python':sys.version,'pillow':PIL.__version__,'platform':platform.platform(),'blender':subprocess.check_output(['/opt/homebrew/bin/blender','--version'],text=True),'executables':{}}
for name,path in {'blenderWrapper':'/opt/homebrew/bin/blender','blenderBinary':'/Applications/Blender.app/Contents/MacOS/Blender','python':sys.executable,'node':'/usr/local/bin/node'}.items():
 p=Path(path);v['executables'][name]={'path':path,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
v['browserExecution']='No browser matrix executed during preparation. Required future configurations are frozen in the evidence plan.'
(B/'evidence/toolchain.json').write_text(json.dumps(v,indent=2)+'\n')
print('FROZEN',len(records),'inputs',sum(r['bytes'] for r in records))
