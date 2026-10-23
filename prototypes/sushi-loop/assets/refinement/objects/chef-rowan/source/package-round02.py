"""Normalize completed round02 delivery, binding all native/assembly/proof resources. No seal."""
from pathlib import Path
import json,hashlib,copy
from PIL import Image
HERE=Path(__file__).parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-02'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rel(p):return str(Path(p).relative_to(OBJ))
def write(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
brief=read(OBJ/'brief-v3-food-depth.json');draft=read(OBJ/'delivery-round02-draft.json');metadata=read(HERE/'round02-metadata/validation.json')
assert read(OUT/'depth-only-audit.json')['allChecksPassed'] and read(OUT/'native-audit.json')['allChecksPassed']
assert read(HERE/'portability-proof-round02/receipt.json')['all20DecodedRGBAEqual']
assert metadata['projectSHA256']==sha(HERE/'round-02.blend')
previews={'four-view-sheet':'candidates/round-02/sheets/four-view-sheet.png','repeated':'candidates/round-02/sheets/repeated.png'}
for c in ['idle','work','hold','load']:
 for d in ['N','E','S','W']:previews[f'{c}-{d}']=f'candidates/round-02/playbacks/{c}-{d}.mp4'
for p in sorted((OUT/'sheets').glob('*.png')):previews.setdefault(p.stem,rel(p))
for p in sorted((OUT/'contexts').glob('*')):
 if p.suffix in ['.png','.mp4']:previews[f'context:{p.stem}:{p.suffix[1:]}']=rel(p)
previews['playback-page']='candidates/round-02/preview.html';previews['native-context-playback-qa']='candidates/round-02/playback-qa.html';previews['closed-package-held-load']='source/portability-proof-round02/held-load-all-facings.png'
assert set(brief['capture']['previews'])<=previews.keys()
for p in previews.values():assert (OBJ/p).is_file(),p
frames=[]
for r in read(OUT/'frame-index.json'):
 q=copy.deepcopy(r);q['globalIndex']=q['index'];q['index']=q['frame'];assert 0<=q['index']<12;frames.append(q)
assert len(frames)==192 and len({(r['clip'],r['direction'],r['index']) for r in frames})==192
for a in draft['atlases']:
 atlas=Image.open(OBJ/a['path']).convert('RGBA');assert a['columns']==6 and a['rows']==2 and atlas.size==(2304,1280)
 for r in [r for r in frames if r['clip']==a['clip'] and r['direction']==a['direction']]:
  i=r['index'];rect=a['rects'][i];assert rect==[i%6*384,i//6*640,384,640]
  assert atlas.crop((rect[0],rect[1],rect[0]+384,rect[1]+640)).tobytes()==Image.open(OBJ/r['path']).convert('RGBA').tobytes()
# Bind complete current outputs and exact local resources. Exclude self-referential packet/seal products.
paths=set(p for p in OUT.rglob('*') if p.is_file() and p.name not in ['packet-inputs.json','packet.json','delivery.snapshot.json'])
for pattern in ['*round02*','*round-02*']:
 for p in HERE.glob(pattern):
  if p.is_file():paths.add(p)
  elif p.is_dir():paths.update(q for q in p.rglob('*') if q.is_file())
for folder in [HERE/'resources',HERE/'round02-metadata',OBJ/'inputs']:
 paths.update(p for p in folder.rglob('*') if p.is_file())
for p in [HERE/'inspection-v1/native-action-audit.json',HERE/'inspection-v1/original-action-identity.json',OBJ/'brief-v3-food-depth.json',OBJ/'reviews/criteria-v3-food-depth.json',OBJ/'candidates/round-01/packet.json',OBJ/'reviews/round-01.json']:paths.add(p)
for p in paths:assert not p.is_symlink() and p.is_file(),p
renders=sorted(rel(p) for p in paths if p.suffix=='.png' and str(p).startswith(str(OUT)))
resource_paths=sorted(rel(p) for p in paths if rel(p) not in renders)
packet_inputs=dict(activeBrief='brief-v3-food-depth.json',project='source/round-02.blend',validation='source/round02-metadata/validation.json',renders=renders,resources=resource_paths)
write(OUT/'packet-inputs.json',packet_inputs);paths.add(OUT/'packet-inputs.json')
resources=[dict(path=rel(p),sha256=sha(p)) for p in sorted(paths)]
nativeRecords={k:v['path'] for k,v in metadata['nativeRecords'].items()}
draft.update(manifestVersion=2,manifestPurpose='Normalized immutable-review input for coordinator sealing; no self-approval',activeBrief='brief-v3-food-depth.json',project='source/round-02.blend',recipeScript='source/round-02-recipe.py',recipe='source/round-02-recipe.py',captureRecipe='source/capture-round-02.py',recipeSettings='source/round-02-recipe.json',heroes={d:f'candidates/round-02/frames/idle-{d}-00.png' for d in ['N','E','S','W']},previews=previews,nativeRecords=nativeRecords,validation='source/round02-metadata/validation.json',originalCaptureValidation='candidates/round-02/validation.json',rawFrames=frames,packetInputs='candidates/round-02/packet-inputs.json',resources=resources,depthOnlyAudit='candidates/round-02/depth-only-audit.json',hiddenFoodPixelAudit='candidates/round-02/hidden-food-pixel-audit.json',globalDisplayDepthWorldCells=.45,normalizationEvidence=dict(projectSHA256=sha(HERE/'round-02.blend'),measuredNativeRecords=192,rawFrameIndexPolicy='index0..11 clip-local, globalIndex retained separately',atlasLayoutsAndRGBAValidated=True),dependencyClosure=dict(savedSource='Closed copy with active brief, inputs, local action helper/inspection records and packed canonical image;20/20 representative decoded RGBA exact, all192 native pose audit passed, no sibling objects/production/linked libraries/symlinks required.',receipt='source/portability-proof-round02/receipt.json',readme='source/README-round02.md',reapplyRecipe='Exact included inputs/baseline-round01.blend is prerequisite; no original-library reconstruction claim.',assemblies='Exact local published neighbor/original atlas bytes and selected metadata in source/round02-context-resources; no production reads required by round02 assembly script.'),notes='Only globally shared plane camera-ray depth drivers/derivedZ/existing provenance changed from round01. Current192 native frames untouched; no raster patches. 94/96 idle/work frames exactly equal prior; two reproducible single-interior-pixel one-level RGB deltas, zero alpha differences, documented separately. Independent judge approval pending. No production edits or self-approval.')
write(OBJ/'delivery-round02.json',draft)
print(json.dumps(dict(delivery='delivery-round02.json',projectSHA256=sha(HERE/'round-02.blend'),rawFrames=len(frames),atlases=len(draft['atlases']),previews=len(previews),resources=len(resources),activeBrief=draft['activeBrief'],deliverySHA256=sha(OBJ/'delivery-round02.json')),indent=2))
