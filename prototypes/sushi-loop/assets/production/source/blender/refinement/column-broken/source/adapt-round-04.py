"""Create evidence-only published metadata. Never write approved round03 files."""
from pathlib import Path
from copy import deepcopy
import json,hashlib,io,struct
from PIL import Image
BASE=Path(__file__).resolve().parent.parent;OUT=BASE/'candidates/round-04'
OUT.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
load=lambda p:json.loads((BASE/p).read_text())
def write(p,v):
 p=BASE/p
 if p.exists():raise RuntimeError('Refusing to replace existing evidence: '+str(p))
 p.write_text(json.dumps(v,indent=2)+'\n')
# Snapshot every approved round03 source, capture, preview, metadata, packet and delivery.
frozen=list((BASE/'candidates/round-03').rglob('*'))+[p for p in (BASE/'source').iterdir() if 'round-03' in p.name]
frozen=[p for p in frozen if p.is_file()]
before={str(p.relative_to(BASE)):sha(p) for p in sorted(frozen)}
old=load('delivery.json');nativecam=load('source/round-03-camera.json');nativeasset=load('source/round-03-assetRecord.json');rig=load('source/round-03-rig.json')
packet=load('candidates/round-03/packet.json');review=load('reviews/round-03.json')
reference={'round':3,'packet':'candidates/round-03/packet.json','packetSHA256':sha(BASE/'candidates/round-03/packet.json'),'review':'reviews/round-03.json','reviewSHA256':sha(BASE/'reviews/round-03.json'),'scope':'Prior approval identifies unchanged art only. Round04 metadata adaptation awaits independent review.'}
# Projection/world-space properties remain identical. Only pixel-valued calibration halves.
pubcam=deepcopy(nativecam)
pubcam.update({'captureScale':2,'nativeCaptureScale':4,'nativeResolution':[768,1280],'publishedCaptureScale':2,'publishedSourceScale':2,'publishedResolution':[384,640],'publishedFrame':[384,640],'logicalFrame':[192,320],'logicalRoot':[96,248],'recordRole':'published-scale2-camera-registration','nativeRecord':'source/round-03-camera.json','nativeRecordSHA256':sha(BASE/'source/round-03-camera.json'),'metadataAdaptationRound':4})
pubcam['nativeCalibration']=deepcopy(nativecam['calibration'])
pubcam['calibration']={k:[x*.5 for x in v] for k,v in nativecam['calibration'].items()}
pubcam['calibrationUnits']='published pixels at scale2; logical frame/anchor and world matrices are unchanged'
pubcam['nativeRender']=deepcopy(nativecam['render'])
pubcam['render']={'resolution':[384,640],'stage':'published-raster','sourceNativeResolution':[768,1280],'nativeRenderRecord':'source/round-03-camera.json','sampling':'Pillow LANCZOS full-canvas uniform scale0.5','nativeRerenderedForRound04':False}
for d,v in pubcam['views'].items():
 v['nativePath']=f'candidates/round-03/native-static-{d}.png';v['nativeSHA256']=sha(BASE/v['nativePath']);v['path']=old['heroes'][d];v['sha256']=sha(BASE/v['path']);v['resolution']=[384,640];v['sourceNativeResolution']=[768,1280]
# Keep catalog occupancy/clearance height distinct from measured editable native geometry.
pubasset=deepcopy(nativeasset)
pubasset.update({'scale':2,'captureScale':2,'publishedSourceScale':2,'publishedResolution':[384,640],'nativeCaptureScale':4,'nativeResolution':[768,1280],'height':1.88,'catalogHeight':1.88,'nominalMaximumHeight':1.88,'functionalMaximumHeight':1.88,'measuredNativeHeight':nativeasset['height'],'nativeGeometryHeight':nativeasset['height'],'recordRole':'published-scale2-asset-record','nativeRecord':'source/round-03-assetRecord.json','nativeRecordSHA256':sha(BASE/'source/round-03-assetRecord.json'),'metadataAdaptationRound':4,'heightMeaning':'height/catalogHeight retain the existing nominal functional maximum1.88; measuredNativeHeight records actual unmodified round03 geometry.'})
write(Path('source/round-04-published-camera.json'),pubcam);write(Path('source/round-04-published-assetRecord.json'),pubasset)
# Assert approved native→published sampling entirely in memory, without writing/rerendering art.
sampling={};raw=[]
for d in 'NESW':
 np=BASE/f'candidates/round-03/native-static-{d}.png';pp=BASE/old['heroes'][d];ap=BASE/next(a['path'] for a in old['atlases'] if a['direction']==d)
 ni=Image.open(np).convert('RGBA');pi=Image.open(pp).convert('RGBA');assert ni.size==(768,1280) and pi.size==(384,640)
 sampled=ni.resize((384,640),Image.Resampling.LANCZOS);buf=io.BytesIO();sampled.save(buf,format='PNG')
 sampling[d]={'nativePath':str(np.relative_to(BASE)),'nativeSHA256':sha(np),'publishedPath':str(pp.relative_to(BASE)),'publishedSHA256':sha(pp),'atlasPath':str(ap.relative_to(BASE)),'atlasSHA256':sha(ap),'nativeResolution':list(ni.size),'publishedResolution':list(pi.size),'uniformWholeCanvasScale':.5,'filter':'Pillow LANCZOS','exactApprovedRGBA':sampled.tobytes()==pi.tobytes(),'exactApprovedPNG':hashlib.sha256(buf.getvalue()).hexdigest()==sha(pp),'publishedAtlasExactSameBytes':sha(pp)==sha(ap)}
 raw.append({'clip':'static','sourceClipId':'static','direction':d,'index':0,'nativeFrame':1,'path':old['heroes'][d],'sha256':sha(pp),'size':[384,640],'captureScale':2,'sourceNativeCapture':str(np.relative_to(BASE)),'sourceNativeSHA256':sha(np)})
assert all(v['exactApprovedRGBA'] and v['exactApprovedPNG'] and v['publishedAtlasExactSameBytes'] for v in sampling.values())
priorReplay=load('candidates/round-03/portable-replay.json')
replay={'round':4,'metadataOnly':True,'newNativeRenderPerformed':False,'approvedNativeProject':'source/round-03.blend','approvedNativeProjectSHA256':sha(BASE/'source/round-03.blend'),'nativeReplay':'source/replay-round-03.py','nativeReplaySHA256':sha(BASE/'source/replay-round-03.py'),'nativeReplayProof':'candidates/round-03/portable-replay.json','nativeReplayProofSHA256':sha(BASE/'candidates/round-03/portable-replay.json'),'priorRelocatedAllFourExactRGBA':priorReplay['allFourExactRGBA'],'publishedSamplingVerifiedInMemory':sampling,'fullRecipe':'source/round-04-recipe.py','fullRecipeSHA256':sha(BASE/'source/round-04-recipe.py'),'command':'python source/round-04-recipe.py --blender blender --output /absolute/new-output-directory'}
write(Path('candidates/round-04/replay.json'),replay)
# Normalized published handoff, pointing at exact approved existing art files.
d=deepcopy(old);d.update({'round':4,'status':'metadata-adaptation-ready-for-independent-review','metadataOnly':True,'priorArtReference':reference,'project':'source/round-03.blend','recipe':'source/round-04-recipe.py','nativeRecipe':'source/round-03-recipe.py','validation':'candidates/round-04/validation.json','rawFrames':raw,'nativeRawFrames':deepcopy(old['rawFrames']),'nativeRecords':{'camera':'source/round-04-published-camera.json','assetRecord':'source/round-04-published-assetRecord.json','rig':'source/round-03-rig.json'},'originalNativeRecords':deepcopy(old['nativeRecords']),'capture':{'logicalFrame':[192,320],'logicalRoot':[96,248],'cellSize':128,'captureScale':2,'publishedSourceScale':2,'publishedResolution':[384,640],'nativeCaptureScale':4,'nativeResolution':[768,1280]},'height':1.88,'measuredNativeHeight':nativeasset['height']})
d['replay']={'script':'source/round-04-recipe.py','nativeScript':'source/replay-round-03.py','command':replay['command'],'verification':'candidates/round-04/replay.json','nativeVerification':'candidates/round-03/portable-replay.json'}
d['evidence']=deepcopy(old['evidence']);d['evidence'].update({'round04Audit':'candidates/round-04/audit.json','round04Replay':'candidates/round-04/replay.json','metadataAdaptationRecipe':'source/adapt-round-04.py','approvedArtPacket':'candidates/round-03/packet.json'})
resources=[{'name':'original-native-camera','path':old['nativeRecords']['camera']},{'name':'original-native-assetRecord','path':old['nativeRecords']['assetRecord']},{'name':'original-native-rig','path':old['nativeRecords']['rig']},{'name':'native-capture-metadata','path':'candidates/round-03/native-capture.json'},{'name':'native-replay-script','path':'source/replay-round-03.py'},{'name':'native-replay-proof','path':'candidates/round-03/portable-replay.json'},{'name':'approved-round03-packet','path':'candidates/round-03/packet.json'},{'name':'round04-replay-proof','path':'candidates/round-04/replay.json'},{'name':'round04-full-recipe','path':'source/round-04-recipe.py'}]
resources.extend({'name':'native4-static-'+r['direction'],'path':r['path']} for r in old['rawFrames'])
for r in resources:r['sha256']=sha(BASE/r['path'])
d['resources']=resources
# Compare exact bytes after adaptation, retaining explicit native and published pixel semantics.
after={str(p.relative_to(BASE)):sha(p) for p in sorted(frozen)}
unchanged=before==after
checks={'allRound03FilesUnchanged':unchanged,'exactApprovedBlend':sha(BASE/d['project'])=='33653eace2509deaf25a9fbe3d67a0649038c529a84b04a0790f645aea57295f','worldMatrixUnchanged':pubcam['camera']['worldMatrix']==nativecam['camera']['worldMatrix'],'projectionMatrixUnchanged':pubcam['camera']['projectionMatrix']==nativecam['camera']['projectionMatrix'],'logicalFrameUnchanged':pubcam['frame']==nativecam['frame']==[192,320],'logicalRootUnchanged':pubcam['anchor']==nativecam['anchor']==[96,248],'pixelCalibrationUniformHalf':all(pubcam['calibration'][k]==[v*.5 for v in vals] for k,vals in nativecam['calibration'].items()),'publishedCameraScale2':pubcam['captureScale']==2,'publishedAssetScale2':pubasset['scale']==2,'nativeScale4Explicit':pubcam['nativeCaptureScale']==pubasset['nativeCaptureScale']==4,'publishedRawFrames384x640':all(r['size']==[384,640] for r in raw),'nativeRawFrames768x1280Separate':all(r['size']==[768,1280] for r in d['nativeRawFrames']),'nativeHeightSeparateFromCatalogMaximum':pubasset['height']==1.88 and pubasset['measuredNativeHeight']==1.8424701690673828,'clipsFacingsFootprintSocketsPortsUnchanged':all(pubasset[k]==nativeasset[k] for k in ['clips','directions','footprint','sockets','ports']),'rigExactUnchanged':d['nativeRecords']['rig']==old['nativeRecords']['rig'],'allPublishedSamplingExact':all(v['exactApprovedPNG'] and v['exactApprovedRGBA'] for v in sampling.values()),'heroesAndAtlasesExactUnchanged':d['heroes']==old['heroes'] and d['atlases']==old['atlases'],'allFourRootMatricesUnchanged':all(pubcam['views'][v]['rootMatrix']==nativecam['views'][v]['rootMatrix'] for v in 'NESW'),'priorNativePortableReplayAllFourExactRGBA':priorReplay['allFourExactRGBA']}
assert all(checks.values()),checks
explanation='Round03 native metadata correctly described a scale4 768x1280 Blender capture, but catalog promotion consumes scale2 384x640 source frames. Round04 points published metadata/rawFrames to already approved published2 bytes, halves pixel-valued calibration, retains exact world/projection matrices, logical frame/root and native records, and separates actual mesh height from existing catalog maximum. No model or image was rendered, modified or re-encoded for this round.'
audit={'round':4,'asset':'column-broken','metadataOnly':True,'reason':explanation,'priorArtReference':reference,'checks':checks,'allRound03FilesBefore':before,'allRound03FilesAfter':after,'publishedMetadata':{key:{'path':path,'sha256':sha(BASE/path)} for key,path in d['nativeRecords'].items()},'fourRootMatrices':{v:pubcam['views'][v]['rootMatrix'] for v in 'NESW'},'calibration':{'nativeScale4':nativecam['calibration'],'publishedScale2':pubcam['calibration'],'uniformPixelScale':.5},'height':{'nativeGeometryMeasured':nativeasset['height'],'catalogNominalMaximum':1.88,'functionalMaximum':1.88},'sampling':sampling}
write(Path('candidates/round-04/audit.json'),audit)
validation={'schemaVersion':1,'asset':'column-broken','round':4,'pipeline':'native-3d','metadataOnly':True,'reason':explanation,'priorArtReference':reference,'project':d['project'],'projectSHA256':sha(BASE/d['project']),'sourceAudit':'candidates/round-03/source-audit.json','round04Audit':'candidates/round-04/audit.json','replay':'candidates/round-04/replay.json','checks':checks,'artHashes':{'blend':sha(BASE/d['project']),'native4':{v:sampling[v]['nativeSHA256'] for v in 'NESW'},'published2':{v:sampling[v]['publishedSHA256'] for v in 'NESW'},'atlases':{v:sampling[v]['atlasSHA256'] for v in 'NESW'}},'nativeTechnicalEvidenceUnchanged':'candidates/round-03/validation.json','consumerEvidenceUnchanged':'candidates/round-03/consumer/evidence.json','newIndependentMetadataVerdict':'pending'}
write(Path('candidates/round-04/validation.json'),validation)
write(Path('candidates/round-04/delivery.json'),d);write(Path('delivery-round04.json'),d)
print(json.dumps({'round04Delivery':'delivery-round04.json','projectSHA256':validation['projectSHA256'],'metadataCamera':d['nativeRecords']['camera'],'metadataAssetRecord':d['nativeRecords']['assetRecord'],'checks':checks},indent=2))
