"""Versioned data-only aliases of immutable Samir source/render/native audit bytes.
Does not seal, approve, publish, alter art, or invoke acceptance bypasses.
"""
from pathlib import Path
from collections import Counter
import copy,hashlib,importlib.util,json,math
from PIL import Image
A=Path(__file__).resolve().parent;P=A.parent.parent
OLD=P/'delivery-round01.json';NEW=P/'delivery-round01-import.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return p.relative_to(P).as_posix()
def load(p):return json.loads(p.read_text())
def write_new(p,v):
 assert not p.exists(),f'Versioned output already exists: {p}'
 p.write_text(json.dumps(v,indent=2)+'\n')
assert sha(OLD)=='ffba2b5d19cc738d5a14d88eb5c937bc1e7878b593c34264478623d25f6486c6'
original=load(OLD);delivery=copy.deepcopy(original);oldvalidation=P/original['validation'];mainold=load(oldvalidation)
# Read only original contracts to establish declared frame order; associations come from atlas records.
maincontract={c['id']:c for c in load(P/'inputs/catalog-object.json')['clips']}
runtimecontract=load(P/'inputs/runtime-variants/original-object.json')['clips']
tools=P.parents[1]/'tools'
spec=importlib.util.spec_from_file_location('audit_directions_import_adapter',tools/'audit_directions.py');directions=importlib.util.module_from_spec(spec);spec.loader.exec_module(directions)
# Exact original resource manifest protects previously handed-off art, source and evidence files.
manifest=load(P/'candidates/round-01/resources-manifest.json')['files']
for path,info in manifest.items():assert sha(P/path)==info['sha256'],path
core_before={p:sha(P/p) for scope in [original,original['runtimeVariants']] for p in [scope['project'],*[f['nativeFrame'] for a in scope['atlases'] for f in a['frames']],*[a['path'] for a in scope['atlases']]]}
allchecks={};ledgers={};scalechecks={};inputrefs={rel(OLD):sha(OLD),rel(oldvalidation):sha(oldvalidation)}
for mode,bundle,oldbundle,contract in [('main',delivery,original,maincontract),('runtime',delivery['runtimeVariants'],original['runtimeVariants'],runtimecontract)]:
 records=[];associations={};checked=[]
 for atlas in bundle['atlases']:
  clip,direction=atlas['clip'],atlas['direction'];declared=contract[clip]['frameOrder']
  assert declared==list(range(12))
  assert [f['index'] for f in atlas['frames']]==declared
  assert atlas['fps']==contract[clip]['fps']==12 and atlas['loop'] is contract[clip]['loop']
  assert atlas['columns']==6 and atlas['rows']==2 and atlas['size']==[2304,1280]
  assert sha(P/atlas['path'])==atlas['sha256']
  atlas['frameOrder']=copy.deepcopy(declared)
  with Image.open(P/atlas['path']) as image:
   assert image.mode=='RGBA' and image.size==(2304,1280)
   for frame in atlas['frames']:
    i=frame['index'];path=frame['nativeFrame'];expected=frame['sha256'];assert sha(P/path)==expected
    assert frame['rect']==atlas['rects'][i]
    x,y,w,h=frame['rect']
    with Image.open(P/path) as raw:
     assert raw.mode=='RGBA' and raw.size==(384,640)
     assert image.crop((x,y,x+w,y+h)).tobytes()==raw.tobytes()
    record={'clip':clip,'direction':direction,'index':i,'path':path,'sha256':expected}
    assert (clip,direction,i) not in associations
    records.append(record);associations[clip,direction,i]=record
  checked.append({'clip':clip,'direction':direction,'atlasPath':atlas['path'],'atlasSHA256':atlas['sha256'],'frameOrder':declared,'wholeNativeRGBAFrames':12})
 assert len(records)==(480 if mode=='main' else 96)
 assert set(oldbundle['rawFrames'])=={r['path'] for r in records}
 bundle['rawFrames']=records
 nativepath=P/(original['validation'] if mode=='runtime' else 'candidates/round-01/main/validation-native.json')
 if mode=='runtime':nativepath=P/oldbundle['validation']
 native=load(nativepath);reopenedpath=P/f'candidates/round-01/{mode}/validation-native-reopened.json';reopened=load(reopenedpath)
 assert native['clips']==reopened['clips'] and native['camera']==reopened['camera']
 assert not native['errors'] and not reopened['errors']
 assert reopened['projectSHA256']==sha(P/bundle['project'])
 inputrefs[rel(nativepath)]=sha(nativepath);inputrefs[rel(reopenedpath)]=sha(reopenedpath)
 ledger=[]
 for clip,info in native['clips'].items():
  for sample_index,sample in enumerate(info['samples']):
   direction=sample['direction'];index=sample['frame']-1;frame=associations[clip,direction,index]
   actual=copy.deepcopy(sample['rootMatrix'])
   measured=directions.angle(actual);difference=math.atan2(math.sin(measured-directions.EXPECTED[direction]),math.cos(measured-directions.EXPECTED[direction]));assert abs(difference)<=1e-4
   # Direction and exact scaled root matrix are copied from evaluated audit samples, not filenames/brief.
   ledger.append({'clip':clip,'direction':direction,'index':index,'nativeFrame':sample['frame'],'path':frame['path'],'sha256':frame['sha256'],'actualRootMatrix':actual,'measurementSource':{'path':rel(nativepath),'sha256':sha(nativepath),'jsonPointer':f'/clips/{clip}/samples/{sample_index}/rootMatrix'}})
 assert len(ledger)==len(records)
 assert {(r['clip'],r['direction'],r['index']) for r in ledger}==set(associations)
 ledgers[mode]=ledger
 camerapath=P/bundle['nativeRecords']['camera'];camera=load(camerapath);assetpath=P/bundle['nativeRecords']['assetRecord'];asset=load(assetpath)
 logical=camera['frame'];assert logical==asset['frame']==[192,320]
 measured_native=camera['actualRegisteredCamera']['frame'];assert measured_native==native['camera']['frame']==[384,640]
 measured_scales=[measured_native[i]/logical[i] for i in [0,1]];assert measured_scales==[2,2]
 assert camera['captureScale']==asset['scale']==2
 scalechecks[mode]={'measuredNativeFrame':measured_native,'logicalFrame':logical,'axisScaleRatios':measured_scales,'publishedSourceScale':2,'nativeCaptureScale':2,'cameraRecord':{'path':rel(camerapath),'sha256':sha(camerapath)},'nativeAudit':{'path':rel(nativepath),'sha256':sha(nativepath)},'allWholeFramesVerified':[384,640]}
 inputrefs[rel(camerapath)]=sha(camerapath);inputrefs[rel(assetpath)]=sha(assetpath)
 allchecks[mode]={'explicitFrameRecords':len(records),'atlasRecords':len(checked),'frameAssociations':'Derived solely from existing atlases[].frames nativeFrame/index/sha256; no filename parsing.','atlasPixelOrderUnchanged':True,'atlases':checked,'measuredFacingSamples':dict(Counter(r['direction'] for r in ledger))}
# Explicit native/publication scale aliases are measured from immutable camera/frame evidence.
delivery['runtimeVariants']['publishedSourceScale']=2;delivery['runtimeVariants']['nativeCaptureScale']=2
mainledger=A/'candidate-phases.json';runtimeledger=A/'runtime-native-phases.json'
write_new(mainledger,ledgers['main']);write_new(runtimeledger,ledgers['runtime'])
# Retain every old main summary field/check. New native-facing adapter uses the generic manifest interface.
validation=copy.deepcopy(mainold)
validation['renderManifest']=mainledger.name
validation['importSchemaAdapter']={'kind':'data-only-import-interface','originalDelivery':{'path':rel(OLD),'sha256':sha(OLD)},'preservedValidation':{'path':rel(oldvalidation),'sha256':sha(oldvalidation)},'measuredEvidence':inputrefs,'frameAndAtlasChecks':allchecks,'scaleChecks':scalechecks,'mainRenderManifest':{'path':rel(mainledger),'sha256':sha(mainledger)},'runtimeRenderManifest':{'path':rel(runtimeledger),'sha256':sha(runtimeledger)},'noArtSourceOrPriorEvidenceChanges':True,'approvalOrPublicationPerformed':False}
mainvalidation=A/'validation-import.json';write_new(mainvalidation,validation)
oldruntimevalidation=P/original['runtimeVariants']['validation'];runtimevalidation=copy.deepcopy(load(oldruntimevalidation));runtimevalidation['renderManifest']=runtimeledger.name;runtimevalidation['importSchemaAdapter']={'kind':'data-only-import-interface','preservedValidation':{'path':rel(oldruntimevalidation),'sha256':sha(oldruntimevalidation)},'measuredNativeManifest':{'path':rel(runtimeledger),'sha256':sha(runtimeledger)},'scaleChecks':scalechecks['runtime'],'frameAndAtlasChecks':allchecks['runtime'],'approvalOrPublicationPerformed':False}
runtimevalidationpath=A/'validation-runtime-import.json';write_new(runtimevalidationpath,runtimevalidation)
delivery['validation']=rel(mainvalidation);delivery['runtimeVariants']['validation']=rel(runtimevalidationpath)
# The old delivery and its complete declared resource closure remain present. All new adapters are packet resources.
newresources=[OLD,P/'candidates/round-01/delivery.json',oldvalidation,oldruntimevalidation,mainledger,runtimeledger,mainvalidation,runtimevalidationpath,Path(__file__).resolve()]
for p in newresources:delivery['resources'][rel(p)]=rel(p)
for path in inputrefs:delivery['resources'][path]=path
# Receipt consumers need the metadata adapters and original runtime measured evidence within the same approved bundle.
delivery['runtimeVariants']['resources']={rel(p):rel(p) for p in [runtimeledger,runtimevalidationpath,oldruntimevalidation,P/'candidates/round-01/runtime/validation-native-reopened.json',P/'candidates/round-01/runtime/records/camera.json']}
for oldkey,oldvalue in original['resources'].items():assert delivery['resources'][oldkey]==oldvalue
assert {p:sha(P/p) for p in core_before}==core_before
preservation=A/'immutable-art-preservation.json';write_new(preservation,{'originalDeliverySHA256':sha(OLD),'coreArtifactCount':len(core_before),'coreArtifactSHA256':core_before,'allCoreArtifactBytesUnchanged':True,'oldResourceManifest':{'path':'candidates/round-01/resources-manifest.json','sha256':sha(P/'candidates/round-01/resources-manifest.json'),'verifiedEntries':len(manifest)},'noPacketApprovalOrPromotionInvoked':True})
delivery['resources'][rel(preservation)]=rel(preservation)
delivery['importSchemaAdapter']={'version':1,'dataOnly':True,'originalDelivery':{'path':rel(OLD),'sha256':sha(OLD)},'preservationEvidence':{'path':rel(preservation),'sha256':sha(preservation)},'mainValidation':{'path':rel(mainvalidation),'sha256':sha(mainvalidation)},'runtimeValidation':{'path':rel(runtimevalidationpath),'sha256':sha(runtimevalidationpath)},'measuredNativePhaseLedgers':{'main':{'path':rel(mainledger),'sha256':sha(mainledger),'samples':480},'runtime':{'path':rel(runtimeledger),'sha256':sha(runtimeledger),'samples':96}},'interfaceFilesInspected':[str(tools/name) for name in ['promote_object.py','save_runtime_variant_approval.py','audit_directions.py']]+[str(P.parents[3]/'godot/tools/refined_actor_variants.py')],'note':'Existing exact art/native source/validation hashes preserved; raw record, frame order and scale aliases only. Root must seal this version and obtain normal independent approval.'}
write_new(NEW,delivery)
report={'delivery':{'path':rel(NEW),'sha256':sha(NEW)},'oldDelivery':{'path':rel(OLD),'sha256':sha(OLD)},'adapters':{rel(p):sha(p) for p in [mainvalidation,runtimevalidationpath,mainledger,runtimeledger,preservation,Path(__file__).resolve()]},'rawFrames':{m:c['explicitFrameRecords'] for m,c in allchecks.items()},'atlases':{m:c['atlasRecords'] for m,c in allchecks.items()},'measuredFacingSampleCounts':{m:c['measuredFacingSamples'] for m,c in allchecks.items()},'sourceProjectHashes':{m:sha(P/b['project']) for m,b in [('main',delivery),('runtime',delivery['runtimeVariants'])]},'coreArtifactCount':len(core_before),'oldResourceManifestFilesVerified':len(manifest),'approvalOrPublicationPerformed':False}
write_new(A/'adapter-result.json',report)
print(json.dumps(report,indent=2))
