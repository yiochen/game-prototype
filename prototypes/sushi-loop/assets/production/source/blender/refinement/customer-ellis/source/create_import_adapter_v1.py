"""Data-only import adapter. Never edits native art or the original handoff."""
from pathlib import Path
from PIL import Image
import copy, hashlib, importlib.util, json, math, os, sys, tempfile
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;RUN=OBJ.parents[1];PROTOTYPE=RUN.parents[1]
OUT=OBJ/'candidates/round-02/import-adapter-v1'
EXPECTED_ORIGINAL='f3eaa0ca1f752043b3b97f2a8935ac5e52316bb7d6fd9e369e26c21abda2db50'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def relative(p):return os.path.relpath(Path(p).resolve(),OBJ.resolve())
def record(p,role):return {'path':relative(p),'sha256':sha(p),'role':role}
def write_new(p,value):
 p=Path(p);content=json.dumps(value,indent=2)+'\n'
 if p.exists():
  assert p.read_bytes()==content.encode(),f'Preserve differing existing adapter file: {p}'
  return
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
def future_record(p,value,role):return {'path':relative(p),'sha256':hashlib.sha256((json.dumps(value,indent=2)+'\n').encode()).hexdigest(),'role':role}
def semantic_compositor(evidence):
 tree=evidence['compositorTrees'][evidence['activeCompositorTree']];nodes=[]
 ui={'location','location_absolute','width','height','dimensions','name','label','select','show_options','show_preview','hide','use_custom_color','color','color_tag','warning_propagation','show_texture'}
 for node in tree['nodes']:
  n={k:copy.deepcopy(v) for k,v in node.items() if k not in ['properties','sceneReference']}
  n['properties']={k:v for k,v in node['properties'].items() if k not in ui and not k.startswith('bl_')}
  if 'sceneReference' in node:n['sceneReference']='<captured scene>' if node['sceneReference']==evidence['scene'] else node['sceneReference']
  nodes.append(n)
 return {'nodes':nodes,'links':tree['links'],'renderCompositingSettings':evidence['renderCompositingSettings'],'renderSettings':evidence['renderSettings']}
originalPath=OBJ/'delivery.round-02.json';assert sha(originalPath)==EXPECTED_ORIGINAL
original=read(originalPath);delivery=copy.deepcopy(original)
unchanged={r['path']:r['sha256'] for r in original['resources']}
assert all(sha(OBJ/p)==h for p,h in unchanged.items()),'Original resource changed before adapter'
frozenBrief=read(HERE/'resources/frozen-brief.json');assert sha(HERE/'resources/frozen-brief.json')==original['frozenInputs']['briefSHA256']
mainMeta={r['id']:r for r in frozenBrief['delivery']['requiredClips']}
runtimeContractPath=OBJ/'inputs/runtime-variants/original-object.json';runtimeContract=read(runtimeContractPath);runtimeMeta=runtimeContract['clips']
assert runtimeContract['sourceScale']==2 and set(runtimeMeta)=={'eat-salmon','seated-wait-empty'}
rects=[[i%6*384,i//6*640,384,640] for i in range(12)]
modeData={};atlasChecks=[];cameraChecks={};phaseRows=[];pendingAliases=[];compositorEvidence={};compositorSemantics={}
for mode,bundle,metadata in [('main',delivery,mainMeta),('runtime',delivery['runtimeVariants'],runtimeMeta)]:
 auditPath=OBJ/'candidates/round-02'/f'{mode}-native-audit.json';audit=read(auditPath);modeData[mode]={'auditPath':auditPath,'audit':audit}
 frames={(r['clip'],r['direction'],r['index']):r for r in bundle['rawFrames']}
 expected={(clip,d,i) for clip in metadata for d in 'NESW' for i in range(12)}
 assert len(frames)==len(bundle['rawFrames'])==len(expected) and set(frames)==expected
 for atlas in bundle['atlases']:
  meta=metadata[atlas['clip']]
  assert meta['frames']==12 and meta['fps']==12 and meta['frameOrder']==list(range(12))
  assert atlas['columns']==6 and atlas['rows']==2 and atlas['size']==[2304,1280] and atlas['rects']==rects
  assert sha(OBJ/atlas['path'])==atlas['sha256']
  with Image.open(OBJ/atlas['path']) as im:
   assert im.mode=='RGBA' and im.size==(2304,1280)
   for i,(x,y,w,h) in enumerate(rects):
    raw=frames[atlas['clip'],atlas['direction'],i];assert sha(OBJ/raw['path'])==raw['sha256']
    with Image.open(OBJ/raw['path']) as cell:assert cell.mode=='RGBA' and cell.size==(384,640) and im.crop((x,y,x+w,y+h)).tobytes()==cell.tobytes()
  atlas.update(fps=meta['fps'],loop=meta['loop'],frameOrder=copy.deepcopy(meta['frameOrder']))
  atlasChecks.append({'mode':mode,'clip':atlas['clip'],'direction':atlas['direction'],'path':atlas['path'],'sha256':atlas['sha256'],'fps':atlas['fps'],'loop':atlas['loop'],'frameOrder':atlas['frameOrder'],'orderedWholeCellsMatch':True})
 originalNativeRecords=copy.deepcopy(bundle['nativeRecords']);camera=read(OBJ/bundle['nativeRecords']['camera']);asset=read(OBJ/bundle['nativeRecords']['assetRecord']);measured=audit['camera']
 assert camera['frame']==measured['logicalFrame']==[192,320] and camera['anchor']==measured['logicalRoot']==[96,248]
 assert camera['captureScale']==measured['captureScale']==asset['scale']==2 and measured['resolution']==[384,640]
 assert camera['camera']['worldMatrix']==measured['matrix'] and camera['camera']['orthoScale']==measured['orthoScale'] and camera['camera']['shift']==measured['shift']
 assert camera['artStyle']==asset['artStyle'] and camera['nativeProjectSHA256']==audit['projectSHA256']==sha(OBJ/bundle['project'])
 compositorPath=OUT/f'compositor-{mode}.json';compositor=read(compositorPath)
 assert compositor['sourceSHA256']==audit['projectSHA256'] and compositor['sceneUseNodes']==audit['renderSettings']['compositor']==True and compositor['renderCompositingSettings']['use_compositing']==True
 compositorSemantics[mode]=semantic_compositor(compositor)
 tree=compositor['compositorTrees'][compositor['activeCompositorTree']];mathNodes=[n for n in tree['nodes'] if n['type']=='ShaderNodeMath']
 assert len(mathNodes)==3 and all(n['properties']['operation']=='MULTIPLY_ADD' and n['properties']['use_clamp'] and not n['mute'] for n in mathNodes)
 gain=mathNodes[0]['inputs'][1]['defaultValue'];offset=mathNodes[0]['inputs'][2]['defaultValue']
 assert all(n['inputs'][1]['defaultValue']==gain and n['inputs'][2]['defaultValue']==offset for n in mathNodes)
 conversions=[n for n in tree['nodes'] if n['type']=='CompositorNodeConvertColorSpace']
 assert [(n['properties']['from_color_space'],n['properties']['to_color_space']) for n in conversions]==[('scene_linear','sRGB'),('sRGB','scene_linear')]
 assert all(not n['mute'] for n in tree['nodes']) and all(l['valid'] and not l['muted'] for l in tree['links'])
 measuredStyle={**camera['artStyle'],'compositor':True,'contrast':gain,'contrastOffset':offset,'contrastSpace':'sRGB','compositorRGBOperation':'clamp(gain * channel + offset), straight alpha; convert back to scene_linear; restore premultiplied alpha'}
 camera['artStyle']=copy.deepcopy(measuredStyle);asset['artStyle']=copy.deepcopy(measuredStyle)
 for kind,value in [('camera',camera),('assetRecord',asset)]:
  value['importMetadataAdapter']={'version':1,'kind':'measured-style-metadata-correction-only','original':record(OBJ/originalNativeRecords[kind],'unchanged-original-native-record'),'nativeCompositorEvidence':record(compositorPath,'read-only-native-compositor-evidence'),'change':'Correct stale compositor=false to measured active=true, and expose the measured sRGB RGB gain/offset/clamp. All other art, source and capture values remain unchanged.'}
  path=OUT/f'{mode}-{kind}.json';pendingAliases.append((path,value));bundle['nativeRecords'][kind]=relative(path)
 compositorEvidence[mode]=record(compositorPath,'actual-native-compositor-nodes-and-settings')
 lights=audit['lights'];assert len(lights)==5
 overhead=[l for l in lights if 'overhead' in l['name']];fills=[l for l in lights if 'equal fill' in l['name']]
 assert len(overhead)==1 and overhead[0]['energy']==170 and abs(overhead[0]['size']-4.2)<1e-5
 assert len(fills)==4 and all(l['energy']==95 and l['size']==4 and abs(l['location'][2]-2.2)<1e-5 and abs(math.hypot(*l['location'][:2])-3)<1e-5 for l in fills)
 cameraChecks[mode]={'camera':future_record(OBJ/bundle['nativeRecords']['camera'],camera,'actual-native-camera-metadata-alias'),'assetRecord':future_record(OBJ/bundle['nativeRecords']['assetRecord'],asset,'current-native-asset-record-alias'),'originalNativeRecords':originalNativeRecords,'nativeAudit':record(auditPath,'measured-native-phases'),'logicalFrame':camera['frame'],'anchor':camera['anchor'],'nativeFrame':measured['resolution'],'nativeCaptureScale':2,'publishedSourceScale':2,'cameraMatchesMeasuredMatrix':True,'assetArtStyleMatchesCamera':True,'artStyleMatchesMeasuredLightRigAndCompositor':True,'artStyle':camera['artStyle']}
 sourceToCatalog={meta.get('sourceClipId',clip):clip for clip,meta in metadata.items()}
 for sampleIndex,sample in enumerate(audit['samples']):
  clip=sourceToCatalog[sample['clip']];direction=sample['direction'];index=sample['frame']-1
  raw=frames[clip,direction,index];assert sample['render']==raw['path'] and sample['renderSHA256']==raw['sha256']
  assert len(sample['rootMatrix'])==4 and all(len(row)==4 for row in sample['rootMatrix'])
  phaseRows.append({'mode':mode,'clip':clip,'sourceClipId':sample['clip'],'direction':direction,'index':index,'sourceFrame':sample['frame'],'rootMatrix':copy.deepcopy(sample['rootMatrix']),'render':raw['path'],'renderSHA256':raw['sha256'],'measuredAudit':relative(auditPath),'measuredAuditSHA256':sha(auditPath),'sampleIndex':sampleIndex})
 assert sum(r['mode']==mode for r in phaseRows)==len(expected)
assert len(phaseRows)==576 and len(atlasChecks)==48
assert compositorSemantics['main']==compositorSemantics['runtime'],'Main/runtime compositor or capture setup differs'
for path,value in pendingAliases:write_new(path,value)
ledgerPath=OUT/'phase-ledger.json';validationPath=OUT/'validation-v2.json';checksPath=OUT/'consumer-checks.json'
ledger={'asset':'customer-ellis','adapterVersion':1,'kind':'translation-of-existing-measured-native-phases','interpretation':'Directions and root matrices copied verbatim from actual native audits; no rotation inferred from filenames, expected cardinals or brief. Catalog clip aliases only follow frozen sourceClipId metadata.','sources':{mode:record(d['auditPath'],'original-measured-native-audit') for mode,d in modeData.items()},'renders':phaseRows}
write_new(ledgerPath,ledger)
oldValidationPath=OBJ/original['validation'];validation=copy.deepcopy(read(oldValidationPath))
# The consumer reserves nativeFrames for iterable measured phase records. Keep
# the original summary count under an unambiguous count key in this adapter.
validation['nativeFrameCount']=validation.pop('nativeFrames')
foodMapping=read(HERE/'resources/frozen-food-mappings.json');canonical=[]
for food in ['dish-cucumber','dish-salmon']:
 p=Path(foodMapping[food]['canonicalTexture']['path']);assert p.is_file() and sha(p)==foodMapping[food]['canonicalTexture']['sha256']==sha(HERE/'resources'/f'{food}.png')
 canonical.append(record(p,'exact-approved-canonical-food'))
validation.update(adapterVersion=1,adapterValidationSchemaRevision=2,adapterKind='data-only-catalog-and-runtime-import-interface',originalDelivery=record(originalPath,'immutable-original-delivery'),originalValidation=record(oldValidationPath,'immutable-original-validation'),previousAdapterValidation=record(OUT/'validation.json','retained-interface-preflight-count-key-collision'),renderManifest='phase-ledger.json',renderManifestSHA256=sha(ledgerPath),measuredPhaseRecords=576,atlasImportMetadata=atlasChecks,nativeRecordCompatibility=cameraChecks,canonicalFoodResources=canonical,lighting=cameraChecks['main']['artStyle']['lighting'],compositorEvidence=compositorEvidence,mainRuntimeCompositorSemanticAgreement=True,compositorSemanticSHA256=hashlib.sha256(json.dumps(compositorSemantics['main'],sort_keys=True).encode()).hexdigest())
write_new(validationPath,validation)
# Exercise the actual read-only direction consumer using a temporary packet
# fixture. This creates no candidate packet, seal, approval or production write.
spec=importlib.util.spec_from_file_location('ellis_direction_adapter_check',RUN/'tools/audit_directions.py');consumer=importlib.util.module_from_spec(spec);spec.loader.exec_module(consumer)
with tempfile.TemporaryDirectory(prefix='ellis-direction-interface-') as temp:
 fake=Path(temp)/'customer-ellis';packetBase=fake/'candidates/interface-test';packetBase.mkdir(parents=True)
 packet={'capture':{'views':['N','E','S','W']},'files':{'nativeValidation':{'path':os.path.relpath(validationPath.resolve(),packetBase.resolve()),'sha256':sha(validationPath)},'candidateResource:import-phase-ledger':{'path':os.path.relpath(ledgerPath.resolve(),packetBase.resolve()),'sha256':sha(ledgerPath)}}}
 (packetBase/'packet.json').write_text(json.dumps(packet));directionResult=consumer.audit(fake,'interface-test')
assert directionResult['sampleCounts']=={d:144 for d in 'NESW'}
checks={'asset':'customer-ellis','adapterVersion':1,'dataOnly':True,'originalDeliverySHA256':EXPECTED_ORIGINAL,'nativeSourcesAndAllOriginalResourcesUnchanged':True,'originalResourceCount':len(unchanged),'nativeFramesVerified':576,'atlasesVerified':48,'orderedWholeNativeCellsUnchanged':True,'actualDirectionConsumer':directionResult,'directionConsumerTestMethod':'Temporary packet fixture only; actual candidate unsealed.','nativeRecords':cameraChecks,'compositorEvidence':compositorEvidence,'mainRuntimeCompositorSemanticAgreement':True,'measuredCompositorGrade':{'gain':gain,'offset':offset,'space':'sRGB','clamp':True},'mainLoopFlags':{clip:meta['loop'] for clip,meta in mainMeta.items()},'runtimeLoopFlags':{clip:meta['loop'] for clip,meta in runtimeMeta.items()},'consumerSources':{str(p.relative_to(PROTOTYPE)):sha(p) for p in [RUN/'preparation/DELIVERY-CONTRACT.md',RUN/'tools/promote_object.py',RUN/'tools/save_runtime_variant_approval.py',RUN/'tools/audit_directions.py',PROTOTYPE/'godot/tools/refined_actor_variants.py']},'limitations':['Approval-gated promotion/runtime receipt/Godot import are not run before the independent review and exact main promotion. Only their data interfaces and whole-cell/timing requirements are checked here.','No source/model/material/camera/action/PNG changes or rerendering. Original technical validation remains unchanged and bound.','Original camera/asset style metadata incorrectly said compositor=false; new aliases expose the actual active source grade. No claim of an ungraded native render is made.']}
write_new(checksPath,checks)
delivery['validation']=relative(validationPath);delivery['status']='complete native handoff with separate import metadata adapter; original independent review pending'
delivery['importAdapter']={'version':1,'originalDelivery':record(originalPath,'immutable-original-delivery'),'originalValidation':record(oldValidationPath,'immutable-original-validation'),'phaseLedger':record(ledgerPath,'measured-direction-translation'),'consumerChecks':record(checksPath,'read-only-consumer-interface-checks'),'noArtChange':True}
bundle=delivery['runtimeVariants'];bundle.update(recipeScript=delivery['recipeScript'],validation=relative(validationPath),publishedSourceScale=2,nativeCaptureScale=2,previews={f'{clip}-{d}':delivery['previews'][f'{clip}-{d}'] for clip in runtimeMeta for d in 'NESW'})
runtimeDeps=[OBJ/bundle['recipeScript'],HERE/'build_round02.py',HERE/'resources/native_actions.py',HERE/'resources/runtime-rig.json',HERE/'resources/original-runtime.blend',HERE/'resources/frozen-brief.json',HERE/'resources/frozen-food-mappings.json',HERE/'resources/hair-height-envelope.json',HERE/'resources/dish-salmon.png',oldValidationPath,ledgerPath,validationPath,checksPath,modeData['main']['auditPath'],modeData['runtime']['auditPath'],OBJ/'candidates/round-02/main-surface-audit.json',OBJ/'candidates/round-02/runtime-surface-audit.json',runtimeContractPath]+[OBJ/p for p in bundle['previews'].values()]+[OUT/f'compositor-{mode}.json' for mode in ['main','runtime']]+[path for path,value in pendingAliases]
bundle['resources']=[record(p,'runtime-native-reproduction-or-evidence') for p in runtimeDeps]
resourceMap={r['path']:r for r in delivery['resources']}
extras=[record(p,'import-metadata-adapter') for p in [Path(__file__),HERE/'inspect_compositor_import_v1.py',originalPath,oldValidationPath,OUT/'validation.json',ledgerPath,validationPath,checksPath,runtimeContractPath]]+canonical+bundle['resources']
for r in extras:
 if r['path'] in resourceMap:assert resourceMap[r['path']]['sha256']==r['sha256']
 else:resourceMap[r['path']]=r
delivery['resources']=list(resourceMap.values());delivery['counts']['boundResourceFiles']=len(delivery['resources'])
failed=[r for r in delivery['resources'] if 'draft-01-hand-weights' in r['path']]
actualFailed=[f for folder in [HERE/'draft-01-hand-weights',OBJ/'candidates/draft-01-hand-weights'] for f in folder.rglob('*') if f.is_file()]
assert len(failed)==len(actualFailed)==792 and {r['path'] for r in failed}=={relative(f) for f in actualFailed}
assert len(bundle['rawFrames'])==96 and len(bundle['atlases'])==8
assert all(sha(OBJ/r['path'])==r['sha256'] for r in delivery['resources'])
assert all(sha(OBJ/p)==h for p,h in unchanged.items()) and sha(originalPath)==EXPECTED_ORIGINAL
destination=OBJ/'delivery.round-02-import.json';write_new(destination,delivery)
print(json.dumps({'delivery':record(destination,'import-adapter-delivery'),'validation':record(validationPath,'new-validation-adapter'),'phaseLedger':record(ledgerPath,'new-measured-phase-ledger'),'consumerChecks':record(checksPath,'new-consumer-checks'),'originalDeliverySHA256':sha(originalPath),'resources':len(delivery['resources']),'failedDraftFilesBound':len(failed),'measuredPhases':len(phaseRows),'directionSampleCounts':directionResult['sampleCounts']},indent=2))
