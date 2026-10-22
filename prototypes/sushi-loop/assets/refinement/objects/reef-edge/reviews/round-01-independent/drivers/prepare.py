import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,shutil,platform
import PIL
B=Path(__file__).resolve().parents[1];O=B.parents[1];R=B.parents[7];C=O/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
packet=json.loads((C/'packet.json').read_text());assert sha(C/'packet.json')=='270d330ded27fa71bc0b1484698e5e75ef671ce5d45bde767d66af559a4ad453'
records=[];fail=[]
for group in ['files','candidateRenders','previews']:
 for name,rec in packet[group].items():
  p=(C/rec['path']).resolve();actual=sha(p);records.append({'group':group,'alias':name,'path':rec['path'],'sha256':actual,'bytes':p.stat().st_size})
  if actual!=rec['sha256']:fail.append(rec['path'])
assert not fail,fail
(B/'evidence/packet-integrity.json').write_text(json.dumps({'candidatePacketSHA256':sha(C/'packet.json'),'recordsVerified':len(records),'failures':fail,'records':records},indent=2)+'\n')
sources={
 'candidate.blend':O/'source/round-01.blend','canonical-middle02.blend':O.parent/'reef-middle/source/round-02.blend','packet.json':C/'packet.json','brief.json':O/'brief.json','native-contract.json':O/'inputs/root-native-contract.json','catalog-object.json':O/'inputs/catalog-object.json',
 'world-sprite-raster.js':R/'prototypes/sushi-loop/wireframe/world-sprite-raster.js','sprite-layout.js':R/'prototypes/sushi-loop/wireframe/sprite-layout.js','context-geometry.json':C/'evidence/context-geometry.json','acceptance_contract.py':R/'prototypes/sushi-loop/assets/refinement/tools/acceptance_contract.py',
 'judge-dispatch.txt':R/'prototypes/sushi-loop/assets/refinement/preparation/reef-edge/judge-round-01-dispatch.txt','REVIEW-COVERAGE.txt':R/'prototypes/sushi-loop/assets/refinement/preparation/REVIEW-COVERAGE.txt','HEADLESS-BROWSER-CONFIGS.txt':R/'prototypes/sushi-loop/assets/refinement/preparation/HEADLESS-BROWSER-CONFIGS.txt',
 'judge-prompt.txt':O/'prompts/judge.txt','AGENTS-root.md':R/'AGENTS.md','AGENTS-sushi.md':R/'prototypes/sushi-loop/AGENTS.md','refine-SKILL.md':Path('/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md')}
index=[]
for name,p in sources.items():
 dest=B/'resources'/name;shutil.copyfile(p,dest);index.append({'source':str(p),'frozen':str(dest.relative_to(B)),'sha256':sha(dest),'bytes':dest.stat().st_size})
text=(B/'resources/world-sprite-raster.js').read_text();extracted=text[text.index('export function worldRasterPlan'):text.index('export function useWorldSpriteRaster')];(B/'resources/exact-used-raster-functions.js').write_text(extracted)
assert sha(B/'resources/world-sprite-raster.js')=='570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545'
assert sha(B/'resources/sprite-layout.js')=='099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'
(B/'resource-index.json').write_text(json.dumps(index,indent=2)+'\n')
(B/'evidence/toolchain-python.json').write_text(json.dumps({'python':sys.version,'executable':sys.executable,'pillow':PIL.__version__,'platform':platform.platform()},indent=2)+'\n')
print('PACKET_VERIFIED',len(records),'MINIMAL_RESOURCES',len(index))
