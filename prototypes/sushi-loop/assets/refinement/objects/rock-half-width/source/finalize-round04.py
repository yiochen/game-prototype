"""Bind candidate resources and compatible delivery without sealing or approval."""
import json,hashlib,pathlib,sys,shutil,datetime
from PIL import Image,ImageChops,ImageDraw,ImageFilter,ImageOps,ImageStat
P=pathlib.Path(__file__).resolve().parents[1];O=P/'candidates/round-04'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
# Save exact frozen brief alongside the recipe as a portable archive input, no modification.
assert sha(P/'brief.json')==sha(P/'source/round-01-resources/frozen-brief.json')
# Freeze only actually loaded Pillow modules from publication and this analysis stage.
module_files={}
for q in json.loads((O/'python-runtime-used.json').read_text())['modules']:module_files[q['path']]=q
for name,mod in sys.modules.items():
 f=getattr(mod,'__file__',None)
 if f and '/PIL/' in f:module_files[f]={'module':name,'path':f,'sha256':sha(pathlib.Path(f)),'bytes':pathlib.Path(f).stat().st_size}
python=[]
for f,r in module_files.items():
 src=pathlib.Path(f);rel=f.split('/PIL/',1)[1];dest=P/'source/round-01-resources/python-runtime/PIL'/rel;assert sha(src)==sha(dest),'Immutable shared Python runtime changed';python.append({'module':r['module'],'originalPath':f,'path':str(dest.relative_to(P)),'sha256':sha(dest)})
# Additional actually loaded package version input was read after require.cache closure in capture driver.
package=pathlib.Path('/Users/yiouchen/dev/game-prototype/node_modules/@playwright/test/package.json');dest=P/'source/round-01-resources/node-loaded/@playwright/test/package.json';assert sha(package)==sha(dest),'Immutable shared Node version input changed'
write(O/'runtime-freeze.json',{'pythonModules':python,'playwrightVersionPackage':{'path':str(dest.relative_to(P)),'originalPath':str(package),'sha256':sha(dest)},'policy':'Actual-used library files only. External executables are hashed in consumer/record.json; no browser/application tree copies. Set PYTHONDONTWRITEBYTECODE=1 for every replay. Use the bundled Python path recorded in python-runtime-used.json. The private Pillow snapshot can be selected with PYTHONPATH=source/round-01-resources/python-runtime.'})
analysis=json.loads((O/'comparison-analysis.json').read_text());edge=[]
for d in 'NESW':
 native=Image.open(O/f'joins/native-{d}-published.png').convert('RGBA');ind=Image.open(O/f'consumer/full-chromium-logical128-integer-repeat-{d}.png').convert('RGBA');expected=Image.new('RGBA',ind.size);expected.alpha_composite(native,(1,1));aa=expected.getchannel('A');bb=ind.getchannel('A');delta=ImageChops.difference(aa,bb);points=[(i%ind.width,i//ind.width) for i,v in enumerate(delta.getdata()) if v]
 # A partial alpha pixel is on native outer coverage if it touches fully transparent exterior.
 zero=aa.point(lambda v:255 if v==0 else 0);nearzero=zero.filter(ImageFilter.MaxFilter(3));outer=sum(nearzero.getpixel(p)>0 for p in points)
 edge.append({'direction':d,'alphaDifferencePixels':len(points),'differencesTouchingNativeTransparentExteriorWithin1px':outer,'remaining':len(points)-outer,'alphaDifferenceBounds':delta.getbbox(),'maximumAlphaDifference':delta.getextrema()[1],'nativeOpaqueButConsumerNotOpaque':analysis[d]['nativeOpaqueButConsumerNotOpaque'],'opaqueRGBMax':analysis[d]['maxRGBDifferenceOnMutuallyOpaque']})
write(O/'alpha-residual-analysis.json',{'records':edge,'interpretation':'Retain these actual silhouette precision/partial-coverage differences; no whole-image equality or local defect waiver. Opaque terrain coverage is separately checked. Every native opaque pixel remains opaque in independently composed canonical repeats.'})
# Close seam crops use exact common-canvas coordinates, for inspection only. Art PNGs unchanged.
seams=Image.new('RGB',(4*328,2*328),(219,226,229));dr=ImageDraw.Draw(seams)
for col,d in enumerate('NESW'):
 for row,kind in enumerate(['native','independent']):
  if kind=='native':im=Image.new('RGBA',(898,1282));im.alpha_composite(Image.open(O/f'joins/native-{d}-published.png').convert('RGBA'),(1,1))
  else:im=Image.open(O/f'consumer/full-chromium-logical128-integer-repeat-{d}.png').convert('RGBA')
  box=(281,550,361,700) if d in 'NS' else (409,445,489,595)
  crop=im.crop(box).resize((160,300),Image.Resampling.NEAREST);bg=Image.new('RGBA',crop.size,(122,137,148,255));bg.alpha_composite(crop);seams.paste(bg.convert('RGB'),(col*328+80,row*328+24));dr.text((col*328+5,row*328+5),f'{d} {kind} / exact seam crop x2',fill=(10,20,30))
seams.save(O/'seam-detail.png')
# Exact runtime and capture summary; native and CSS layers are not interchangeable.
consumer=json.loads((O/'consumer/record.json').read_text());runtimes=[]
for r in consumer['runs']:
 runtimes.append({k:r[k] for k in ['id','launchOptions','browserVersion','viewport','DPR','case','screenshot','errors']})
write(O/'consumer-summary.json',{'runs':runtimes,'nativeCanvasVersusCSS':'PNG native canvases are actual paintWorldRaster output. Screenshots include CSS whole-scene filtering at the frozen cell size/phase/pan. Background aliases in record.json map verified identical nativeCanvasSHA256 files; screenshot backgrounds are visibly separate.','limitations':'Source-only review fixture; not complete app/Godot evidence or actor-transit certification. No consumer/helper changes.'})
assert json.loads((P/'source/criteria-acknowledgement-round04.json').read_text())['acknowledgedBeforeConstruction']
# Compact native source measurements from the actual rendered mesh, plus active graph and full fields bound separately.
validation=json.loads((O/'native-validation.json').read_text());checks=validation['checks'];assert all(checks.values());assert all(r['decodedRGBAEqual'] and r['differingPixels']==0 for r in analysis['savedSourceReplay']);assert all(not r['errors'] for r in consumer['runs']);assert len(consumer['runs'])==8
write(O/'validation.json',{'asset':'rock-half-width','round':'round-04','status':'technical evidence complete; visual verdict pending independent judge','nativeValidation':'candidates/round-04/native-validation.json','views':validation['views'],'checks':checks,'sourceReplay':analysis['savedSourceReplay'],'continuity':'See comparison-analysis.json, alpha-residual-analysis.json, native-field-proof.json, actual native/independent repeated.png and seam-detail.png; numeric analysis does not certify visible quality.','registration':'Registered native4x with filter.01; full-frame BOX2x; all source/published frame/anchor/density metadata preserved.','limitations':['Analytic native diffuse illumination is the actual active shader; stored area lights are inactive presentation controls for this material.','Slight native versus independently composed nonopaque outer-coverage differences are retained and measured, with no new opaque holes; no local defect waiver.','Single-view ImageGen target does not establish unseen views. The independent judge must evaluate all cardinal captures, repeat views and declared CSS screenshots.','Geometric parallel-strip ground clearance .66 only; no actor transit claim.','Browser evidence is the exact current consumer in a bounded fixture, not full Godot/app proof.']})
# Resource paths use object root; no approvals or packet sealing performed here.
sourcefiles=[p for p in (P/'source').rglob('*') if p.is_file() and '__pycache__' not in p.parts and ('round04' in p.name or 'round-04' in p.name or 'round-01-resources' in p.parts or p.name in ['initial-observations.json','inspect-original-editor-v1.py','inspect-original-editor-v1.log','actual-original-measurement-editor-v1.json'])]
# This manifest is intentionally finite and is itself bound through delivery resources.
resources=[]
sourcefiles+= [P/'source/round-03.blend',P/'reviews/round-03.json',P/'candidates/round-03/packet.json',P/'candidates/round-03/joins/native-S-published.png']+[P/f'candidates/round-03/frames/static/{d}/000.png' for d in 'NESW']
for p in sorted(sourcefiles):
 assert p.stat().st_size<100_000_000
 resources.append({'path':str(p.relative_to(P)),'sha256':sha(p),'bytes':p.stat().st_size})
write(O/'used-resources.json',{'pathBase':'object root','files':resources,'inputs':['brief.json','inputs/root-native-contract.json','inputs/root-preparation-reconciliation-v1.json','inputs/source-camera.json','inputs/source-assetRecord.json','inputs/source-rig.json','inputs/catalog-object.json','inputs/original.png','inputs/target.png'],'initialEvidencePreserved':True,'portableArchiveAliases':[{'from':'source/round-01-resources/frozen-brief.json','to':'brief.json'},{'from':'source/round-01-resources/sprite-layout.js','to':'../../../../wireframe/sprite-layout.js'},{'from':'source/round-01-resources/world-sprite-raster.js','to':'../../../../wireframe/world-sprite-raster.js'}],'archiveAliasPolicy':'Only in a new isolated archive staging workspace, restore the exact bound helper snapshots to their original relative source paths before browser replay; current capture already checked their actual current originals byte-for-byte. These bytes are fully retained, no external download is needed. Never overwrite production helpers.','excludedExploration':'/tmp/rock-half-width-editor-unsubmitted','recipeReplay':'From the archived object root containing frozen inputs and brief.json: PYTHONDONTWRITEBYTECODE=1 /opt/homebrew/bin/blender -b --factory-startup --python source/reproduce-round04.py. The source/round-01-resources/frozen-brief.json byte alias can be restored to brief.json when preparing a portable archive. Publish with the recorded bundled Python; run replay-round04.py for clean saved-source confirmation; consumer helper copies and actual loaded modules are retained.'})
previews={'four-view-sheet':'candidates/round-04/four-view-sheet.png','repeated':'candidates/round-04/repeated.png','phone':'candidates/round-04/consumer/full-chromium-phone32-portrait.png','style-comparison':'candidates/round-04/style-comparison.png','round-comparison':'candidates/round-04/round-comparison.png','parallel-context':'candidates/round-04/parallel-context.png','seam-detail':'candidates/round-04/seam-detail.png'}
for r in consumer['runs']:
 alias=f"consumer-{r['id']}-{r['case']['id']}"
 if r['screenshot']!=previews['phone']:previews[alias]=r['screenshot']
delivery={'asset':'rock-half-width','round':'round-04','project':'source/round-04.blend','recipeScript':'source/reproduce-round04.py','validation':'candidates/round-04/validation.json','nativeRecords':{'camera':'candidates/round-04/published-camera.json','assetRecord':'candidates/round-04/assetRecord.json','rig':'candidates/round-04/rig.json'},'heroes':{d:f'candidates/round-04/frames/static/{d}/000.png' for d in 'NESW'},'previews':previews,'rawFrames':[{'clip':'static','direction':d,'index':0,'path':f'candidates/round-04/frames/static/{d}/000.png'} for d in 'NESW'],'nativeRawFrames':[{'clip':'static','direction':d,'index':0,'path':f'candidates/round-04/native/static/{d}/000.png'} for d in 'NESW'],'atlases':[{'clip':'static','direction':d,'path':f'candidates/round-04/atlases/static-{d}.png','columns':1,'rows':1,'size':[384,704],'rects':[[0,0,384,704]]} for d in 'NESW'],'resources':resources+[{'path':'candidates/round-04/used-resources.json','sha256':sha(O/'used-resources.json')}],'normalization':{'sourceScale':4,'publishedScale':2,'method':'uniform whole-frame BOX','filterSize':.01,'nativeFrame':[768,1408],'publishedFrame':[384,704]},'scope':'Editor handoff only; original judge approval, root seal/promotion/publication pending.'}
(P/'delivery').mkdir(exist_ok=True);write(P/'delivery/round-04.json',delivery)
write(O/'handoff-manifest.json',{'pathBase':'object root','createdUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'delivery':{'path':'delivery/round-04.json','sha256':sha(P/'delivery/round-04.json')},'project':{'path':'source/round-04.blend','sha256':sha(P/'source/round-04.blend')},'frozenBriefSHA256':sha(P/'brief.json'),'initialObservationsSHA256':sha(P/'source/initial-observations.json'),'fileCount':sum(p.is_file() for p in O.rglob('*'))+len(sourcefiles),'declaredCandidateRenders':4,'declaredPreviews':len(previews),'approval':'none; stop for root seal and original judge'})
print(json.dumps({'delivery':str(P/'delivery/round-04.json'),'deliverySHA256':sha(P/'delivery/round-04.json'),'projectSHA256':sha(P/'source/round-04.blend'),'previews':len(previews),'sourceResources':len(resources),'technicalChecks':checks,'runs':len(runtimes),'alpha':edge}))
