"""Compute honest technical validation and an editor delivery manifest. No approval or packet seal."""
import json,hashlib,copy,sys
from pathlib import Path
from PIL import Image,ImageChops,ImageStat
sys.dont_write_bytecode=True
S=Path(__file__).resolve().parent;O=S.parent.parent;C=O/'candidates/round-01';D=O/'delivery/round01';D.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2)+'\n')
def rel(p):return p.relative_to(O).as_posix()
native=read(C/'native-validation.json');browser=read(C/'browser-ledger.json');publication=read(C/'publication.json');control=read(C/'control-records.json');cat=read(S/'resources/catalog-object.json');geom=native['geometryMeasurements'];raw=read(C/'raw-records.json');atlas=read(C/'atlas-records.json');pubcam=read(C/'published-camera.json')
replay=[]
for rec in control['captureRecords']:
 p=O/rec['path'];ref=C/'native'/rec['clip']/rec['direction']/f'{rec["index"]:03}.png';im=Image.open(p).convert('RGBA');original=Image.open(ref).convert('RGBA');diff=ImageChops.difference(im,original);replay.append({'control':rel(p),'submittedNative':rel(ref),'decodedRGBAExact':im.tobytes()==original.tobytes(),'absoluteMaxRGBA':[mx for mn,mx in diff.getextrema()],'meanAbsoluteRGBA':ImageStat.Stat(diff).mean,'controlSHA256':sha(p),'submittedSHA256':sha(ref)})
write(C/'control-comparison.json',{'method':'Clean saved-source process recapture; same native camera/filter/seed/material/light settings. Decoded pixels compared honestly, no repair.','records':replay})
closures=[]
for d in 'NESW':
 a=Image.open(C/'native/idle'/d/'000.png').convert('RGBA');b=Image.open(C/'native/idle'/d/'012.png').convert('RGBA');diff=ImageChops.difference(a,b);closures.append({'direction':d,'decodedRGBAExact':a.tobytes()==b.tobytes(),'maxRGBA':[x[1] for x in diff.getextrema()]})
packing=[]
for a in atlas:
 im=Image.open(O/a['path']).convert('RGBA')
 for i,rect in enumerate(a['rects']):
  x,y,w,h=rect;f=Image.open(C/'frames'/a['clip']/a['direction']/f'{i:03}.png').convert('RGBA');packing.append(im.crop((x,y,x+w,y+h)).tobytes()==f.tobytes())
bounds=[[min(g['bounds'][0][i] for g in geom) for i in range(3)],[max(g['bounds'][1][i] for g in geom) for i in range(3)]]
static=[g for g in geom if g['clip']=='static'];idle=[g for g in geom if g['clip']=='idle'];expected={'N':180,'E':90,'S':0,'W':-90}
checks={
 'all52PublishedFrames':len(raw)==52 and {(r['clip'],r['direction'],r['index']) for r in raw}=={(c['id'],d,i) for c in cat['clips'] for d in 'NESW' for i in range(c['frames'])},
 'all56NativeCapturesIncluding4ClosureFrames':len(native['captureRecords'])==56,
 'original8AtlasLayouts':len(atlas)==8 and all(a['rects']==next(c for c in cat['clips'] if c['id']==a['clip'])['directions'][a['direction']]['rects'] for a in atlas),
 'atlasDecodedPixelsExactlyRawFrames':all(packing),
 'staticGeometryWithinHalfCell':all(g['bounds'][0][i]>=-.50001 and g['bounds'][1][i]<=.50001 for g in static for i in [0,1]),
 'animatedGeometryWithinFrozenMargin':all(g['bounds'][0][i]>=-.51401 and g['bounds'][1][i]<=.51401 for g in idle for i in [0,1]),
 'geometryZWithinHeightAllowance':bounds[0][2]>=-1e-5 and bounds[1][2]<=1.45001,
 'every64PointTubeBasalRingEmbeddedAll56Poses':all(g['allTubeBasesEmbedded'] for g in geom),
 'nativeFrame13GeometryExact':all(g['frame1vs13MaxVertexDelta']==0 for g in native['closure']),
 'nativeFrame13DecodedPixelsExact':all(c['decodedRGBAExact'] for c in closures),
 'staticGeometryHoldThrough13Exact':all(g['frame1vs13MaxVertexDelta']==0 for g in native['staticHolds']),
 'actualRootPosesAllCardinals':all(abs(g['rootRotationDegrees']-expected[g['direction']])<1e-4 for g in geom),
 'nativeRootRegistration':all(abs(a-b)<.001 for a,b in zip(native['camera']['calibration']['root'],[384,1152])),
 'nativeCameraMatrixFrozenWithinFloatTolerance':max(abs(a-b) for ra,rb in zip(native['camera']['camera']['worldMatrix'],read(S/'resources/source-camera.json')['camera']['worldMatrix']) for a,b in zip(ra,rb))<1e-5,
 'publishedCameraTruthful2x':pubcam['captureScale']==2 and pubcam['nativeCaptureScale']==4 and pubcam['frame']==[192,384] and pubcam['anchor']==[96,288],
 'noAlphaTouchesFrameEdge':all(r['edgeAlphaMax']==0 for r in publication['records']),
 'noExternalRasterOrLinkedLibraries':not control['fileImages'] and not control['libraries'],
 'nativeManifoldNondegenerateMeshes':all(o['nonManifoldEdges']==0 and o['degenerateFaces']==0 for o in control['nativeTopology']),
 'cleanSavedSourceRecaptureDecodedExact':all(r['decodedRGBAExact'] for r in replay),
 'currentConsumerRenderer570a0d0d':browser['rendererSHA256']=='570a0d0d788ab65252724da1f0ff7d82a086eab1875ba37ed032dac34acf9545',
 'currentSpriteLayout099de618':browser['spriteLayoutSHA256']=='099de61830564dbe0de7e3b85ffbeefcc1b80555098ed499b889b50db6074c65',
 'consumerSmoothingDisabledAfterEveryResize':browser['allIntermediateSmoothingDisabled'],
 'consumerStaticHoldExactAt2Seconds':browser['staticHoldAt2SecondsRGBAExact'],
 'consumerAll4LoopClosureDecodedExact':browser['temporal'][-1]['equalsFirstRGBA'],
 'consumerBrowserNoErrors':not browser['errors'],
 'frozenBriefUnchanged':sha(O/'brief.json')=='4a8804d2921331ff1c6dabe577c4de845e22d12e968a1c8e28b627f3061358f3',
 'frozenNativeContractUnchanged':sha(O/'inputs/root-native-contract.json')=='0543e1f7faaf2bf890b16f829a89ef3e0ccf6c47219c1cb057574548c0abb447',
 'originalAndBackupUnchanged':all(sha(p)=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6' for p in [O/'../../backups/b1765262bfa897ad-sushi-loop-world-library.blend',O/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend'])
}
validation={'asset':'decor-foreground-coral','round':'round-01','status':'native technical evidence; independent visual review pending','allChecksPassed':all(checks.values()),'checks':checks,'nativeValidation':rel(C/'native-validation.json'),'nativeProjectSHA256':sha(S/'round-01.blend'),'recipeSHA256':sha(S/'reproduce.py'),'nativeSourceReplay':'candidates/round-01/control-comparison.json','captureContract':{'logicalFrame':[192,384],'logicalRoot':[96,288],'nativeFrame':[768,1536],'nativeRoot':[384,1152],'nativeCaptureScale':4,'publishedFrame':[384,768],'publishedRoot':[192,576],'publishedCaptureScale':2,'publication':'Whole-frame LANCZOS4xto2x, no pixel repair','cameraElevation':55.00797980144134,'rootConvention':'S0/E90/N180/W-90'},'sweptBounds':bounds,'basalProbeCount':sum(sum(c['probes'] for c in g['contacts']) for g in geom),'minimumBasalEmbedDepth':min(c['minimumEmbedDepth'] for g in geom for c in g['contacts']),'decodedNativeClosure':closures,'rendererSHA256':browser['rendererSHA256'],'spriteLayoutSHA256':browser['spriteLayoutSHA256'],'consumerLedger':rel(C/'browser-ledger.json'),'previewMapping':rel(C/'preview-coverage-mapping.json'),'lightingEvidence':'native-validation.json lights: common overhead +4equal cardinal fills, constant neutral world; no ground plane or raster cards.','notes':['All52published and56nativeframes supplied. Technical checks are separate from aesthetic judgment.','Control recapture differences are retained honestly; a pixel difference is not silently repaired.','Compact preview sheets map exact source pixels to visible panels; full native and consumer files remain bound resources.','Actual interaction host uses unchanged current helper and catalog coral/submarine/eel placements; it is not a full Godot device capture.']}
write(C/'validation.json',validation)
previews={'four-view-sheet':rel(C/'previews/four-view-sheet.png'),'repeated':rel(C/'browser/repeated-phone.png'),**{f'idle-{d}':rel(C/f'previews/idle-{d}.webp') for d in 'NESW'},**{name:rel(C/f'previews/{name}.png') for name in ['native-four-view','native-light-dark','all-motion-phases','consumer-sizes','fractional-phases','actual-context','context-motion','consumer-motion']}}
resources=[]
for base in [S,C]:
 for p in sorted(base.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.name!='packet.json' and p.suffix not in ['.blend1']:
   resources.append({'path':rel(p),'sha256':sha(p),'pathBase':'object-root'})
# Include separate independent initial observations, which predate this source round.
resources.append({'path':'source/initial-observations.json','sha256':sha(O/'source/initial-observations.json'),'pathBase':'object-root'})
delivery={'asset':'decor-foreground-coral','round':'round-01','project':rel(S/'round-01.blend'),'recipeScript':rel(S/'reproduce.py'),'validation':rel(C/'validation.json'),'nativeRecords':{'camera':rel(C/'published-camera.json'),'assetRecord':rel(C/'assetRecord.json'),'rig':rel(C/'rig.json')},'heroes':{d:rel(C/'frames/static'/d/'000.png') for d in 'NESW'},'previews':previews,'rawFrames':raw,'nativeRawFrames':[{k:r[k] for k in ['clip','direction','index','path']} for r in native['captureRecords']],'atlases':atlas,'resources':resources,'pathBase':'object-root','publication':'Native4x -> fullframe Pillow LANCZOS2x; original exact atlas layout, no edits','reviewStatus':'pending original independent judge; editor does not self-approve','resourceClosure':{'base':'object-root','files':len(resources),'description':'Self-contained editable saved blend, minimal bpy-only native recipe, exact camera/catalog/contract inputs, minimal used browser helper+React/context closure and reproducible browser bundle. No copied runtimes.'}}
write(D/'delivery.json',delivery)
# A handoff manifest binds all exact owned source/candidate/delivery bytes, with an explicit base.
files=[]
for base in [O/'source',C,D]:
 for p in sorted(base.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.name!='manifest.json' and p.suffix!='.blend1':files.append({'path':rel(p),'sha256':sha(p),'bytes':p.stat().st_size})
assert all(f['bytes']<100*1024*1024 for f in files)
manifest={'asset':'decor-foreground-coral','round':'round-01','pathBase':'object-root','delivery':{'path':rel(D/'delivery.json'),'sha256':sha(D/'delivery.json')},'project':{'path':rel(S/'round-01.blend'),'sha256':sha(S/'round-01.blend')},'validation':{'path':rel(C/'validation.json'),'sha256':sha(C/'validation.json')},'frozenBriefSHA256':sha(O/'brief.json'),'frozenNativeContractSHA256':sha(O/'inputs/root-native-contract.json'),'files':files,'status':'Immutable editor handoff. Root must seal packet and route original independent judge. No approval inferred.'}
write(D/'manifest.json',manifest)
print(json.dumps({'checks':checks,'allChecksPassed':validation['allChecksPassed'],'deliverySHA256':sha(D/'delivery.json'),'manifestSHA256':sha(D/'manifest.json'),'projectSHA256':sha(S/'round-01.blend'),'files':len(files),'largestFileBytes':max(f['bytes'] for f in files)},indent=2))
