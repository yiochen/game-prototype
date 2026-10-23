import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib,datetime
P=Path(__file__).resolve().parent;E=P.parent;C=E/'candidates/round-01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
frozen={'brief.json':'d5096449ffa4034c3f1a9a46e53c707d25ff55118b30874cf84d3a439b4dc4b0','inputs/root-native-contract.json':'2f1b819b4bd51c259f151e7b8ddabe022b9541d2f087583a9652eff1fa433896','inputs/root-preparation-reconciliation-v1.json':'6bc63b443027e7cd884baacccebbbc55c4db9cc542cd0394f13aaff7a4404dc9','reviews/criteria.json':'261342c4418a19dccb561aca940e95c3c4f04f36c7421fa411330d31378913c3','source/initial-observations.json':'83310489eea8fe985f9a1d9d338c7bc2b189e80a43ec3b1ec1ff9ed2379c1eed','source/construction-acknowledgment.json':'e91c91c7c43bf5abef9b09a39df57299ccc10ecbd746f0e3dbde7853d6c11141'}
for p,s in frozen.items():assert sha(E/p)==s,p
assert sha(P/'resources/raw-original.blend')=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
assert sha(C/'resources/consumer/sprite-layout.js')=='099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65'
assert sha(C/'resources/consumer/world-sprite-raster.js')=='570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545'
pub=json.loads((C/'publication.json').read_text());brief=json.loads((E/'brief.json').read_text());val=json.loads((C/'native-validation.json').read_text());motion=json.loads((C/'motion-witness-summary.json').read_text());coverage=json.loads((C/'visual-coverage-map.json').read_text())
assert len(pub['rawFrames'])==528 and len(pub['nativeRawFrames'])==528 and len(pub['atlases'])==44
assert len(coverage['all528NativeUsefulPixelCoverage'])==44
assert len(val['captureRecords'])==542
heroes={f:f'candidates/round-01/published/frames/normal/{f}/000.png' for f in ['N','E','S','W']}
previews={'four-view-sheet':'candidates/round-01/four-view-sheet.png','phone':'candidates/round-01/browser/chromium/phone.png','repeated':'candidates/round-01/browser/chromium/repeated.png'}
for clip in brief['delivery']['requiredClips']:
 for f in ['N','E','S','W']:previews[clip['id']+'-'+f]=f'candidates/round-01/sheets/{clip["id"]}-{f}-native.png'
assert set(brief['capture']['previews'])<=set(previews)
used_source=['round-01.blend','round-01-recipe.json','build-round-01.py','build-round-01.log','capture-round-01.py','capture-round-01.log','publish-round-01.py','publish-round-01.log','capture-consumer-round-01.mjs','capture-consumer-round-01.log','vite-round-01.config.mjs','vite-round-01.log','analyze-round-01.py','analyze-round-01.log','handoff-round-01.py','resources/raw-original.blend']
files=sorted([p for p in C.rglob('*') if p.is_file() and p.name not in ['delivery.v1.json','delivery.json','handoff.v1.json','handoff.v1.json.sha256','resources.v1.json']]+[P/n for n in used_source],key=lambda p:str(p))
entries=[]
for p in files:
 assert p.stat().st_size<100_000_000,p
 assert '__pycache__' not in p.parts,p
 entries.append({'path':str(p.relative_to(E)),'sha256':sha(p),'bytes':p.stat().st_size})
save(C/'resources.v1.json',{'asset':'creature-eel','round':1,'files':entries,'portableNativeReplay':'Open source/round-01.blend with Blender5.2.2 and run source/capture-round-01.py; .blend has no external image/library resources.','portableRebuild':'Open source/resources/raw-original.blend and run source/build-round-01.py. Raw original clone SHA is retained; source original remains unchanged.','runtimeDependencies':{'Blender':'5.2.2 LTS d13f752e3b9c','Python':'bundled Python3.12 with Pillow/numpy; paths and exact commands in source logs and recipe','Node':'22.18.0','Playwright':'1.63.0','Vite':'7.3.6','consumerHelpers':'Exact099/570 copies; React resolves from existing workspace runtime, no app/runtime tree copied.'}})
delivery={'asset':'creature-eel','round':1,'status':'candidate immutable handoff; pending ROOT packet and original independent judge','project':'source/round-01.blend','recipeScript':'source/build-round-01.py','recipe':'source/round-01-recipe.json','heroes':heroes,'previews':previews,'rawFrames':pub['rawFrames'],'nativeRawFrames':pub['nativeRawFrames'],'atlases':pub['atlases'],
 'nativeRecords':{'camera':'candidates/round-01/nativeRecords/camera.json','assetRecord':'candidates/round-01/nativeRecords/assetRecord.json','rig':'candidates/round-01/nativeRecords/rig.json','nativeCamera':'candidates/round-01/native-camera.json','catalogObject':'candidates/round-01/nativeRecords/catalog-object.json'},
 'nativeValidation':'candidates/round-01/native-validation.json','nativeCaptureManifest':'candidates/round-01/capture-records.json','resources':entries,'resourceManifest':'candidates/round-01/resources.v1.json','visualCoverage':'candidates/round-01/visual-coverage-map.json','browserRecords':'candidates/round-01/browser-records.json','browserResiduals':'candidates/round-01/browser-comparison.json','motionWitness':'candidates/round-01/motion-witness-summary.json',
 'nativeFrame':[1792,2048],'publishedFrame':[896,1024],'logicalFrame':[448,512],'logicalRoot':[224,352],'nativeCaptureScale':4,'publishedSourceScale':2,'publication':'Uniform whole authored1792x2048canvas LANCZOS896x1024; original6x2atlas5376x2048. No fitting/crop/warp/pixelrepair/perviewcolor or light adjustment.',
 'notes':['Native BODY only; all13 marked2D effects excluded. Rounded continuous body, integrated eye seats, solid curved dimensional fins and native readable smile.','Actual evaluated flexible seven-bone motion repaired by XYZ modes. Caught object X pitch scaled.80 for muzzle clearance; all11IDs/12phases/12fps/order/eightclosures/threeholds retained.','One common35degree camera and symmetric light/material recipe; no floor/groundcast shadow. All528 poses measured and rendered directly from exact editable saved source.','Atlas exactness, allphase closure/hold/attachment/envelope evidence and actual two-mode RAF consumer witness are technical evidence; original judge still decides visual acceptance.','Native useful-pixel sheets contain exact1:1RGBA regions for all528; published hero useful pixels covered separately. Diagnostics crop only review sheets; delivered frames retain complete canvas.'],
 'limits':val['limits'],'frozenInputHashes':frozen}
save(C/'delivery.v1.json',delivery);save(C/'delivery.json',delivery)
handoff={'asset':'creature-eel','round':1,'atUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':'STOP at immutable editor handoff; no selfpacket/selfapproval','project':{'path':'source/round-01.blend','sha256':sha(P/'round-01.blend')},'delivery':{'path':'candidates/round-01/delivery.v1.json','sha256':sha(C/'delivery.v1.json')},'resourceManifest':{'path':'candidates/round-01/resources.v1.json','sha256':sha(C/'resources.v1.json')},'nativeValidation':{'path':'candidates/round-01/native-validation.json','sha256':sha(C/'native-validation.json')},'visualCoverage':{'path':'candidates/round-01/visual-coverage-map.json','sha256':sha(C/'visual-coverage-map.json')},'frozenInputHashes':frozen,'counts':{'nativeRequired':528,'nativeControls':14,'publishedFrames':528,'atlases':44,'nativeUsefulPixelSheets':44,'heroDirections':4,'previewAliases':len(previews),'resourceFiles':len(entries),'browserMotionRecords':len(motion['records'])},'coordinatorNext':'ROOT creates aliases/seals immutable packet; same original judge independently inspects actual candidate pixels/coverage and verdict. No promotion, Git, deploy or device action by editor.'}
save(C/'handoff.v1.json',handoff);h=sha(C/'handoff.v1.json');(C/'handoff.v1.json.sha256').write_text(h+'  handoff.v1.json\n')
for p in files+[C/n for n in ['delivery.v1.json','delivery.json','handoff.v1.json','handoff.v1.json.sha256','resources.v1.json']]:p.chmod(0o444)
print(json.dumps({'handoff':str((C/'handoff.v1.json').relative_to(E)),'sha256':h,'projectSHA256':sha(P/'round-01.blend'),'deliverySHA256':sha(C/'delivery.v1.json'),'counts':handoff['counts']},indent=2),flush=True)
