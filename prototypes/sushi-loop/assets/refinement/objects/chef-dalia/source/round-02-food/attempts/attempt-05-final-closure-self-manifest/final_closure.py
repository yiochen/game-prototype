"""Close unsealed review evidence without changing native sources or runtime pixels."""
from pathlib import Path
from PIL import Image
import hashlib,json,math,subprocess

P=Path(__file__).resolve().parent
BASE=P.parent.parent
OUT=BASE/'candidates/round-02'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def write(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def rel(p):return Path(p).relative_to(BASE).as_posix()
def rgba(p):
 im=Image.open(p);assert im.mode=='RGBA';return im
expected={
 'source/round-02.blend':'0673c6918aa0f8974c7c0e5336719296d3f886f5915ade64e4a75c17290d7678',
 'source/round-01.blend':'6786550a8d05b9d4563c038cd4d3614ce7c189a5a1e40813e2f536ac67c2709c',
 'source/round-02-food/dependencies/approved-body.blend':'6786550a8d05b9d4563c038cd4d3614ce7c189a5a1e40813e2f536ac67c2709c',
 'source/round-02-food/dependencies/dish-salmon.png':'4389d1e6607e6afbfb3cd03594afb4196394b14c5ee6ca6a92fb534cd3b9ebe4',
 'brief-v3-held-food-frozen.json':'d500baed2708cdd42bf5830b8bf373dc9f589292d0c333d5e0e1f5341d005107',
 'delivery.json':'10f4e296e206a558863b2508b2fc6da5c79a06bd3782ff00ed206279daf097da'}
for path,digest in expected.items():assert sha(BASE/path)==digest,path
native=read(OUT/'native-validation.json');assert native['ok'] and native['failures']==[]
assert all(native['strictNativePreservation']['checks'].values())
assert native['all192PhysicalPoseVertexHashesEqual']
assert native['globalDepthWorld']==.6 and native['unchangedSourceDepthAndYawDrivers']
assert native['linkedLibraries']==[] and len(native['images'])==1
assert native['images'][0]['packed'] and native['images'][0]['packedSHA256']==expected['source/round-02-food/dependencies/dish-salmon.png']
assert native['images'][0]['size']==[731,505]
phases=read(OUT/'candidate-phases.json')['frames'];assert len(phases)==192
assert len({(r['clip'],r['direction'],r['index']) for r in phases})==192
for r in phases:
 assert abs(r['rootRotationDegrees']-{'N':180,'E':90,'S':0,'W':-90}[r['direction']])<.0001
 ev=r['diagnosticVisibilityEvaluation']
 assert ev['allMuteStatesRestoredBeforeRender'] and ev['allAuthoredVisibilityRestoredBeforeRender']
controls=read(OUT/'controls-record.json')['records'];assert len(controls)==26
for r in controls:
 assert sha(BASE/r['path'])==r['sha256'] and r['visibilityRestoredAfterDiagnostic']
 if r['mode']=='food-off':
  assert r['preRenderVisibility']['hideRender'] and r['postRenderHideRender']
  assert r['preRenderVisibility']['mutedVisibilityCurves']>0 and r['preRenderVisibility']['allDiagnosticCurvesMuted']
pixel=read(OUT/'pixel-diagnostics.json')
off=[r for r in pixel['controls'] if r.get('mode')=='food-off']
assert len(off)==6
assert all(r['stats']['differentAlphaPixels']==0 and max(r['stats']['maximumRGBAByteDifference'])<=1 for r in off)
assert all(r['stats']['differentPixels']<=12 for r in off)
prior=OUT.parent/'round-01/packet.json';prior_data=read(prior)
for k,v in prior_data['files'].items():assert sha((prior.parent/v['path']).resolve())==v['sha256'],k

browser={
 'kind':'Original editor browser playback observation; no independent style approval',
 'surface':'http://127.0.0.1:4178/prototypes/sushi-loop/assets/refinement/objects/chef-dalia/candidates/round-02/playback.html',
 'browser':'Existing Chrome workspace HTTP review surface, controlled with cua_repl',
 'actions':['Play all from frame00','Read actual media state after playback','Inspect idle/work and hold/load viewport screenshots','Replay load-S using its native video control and observe an in-motion pose','Pause all after inspection'],
 'observations':{
  'all24MediaDecoded':True,'readyState':4,'errors':[],
  'nativeVideoDimensions':[384,640],'servingVideoDimensions':[512,640],
  'durationSeconds':1,'native12LoopingMediaStillPlayingAfterOneSecond':True,
  'fourNativeLoadAndEightServingContextsEndedAtOneSecond':True,
  'loadEndingHasFoodStillHeld':True,'noReleaseOrNewBeltTrajectory':True,
  'northFoodOcclusionPreserved':True,'commonLogicalVideoDisplay':[192,320],
  'lastLoopReadbackCurrentTimesSecondsRange':[.849148,.924208]},
 'media':[{'src':f'playbacks/{c}-{d}.mp4','readyState':4,'durationSeconds':1,'loop':c!='load','endedAtReadback':c=='load','pausedAtReadback':c=='load','width':384,'height':640,'error':None} for c in ['idle','work','hold','load'] for d in ['N','E','S','W']]+[{'src':f'contexts/{k}-load-{d}.mp4','readyState':4,'durationSeconds':1,'loop':False,'endedAtReadback':True,'pausedAtReadback':True,'width':512,'height':640,'error':None} for d in ['N','E','S','W'] for k in ['source','candidate']],
 'browserRecovery':'One Page.getFrameTree timeout after package regeneration; screenshot succeeded on same tab. The completed page was replayed and all24 media states re-read. No approval or safety denial was bypassed.'}
write(OUT/'editor-browser-playback.json',browser)
visual={
 'role':'Original editor final observation; independent original judge verdict pending',
 'sourceProjectSHA256':expected['source/round-02.blend'],
 'frozenBriefSHA256':expected['brief-v3-held-food-frozen.json'],
 'manuallyInspected':{
  'all192IndexedFramesOn48LogicalSheets':{'clips':['idle','work','hold','load'],'directions':['N','E','S','W'],'backgrounds':['light','gray','dark'],'frameIndices':list(range(12))},
  'registeredSourceCandidateSheets':{'clips':['work','hold','load'],'directions':['N','E','S','W'],'frameIndices':[0,5,11]},
  'all12PhoneSheets':{'canvas':[390,844],'display':[192,320],'clips':['work','hold','load'],'directions':['N','E','S','W'],'frameIndices':[5,11]},
  'servingPhaseComparisonSheets':[rel(OUT/'contexts'/f'load-{d}-serving-phase-comparison.png') for d in ['N','E','S','W']],
  'nativeSizeContactContexts':[rel(OUT/'contexts'/f'{c}-contacts.png') for c in ['work','hold','load']],
  'otherViews':['four-view-sheet.png','comparison.png','repeated.png','backgrounds/all-states-facings-light.png','backgrounds/all-states-facings-gray.png','backgrounds/all-states-facings-dark.png'],
  'sixCorrectedRadianceStrips':True,'actualBrowserPlayback':'candidates/round-02/editor-browser-playback.json'},
 'observations':[
  'The canonical731x505 food retains its source-specific semantic support and common full-display width. Native width and alpha-occupied width are distinct; canonical alpha naturally occupies a slightly different width.',
  'S food remains in the approved near-face/chest placement, with plate support above the palm mean as frozen. This is preserved semantic registration, not a claim of literal simultaneous two-palm contact.',
  'N food remains naturally hidden behind native body/hair; W food remains partly occluded; E and S retain the original carrying relation through hold and load.',
  'All twelve indexed phases remain present including authored repeated endpoint poses. Load extends and returns to holding, with no newly invented release.',
  'Full native frame cells, common logical scale, frame roots, direction convention and source timing are preserved. No frame crop, per-view fit, recolor or raster touchup was used.',
  'Corrected food-off comparisons contain4..12 changed pixels, max one RGB byte and identical alpha. Source/candidate food-on differences include exact new artwork, occlusion and transported radiance; these are not described as universal renderer noise.',
  'The initial26 food-off controls were invalid because animated visibility restored food during rendering. They, the first script/log and first comparisons are retained in attempt04. Corrected controls mute only the image-plane hide_render curve during that diagnostic render, log pre/post hidden state, restore visibility/mute states, and never save native sources.'
 ],
 'limits':[
  'Packed salmon is explicitly2D; body and knife are native3D.',
  'The immutable packed image retains a duplicated relative filepath metadata string. Active packed bytes are exact canonical SHA and render without linked libraries; the exact unpacked canonical dependency is separately included under source/round-02-food/dependencies/dish-salmon.png. No immutable source resave was made to change metadata.',
  'Original source near-face hold, N occlusion and returned-holding load semantics are retained as required by frozen brief. No new choreography or physical two-hand contact is claimed.',
  'Technical closure and editor observations do not issue independent visual approval.'
 ]}
write(OUT/'editor-visual-inspection.json',visual)

delivery=read(BASE/'delivery-round-02.json')
raws=delivery['rawFrames'];atlases=delivery['atlases'];assert len(raws)==192 and len(atlases)==16
lookup={(r['clip'],r['direction'],r['index']):r for r in raws}
alpha_bounds=[]
for r in raws:
 path=BASE/r['path'];assert sha(path)==r['sha256']
 im=rgba(path);assert im.size==(384,640)
 box=im.getchannel('A').getbbox();assert box and box[0]>0 and box[1]>0 and box[2]<384 and box[3]<640
 alpha_bounds.append(box)
catalog=read(P/'dependencies/original-catalog-object.json');clips={c['id']:c for c in catalog['clips']}
for r in atlases:
 assert sha(BASE/r['path'])==r['sha256']
 im=rgba(BASE/r['path']);assert im.size==(2304,1280)
 original=clips[r['clip']]['directions'][r['direction']]
 assert r['rects']==original['rects'] and r['columns']==6 and r['rows']==2
 assert r['frameOrder']==list(range(12)) and r['fps']==12 and r['loop']==clips[r['clip']]['loop']
 for i,(x,y,w,h) in enumerate(r['rects']):
  assert [w,h]==[384,640]
  source=rgba(BASE/lookup[r['clip'],r['direction'],i]['path'])
  assert im.crop((x,y,x+w,y+h)).tobytes()==source.tobytes()
preview=read(OUT/'preview-manifest.json');assert len(preview['sheets'])==96
backgrounds={'light':'#f3f0e7','gray':'#8a8d8b','dark':'#242c30'}
for r in preview['sheets']:
 path=BASE/r['path'];assert sha(path)==r['sha256']
 sheet=Image.open(path).convert('RGB');scale=1 if r['display']=='logical' else 2
 fw,fh=192*scale,320*scale;head=24*scale
 for i in range(12):
  source=rgba(BASE/lookup[r['clip'],r['direction'],i]['path'])
  if scale==1:source=source.resize((192,320),Image.Resampling.LANCZOS)
  flat=Image.new('RGBA',source.size,backgrounds[r['background']]);flat.alpha_composite(source);flat=flat.convert('RGB')
  x=i%6*fw;y=i//6*(fh+head)+head
  assert sheet.crop((x,y,x+fw,y+fh)).tobytes()==flat.tobytes()
for r in preview['nativeVideos']+preview['servingContextVideos']:
 assert sha(BASE/r['path'])==r['sha256']
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=width,height,r_frame_rate,nb_read_frames,duration','-of','json',str(BASE/r['path'])]))['streams'][0]
 assert probe['r_frame_rate']=='12/1' and int(probe['nb_read_frames'])==12 and float(probe['duration'])==1
 assert [probe['width'],probe['height']]==([384,640] if r in preview['nativeVideos'] else [512,640])
for d in ['N','E','S','W']:delivery['previews'][f'load-{d}-serving-phase-comparison']=rel(OUT/'contexts'/f'load-{d}-serving-phase-comparison.png')
complete=read(OUT/'complete-validation.json')
complete.update({'editorClosure':'candidates/round-02/editor-closure-validation.json','editorVisualInspection':'candidates/round-02/editor-visual-inspection.json','editorBrowserPlayback':'candidates/round-02/editor-browser-playback.json','resourceHashManifest':'candidates/round-02/final-resource-hashes.json','status':'Food-only native technical and original-editor closure complete; independent original-judge verdict pending'})
write(OUT/'complete-validation.json',complete)
delivery['editorClosure']='candidates/round-02/editor-closure-validation.json'
delivery['notes'].append('Final editor closure: corrected food-off controls and all retained first failure artifacts, browser playback, all192 RGBA cells/96 sheets and resource hashes bound. No independent visual approval.')
resources=delivery['resources']
for tree,prefix in [(BASE/'source','source:'),(OUT,'round:')]:
 for path in tree.rglob('*'):
  if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc' and path.name not in ['packet.json','delivery.snapshot.json','editor-handoff-hashes.json']:
   resources[prefix+path.relative_to(tree).as_posix()]=rel(path)
for n in ['editor-closure-validation.json','final-resource-hashes.json']:resources['round:'+n]=rel(OUT/n)
for key in ['project','recipe','recipeScript','validation']:assert isinstance(delivery[key],str) and (BASE/delivery[key]).is_file()
for v in delivery['heroes'].values():assert isinstance(v,str) and (BASE/v).is_file()
for v in delivery['previews'].values():assert isinstance(v,str) and (BASE/v).is_file()
for v in delivery['nativeRecords'].values():assert isinstance(v,str) and (BASE/v).is_file()
camera=read(BASE/delivery['nativeRecords']['camera']);rig=read(BASE/delivery['nativeRecords']['rig']);asset=read(BASE/delivery['nativeRecords']['assetRecord'])
assert camera['captureScale']==camera['sourceScale']==rig['sourceScale']==asset['sourceScale']==2
assert camera['frame']==[192,320] and camera['anchor']==[96,248]
for k,v in resources.items():
 assert isinstance(v,str) and not Path(v).is_absolute() and '..' not in Path(v).parts
 if Path(v).name not in ['editor-closure-validation.json','final-resource-hashes.json']:assert (BASE/v).is_file(),v
write(BASE/'delivery-round-02.json',delivery)
closure={
 'ok':True,'status':'Original editor technical closure complete; independent original judge pending',
 'sourceSHA256':expected['source/round-02.blend'],'nativeSourceUnchanged':True,
 'frozenBriefSHA256':expected['brief-v3-held-food-frozen.json'],
 'priorSealedPacket':{'path':'candidates/round-01/packet.json','sha256':sha(prior),'boundFileCount':len(prior_data['files']),'allBoundFilesStillMatch':True,'priorDeliverySHA256':expected['delivery.json']},
 'strictNativePreservation':native['strictNativePreservation']['checks'],
 'bodyMeshes':95,'actions':24,'materials':15,'all192PhysicalPoseVertexHashesEqual':True,
 'measuredPhaseLedger':complete['renderManifest'],'globalDepthWorld':.6,'depthYawDriversUnchanged':True,
 'maximumErrors':native['maxErrors'],
 'actualNativeRootDirections':{'N':{'degrees':180,'measuredPhaseCount':48},'E':{'degrees':90,'measuredPhaseCount':48},'S':{'degrees':0,'measuredPhaseCount':48},'W':{'degrees':-90,'measuredPhaseCount':48}},
 'all192VisibilityMuteAndAuthoredStatesRestoredBeforeNativeCapture':True,
 'rawFrameCount':192,'nativeFrame':[384,640],'logicalFrame':[192,320],'logicalRoot':[96,248],'nativeScale':2,
 'all192RGBAHashesVerified':True,'all192UnclippedAlphaBounds':True,
 'atlasCount':16,'all192AtlasCellsEqualNativeRGBA':True,'originalRectsAndFrameOrderAndLoopFlagsPreserved':True,
 'allFrameSheetCount':96,'all1152SheetFramePanelsPixelVerified':True,
 'native12fpsVideoCount':16,'sourceCandidateServing12fpsVideoCount':8,'all24VideoHashesAnd12fps12FramesVerified':True,
 'correctedDiagnosticRenderCount':26,'invalidFirst26ControlsRetained':True,
 'foodOffComparisonObservations':[{'clip':r['clip'],'direction':r['direction'],'index':r['index'],'stats':r['stats']} for r in off],
 'sourceAndCandidateRepeatObservations':[r for r in pixel['controls'] if r['comparison']=='same-source-repeat'],
 'radianceInterpretation':'Food-on changes include exact canonical artwork, occlusion and transported radiance. Food-off comparisons and repeat observations are limited measured controls, never a universal PNG noise allowance.',
 'dependencyClosure':{'packedImageCount':1,'canonicalImageSHA256':expected['source/round-02-food/dependencies/dish-salmon.png'],'linkedLibraries':[],'projectOpensInScene':native['presentation']['scene'],'imageFilepathMetadataCaveat':'Duplicated relative filepath string retained in immutable source. Actual packed bytes and separately bound canonical dependency are exact.'},
 'declaredResourceCount':len(resources),'allActualSourceAndCandidateFilesDeclaredExceptCachesAndSelfHashReceipt':True,
 'resourceManifest':'candidates/round-02/final-resource-hashes.json',
 'visualObservations':'candidates/round-02/editor-visual-inspection.json','browserPlayback':'candidates/round-02/editor-browser-playback.json',
 'selfApprovalIssued':False,'productionEdited':False,'priorSealedEvidenceEdited':False}
write(OUT/'editor-closure-validation.json',closure)
hashrows=[]
for key,path in resources.items():
 assert (BASE/path).is_file(),path
 if path=='candidates/round-02/final-resource-hashes.json':continue
 hashrows.append({'key':key,'path':path,'sha256':sha(BASE/path),'bytes':(BASE/path).stat().st_size})
manifest={'scope':'Every explicit delivery resource except this manifest; coordinator packet separately hash-binds the manifest itself, delivery snapshot and handoff receipt','resourceCount':len(resources),'hashedResourceCount':len(hashrows),'deliveryPath':'delivery-round-02.json','deliverySHA256':sha(BASE/'delivery-round-02.json'),'records':hashrows}
write(OUT/'final-resource-hashes.json',manifest)
for r in hashrows:assert sha(BASE/r['path'])==r['sha256']
declared=set(resources.values())
for tree in [BASE/'source',OUT]:
 for path in tree.rglob('*'):
  if path.is_file() and '__pycache__' not in path.parts and path.suffix!='.pyc' and path.name not in ['packet.json','delivery.snapshot.json','editor-handoff-hashes.json']:assert rel(path) in declared,rel(path)
for path,digest in expected.items():assert sha(BASE/path)==digest,path
receipt={'status':'Original-editor closure complete; writes stopped for coordinator sealing and original judge. No self-approval.',
 'project':'source/round-02.blend','projectSHA256':sha(BASE/'source/round-02.blend'),
 'delivery':'delivery-round-02.json','deliverySHA256':sha(BASE/'delivery-round-02.json'),
 'validation':'candidates/round-02/complete-validation.json','validationSHA256':sha(OUT/'complete-validation.json'),
 'editorClosure':'candidates/round-02/editor-closure-validation.json','editorClosureSHA256':sha(OUT/'editor-closure-validation.json'),
 'resourceHashManifest':'candidates/round-02/final-resource-hashes.json','resourceHashManifestSHA256':sha(OUT/'final-resource-hashes.json'),
 'nativeFrames':192,'atlases':16,'native12fpsClips':16,'allFrameSheets':96,'sourceCandidateContextClips':8,'correctedDiagnosticControls':26,'retainedInvalidDiagnosticControls':26,'allActualResourcesDeclared':len(resources)}
write(OUT/'editor-handoff-hashes.json',receipt)
print(json.dumps(receipt,indent=2))
