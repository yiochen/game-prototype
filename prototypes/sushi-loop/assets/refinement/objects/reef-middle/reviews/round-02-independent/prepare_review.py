import sys
sys.dont_write_bytecode = True
from pathlib import Path
import hashlib, json, shutil, os

B=Path(__file__).resolve().parent; O=B.parent.parent; R=O.parents[5]; P=O/'candidates/round-02'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(v,indent=2)+'\n')
assert sha(P/'packet.json')=='d60ff36edc6006a0d4082692e7c115be23e1fc1e9d674f8bdc5c2f8ccc447ca8'
assert sha(O/'source/round-02.blend')=='51d515119c1a229f57f3b242fdf040b28ef00121692cb3d40d8821dab70ff3c5'
assert sha(O/'brief.json')=='ff47e76406d5d0ed40bc5e6ed85ef8d78eba33db0d0b2ee4740afb870d457271'
assert sha(O/'inputs/root-native-contract.json')=='738552afcc57f82a83f6f5f58bc5b26ec6bc95fe987e99277624e8c7e0b457c5'
packet=json.loads((P/'packet.json').read_text()); records=[]
for group in ['files','candidateRenders','previews']:
 for name,item in packet[group].items():
  p=(P/item['path']).resolve(); assert sha(p)==item['sha256'],str(p)
  records.append({'group':group,'name':name,'path':os.path.relpath(p,O),'sha256':sha(p),'bytes':p.stat().st_size})
save(B/'packet-integrity.json',{'packetSHA256':sha(P/'packet.json'),'sourceSHA256':sha(O/'source/round-02.blend'),'verifiedRecords':len(records),'records':records})
copies={
 'source/round-02.blend':O/'source/round-02.blend',
 'object/brief.json':O/'brief.json','object/native-contract.json':O/'inputs/root-native-contract.json',
 'object/packet.json':P/'packet.json','object/original.png':O/'inputs/original.png','object/target.png':O/'inputs/target.png',
 'object/proposedcriteria.json':O/'reviews/proposedcriteria.json','object/round-01-review.json':O/'reviews/round-01.json',
 'object/warm-soft-reference.png':O.parent.parent/'style/warm-soft-reference.png',
 'instructions/AGENTS.md':R/'AGENTS.md','instructions/game-AGENTS.md':R/'prototypes/sushi-loop/AGENTS.md',
 'instructions/REVIEW-COVERAGE.txt':O.parent.parent/'preparation/REVIEW-COVERAGE.txt',
 'instructions/judge-dispatch.txt':O.parent.parent/'preparation/reef-middle/judge-round-02-dispatch.txt',
 'instructions/judge-prompt.txt':O/'prompts/judge.txt',
 'instructions/refine-SKILL.md':Path('/Users/yiouchen/.codex/skills/refine-3d-model/SKILL.md'),
 'tools/acceptance_contract.py':O.parent.parent/'tools/acceptance_contract.py',
}
# Bind/reuse the exact previously saved current570 consumer extraction, after verifying it against production.
old=O/'reviews/round-01-independent'
for name in ['world-sprite-raster.js','sprite-layout.js','exact-used-raster-functions.js','catalog-object.json','host.html']:
 copies['consumer/'+name]=old/'resources/consumer'/name
for target,src in copies.items():
 dst=B/'resources'/target;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
assert sha(B/'resources/consumer/world-sprite-raster.js')=='570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545'
assert sha(B/'resources/consumer/sprite-layout.js')=='099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'
# Preserve exact new submitted drivers before their invocation; no native construction recipe is run.
for name in ['reopen_audit.py','analyze_native.py','independent_consumer_replay.cjs','consumer_and_coverage.py']:
 text=(old/name).read_text().replace('round-01','round-02').replace('round01','round02').replace('8b37245ce44d02d4782e5d8bfcf8d4efca27813262b2f051eb5ad99abcca4849',sha(P/'packet.json'))
 if name=='analyze_native.py':
  text=text.replace('Flat slab appearance and lost stone separation are assessed','Support massing and stone separation are assessed')
 (B/name).write_text(text)
(B/'evidence').mkdir(exist_ok=True)
save(B/'first-look.json',{'basis':'Fixed target, actual4heroes, use-size, four-view and fixed-scale round01/02 comparison inspected before candidate technical audit/rationale. Editor rationale/self-ratings not read.',
 'observations':['Blue stones are now distinct raised rounded/faceted masses in all4 instead of near-flat samecyan patches.','Central support has stronger stepped planes; useful blue rock hierarchy is visible at logical128 and coherent at phone32.','Teal focal hollow group and purple supporting clusters remain readable. Palette and broad symmetric lighting remain coherent.','Technical checks and full1:1 repeated-preview inspection still pending; no verdict from first look.']})
print(json.dumps({'packetRecords':len(records),'driverDirectory':str(B),'sourceSHA256':sha(B/'resources/source/round-02.blend')}))
