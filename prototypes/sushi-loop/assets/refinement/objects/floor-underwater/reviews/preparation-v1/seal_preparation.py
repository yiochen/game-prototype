import sys,json,hashlib,shutil,os
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;O=P.parent.parent;R=P/'resources'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def ref(p,role=None):
 d={'path':str(p.relative_to(O)),'sha256':sha(p),'relativeTo':'object','pathBase':str(O),'bytes':p.stat().st_size}
 if role:d['role']=role
 return d
inspected=['resources/inputs/original.png','resources/inputs/target.png','resources/warm-soft-reference.png','replay-raw/S/000.png','replay-raw/E/003.png','replay-raw/N/006.png','replay-raw/W/009.png','packed/contexts-S.png','native-patch/S-000.png','native-patch/overview.png','consumer/native-S-0.png','consumer/logical-E-1.png','consumer/phone-W-09.png','consumer/context-S-0.png','consumer/context-N-1.png','consumer/context-W-2.png']
inspected += ['packed/all-phases-'+v+'.png' for v in 'NESW']+['consumer/all-phases-'+v+'.png' for v in 'NESW']
review={'asset':'floor-underwater','stage':'preparation-complete-await-root-freeze','candidateVerdict':None,'initialObservations':ref(O/'reviews/initial.json'),'criteria':ref(O/'reviews/proposedcriteria.json'),'technicalProposal':ref(O/'reviews/source-contract-proposal.json'),'inspectedFiles':[ref(P/name,'directly inspected image or verified contact sheet') for name in inspected],'visualFindings':['The original remains a fully opaque flat turquoise panel with two dark ribbons. No black/empty interior hole appeared in inspected views.','Native3x3 and independent3x3 consumer images show a prominent dark rectangular grid from four grout strips, including at phone size. This conflicts with continuous water goal.','The motion phase advances coherently across same-facing patch tiles; nativeKey closure is exact. Existing flat bands provide weak depth/detail compared with frozen connected caustic reference.','Source/reference submarine and rock remain readable over the calm source floor; contextual images do not approve those objects or prescribe their style.'],'technicalLimits':['No candidate exists and no candidate approval is issued.','276 common-canvas cases measure internal alpha only; visible screenshots separately show grid defects. No absence-of-artifact claim comes from count or hashes alone.','All4×12 single-tile and phone phase sheets are inspected; native3x3 baseline evidence samples phases0/3 in every facing. Future candidate needs every phase and playback in assembled form.','No arbitrary mixed-facing gameplay joins or unseen views are inferred.','Source footprint overhang andZ0 support/.004 envelope proposal require root reconciliation before editor.'],'next':'Root freezes outcomes/technical contract, then a fresh editor constructs; original independent judge later reviews exact sealed candidate.'}
(P/'preparation-review.json').write_text(json.dumps(review,indent=2)+'\n')
recipe=R/'recipe';recipe.mkdir(exist_ok=True)
for p in P.iterdir():
 if p.suffix in ('.py','.mjs','.html','.txt'):shutil.copyfile(p,recipe/p.name)
runtimes=[]
for name,location,version in [('Blender','/opt/homebrew/bin/blender','5.2.2 LTS d13f752e3b9c'),('Python','/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3','3.12; see python-runtime.json'),('Node','/Users/yiouchen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node','v24.19.0')]:
 p=Path(location).resolve();runtimes.append({'name':name,'executablePath':location,'resolvedExecutable':str(p),'sha256':sha(p),'version':version,'role':'runtime prerequisite; do not stage large runtime tree'})
browser=json.loads((P/'browser-runtime.json').read_text());runtimes.append({'name':'Chromium','executablePath':browser['browserExecutable'],'sha256':browser['browserSHA256'],'version':browser['browserVersion'],'role':'runtime prerequisite; do not stage app bundle'})
files=[ref(p) for p in sorted((O/'reviews').rglob('*')) if p.is_file() and p.name not in ('preparation-manifest.json','preparation-seal.json')]
assert all(x['bytes']<100_000_000 for x in files)
manifest={'schema':'floor-underwater-independent-preparation-v1','asset':'floor-underwater','stage':'preparation only; pending root freeze/fresh editor','relativeTo':'object','pathBase':str(O),'resources':[f for f in files if f['path'].startswith('reviews/preparation-v1/resources/')],'files':files,'runtimePrerequisites':runtimes,'bytecode':'All native imports use sys.dont_write_bytecode/PYTHONDONTWRITEBYTECODE. Frozen closure has no pycache.','resourcePolicy':'Exact minimal source/skill/helper/input/runtime-library package closure. OS/runtime binaries are version/hash recorded prerequisites, not duplicated app/runtime trees. One source blend snapshot binds byte-identical source and backup.','reproduction':ref(P/'README.txt'),'evidence':ref(P/'preparation-review.json'),'notApproval':'No candidate or family/main/production approval is inferred.'}
mp=P/'preparation-manifest.json';mp.write_text(json.dumps(manifest,indent=2)+'\n')
seal={'schema':'floor-underwater-preparation-seal-v1','stage':'sealed preparation only; root freezes proposals separately','manifest':ref(mp),'proposals':[ref(O/'reviews/initial.json'),ref(O/'reviews/proposedcriteria.json'),ref(O/'reviews/source-contract-proposal.json')],'source':ref(R/'source-original.blend'),'target':ref(R/'inputs/target.png'),'rule':'Review scope is these exact bytes. Root may freeze or request versioned changes; do not silently mutate this packet. No candidate approval.'}
(P/'preparation-seal.json').write_text(json.dumps(seal,indent=2)+'\n')
print(json.dumps({'manifestSHA256':sha(mp),'sealSHA256':sha(P/'preparation-seal.json'),'files':len(files),'resources':len(manifest['resources']),'totalBytes':sum(x['bytes'] for x in files),'maxFileBytes':max(x['bytes'] for x in files),'proposals':seal['proposals']},indent=2))
