from pathlib import Path
from PIL import Image,ImageDraw,ImageChops
import numpy as np,json,hashlib,math,ast
H=Path(__file__).resolve().parent;E=H.parent;O=E/'candidates/round-01';P=O/'previews';D=E/'delivery/round-01'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
if (D/'delivery.json').exists():raise RuntimeError('Versioned delivery already exists; retain immutable and create a new version')
pub=json.loads((O/'publication-audit.json').read_text());native=json.loads((O/'native-audit.json').read_text());assembly=json.loads((O/'assembly-audit.json').read_text());consumer=json.loads((O/'consumer/receipt.json').read_text());repeat=json.loads((O/'repeatability/closure-analysis.json').read_text())
assert len(pub['rawFrames'])==52 and len(pub['atlases'])==8
assert assembly['allOriginalGeometryMaterialsHierarchyCameraLightsIdentical'] and assembly['allNeutralResourcesExact']
assert all(x['intentionalSeatInsertion'] for x in assembly['nativeBodyIntersections']+assembly['nativeBodyContainment'])
assert all(x['minimumFiniteSurfaceDistance']>0 for x in assembly['lampFiniteDistances'])
assert all(v['occludedByCandidate']==0 for r in assembly['lampRayVisibility'] for v in r['lenses'].values())
assert consumer['errors']==[] and all(r['nearestAfterResize'] for r in consumer['captures'])
atlasProof=[]
for a in pub['atlases']:
 im=Image.open(E/a['path']).convert('RGBA')
 for i,rect in enumerate(a['rects']):
  r=next(r for r in pub['rawFrames'] if r['clip']==a['clip'] and r['direction']==a['direction'] and r['index']==i);x,y,w,h=rect
  assert im.crop((x,y,x+w,y+h)).tobytes()==Image.open(E/r['path']).convert('RGBA').tobytes()
 atlasProof.append({'clip':a['clip'],'direction':a['direction'],'allWholeFrameRectanglesExact':True,'frames':len(a['rects'])})
 # Complete registered all-four native assembly sheet (no geometry/sprite overlays).
sheet=Image.new('RGB',(1280,410),'#9da9ae')
for j,di in enumerate('NESW'):
 im=Image.open(O/f'assembled/upgraded-dock-ready-{di}.png').convert('RGBA').resize((320,384),Image.Resampling.BOX);sheet.paste(im,(j*320,20),im);ImageDraw.Draw(sheet).text((j*320+8,4),f'{di} · static preliminary main / provisional other gear',fill='#152d38')
sheet.save(P/'assembled-neutral-all4.png')
for di in 'NESW':
 frames=[Image.open(O/f'consumer/captures/phone-{di}-{i+1:02d}.png').convert('RGB') for i in range(12)]
 frames[0].save(P/f'consumer-phone-{di}.webp',save_all=True,append_images=frames[1:],duration=[83,83,84]*4,loop=0,lossless=True)
 sheet=Image.new('RGB',(1170,3376),'#edf1f1')
 for i,im in enumerate(frames):sheet.paste(im,(i%3*390,i//3*844))
 sheet.save(P/f'consumer-phone-every-phase-{di}.png')
motion=[]
for di in 'NESW':
 imgs=[Image.open(O/f'frames/active/{di}/{i:03d}.png').convert('RGBA') for i in range(12)];logical=[im.resize((192,352),Image.Resampling.BOX) for im in imgs]
 motion.append({'direction':di,'uniquePublishedRGBA':len({hashlib.sha256(im.tobytes()).hexdigest() for im in imgs}),'uniqueLogicalRGBA':len({hashlib.sha256(im.tobytes()).hexdigest() for im in logical}),'logicalPixelsChangedPhase3vs9':int(np.any(np.asarray(logical[2])!=np.asarray(logical[8]),axis=2).sum()),'qualification':'Structural motion evidence only; intended-size readability requires independent visual/playback judgment.'})
neutral=next(r for r in native['records'] if r['clip']=='idle' and r['direction']=='S')['worldBounds'];lo=[min(r['canonicalBounds'][0][i] for r in native['continuousSweep']) for i in range(3)];hi=[max(r['canonicalBounds'][1][i] for r in native['continuousSweep']) for i in range(3)]
assert all(neutral[0][i]>=v-1e-6 for i,v in enumerate([-.425,-.275,0])) and all(neutral[1][i]<=v+1e-6 for i,v in enumerate([.425,.25,.4]))
assert lo[2]>=0 and hi[2]<=.55 and all(lo[i]>=-.5 and hi[i]<=.5 for i in [0,1])
checks={'registeredNativeCapture':[768,1408],'publishedFrame':[384,704],'logicalFrame':[192,352],'logicalRoot':[96,248],'publishedRoot':[192,496],'nativeRoot':[384,992],'nativeCaptureScale':4,'publishedSourceScale':2,'filterSize':.5,'publication':'Complete registered native frame BOX reduction; all atlas rectangles byte-equal to corresponding published whole frame.','runtimeFrames':52,'closureOnlyFrames':4,'atlases':8,'atlasProof':atlasProof,'neutralCanonicalBounds':neutral,'frozenNeutralReservationFits':True,'activeSweepCanonicalBounds':[lo,hi],'continuousAnalyticBound':native['continuousAnalyticBound'],'activeFootprintHeightGroundFits':True,'motion':motion,'frame13NativeStateExactAll4':all(r['comparisons'][2]['fullGeometryNormalsUVMaterialTransformsExact'] for r in repeat['records']),'originalClosureNativePixelExact':[r['nativeRGBAEqual'] for r in pub['closure']],'originalClosureLogicalPixelExactAll4':all(r['comparisons'][3]['logicalRGBA']['changedPixels']==0 for r in repeat['records']),'closureQualification':'Raw EEVEE RGB closure variation0..10pixels by1/255; fresh same-source same-pose controls0..15pixels by1/255, unchanged alpha. Exact native state closure proven. Empirical temporal acceptance remains for independent original judge; no raster repair, quality reduction or editor approval.','frozenMainResourceIdentity':True,'exactNeutralCanonicalResourceIdentity':True,'storedNeutralLocalTransformChannelsExact':assembly['allStoredNeutralLocalTransformChannelsExact'],'inverseMountMaxVertexResidual':max(r['maxVertexError'] for r in assembly['inverseMountExtraction']),'finiteSeatArea':assembly['finiteSeat']['areaWorld'],'minimumLampFiniteDistance':min(x['minimumFiniteSurfaceDistance'] for x in assembly['lampFiniteDistances']),'zeroBaselineVisibleLensOcclusionAll4':True,'onlyIntentionalSeatIntersectionAndContainment':True,'mouth':assembly['actualMouth'],'hover':assembly['hover'],'consumerCaptureCount':len(consumer['captures']),'consumerNativeNearestAfterResizeAll':True,'consumerErrors':[],'consumerActualClip':'One actual native assembled upgraded-dock-ready frame1, provisional other gear; own active standalone equipment/eel independent neighbors.','publishedRegistrationNoFit':True}
validation={'asset':'sub-collector-inlet','round':'round-01','status':'complete-evidence-awaiting-independent-visual-and-temporal-review','nativeValidation':'candidates/round-01/native-audit.json','assemblyAudit':'candidates/round-01/assembly-audit.json','publicationAudit':'candidates/round-01/publication-audit.json','repeatabilityAudit':'candidates/round-01/repeatability/closure-analysis.json','consumerAudit':'candidates/round-01/consumer/receipt.json','nativeProject':'source/round-01.blend','nativeProjectSHA256':sha(H/'round-01.blend'),'frozenBriefSHA256':sha(E/'brief.json'),'frozenContractSHA256':sha(E/'inputs/root-native-contract.json'),'checks':checks,'approval':False,'pending':['Root immutable packet seal','Original independent judge review of exact candidate and empirical renderer repeatability','Exact neutral main adoption/final576 native captures and main/family approval','Production/catalog/Godot integration by coordinator']}
write(O/'validation.json',validation)
# Resource closure includes actual source/capture/atlas/replay/consumer files, failed drafts,
# original/frozen technical input bytes and immutable independent criteria. Exclude caches/self manifests.
files=[]
for folder in [E/'source',E/'candidates/round-01',E/'inputs']:
 for p in sorted(folder.rglob('*')):
  if not p.is_file() or '__pycache__' in p.parts or p.name in ['resource-closure.json','evidence-manifest.json']:continue
  assert p.stat().st_size<100_000_000
  files.append({'path':str(p.relative_to(E)),'sha256':sha(p),'bytes':p.stat().st_size})
for rel in ['brief.json','reviews/proposedcriteria.json','reviews/source-contract-proposal.json','reviews/preparation-manifest.json']:
 p=E/rel;files.append({'path':rel,'sha256':sha(p),'bytes':p.stat().st_size})
write(O/'resource-closure.json',{'asset':'sub-collector-inlet','filesRelativeTo':'object','files':files,'externalActiveImages':[],'externalLinkedLibraries':[],'portableRecipe':'source/reproduce-01.py','noUnboundRuntimeDependency':True,'qualification':'Python/Pillow/NumPy, Blender5.2.2 and Node/Playwright are toolchain dependencies; source package versions snapshotted. No remote mutable image or scene library is used by the candidate.'})
delivery={'asset':'sub-collector-inlet','round':'round-01','project':'source/round-01.blend','recipeScript':'source/reproduce-01.py','recipe':'source/round-01-settings.json','validation':'candidates/round-01/validation.json','nativeRecords':{'camera':'candidates/round-01/camera.json','assetRecord':'candidates/round-01/assetRecord.json','rig':'candidates/round-01/rig.json','audit':'candidates/round-01/native-audit.json'},'originalNativeCameraRecord':'inputs/source-camera.json','actualNativeCameraRecord':'candidates/round-01/native-camera.json','nativeCaptureScale':4,'publishedSourceScale':2,'heroes':{di:f'candidates/round-01/frames/idle/{di}/000.png' for di in 'NESW'},'previews':{'four-view-sheet':'candidates/round-01/previews/idle-all4-gray-1x.png','repeated':'candidates/round-01/previews/repeated.png',**{f'active-{di}':f'candidates/round-01/previews/active-{di}.webp' for di in 'NESW'},'all4-logical-playback':'candidates/round-01/previews/all4-logical-playback.webp','assembled-neutral-all4':'candidates/round-01/previews/assembled-neutral-all4.png',**{f'consumer-phone-{di}':f'candidates/round-01/previews/consumer-phone-{di}.webp' for di in 'NESW'}},'rawFrames':pub['rawFrames'],'nativeRawFrames':pub['nativeRawFrames'],'atlases':pub['atlases'],'resources':[x['path'] for x in files]+['candidates/round-01/resource-closure.json'],'publication':'Complete native4x768x1408 to published2x384x704 using BOX; idle1x1 and active6x2 original atlas layout,12fps, closing key13 excluded.','nativeAssembly':'source/round-01-assembled.blend','canonicalNeutralResources':'candidates/round-01/canonical-neutral-resources.json','approval':False,'limitations':validation['pending']+[checks['closureQualification']],'neutralMount':{'translation':[0,-.52,.09],'positiveUniformScale':.4,'rotationZ':0,'idleFrame':1,'canonicalFacing':'S','activeMainMapping':False}}
write(D/'delivery.json',delivery)
evidence={'asset':'sub-collector-inlet','delivery':{'path':'delivery/round-01/delivery.json','sha256':sha(D/'delivery.json')},'source':{'path':'source/round-01.blend','sha256':sha(H/'round-01.blend')},'validation':{'path':'candidates/round-01/validation.json','sha256':sha(O/'validation.json')},'resourceClosure':{'path':'candidates/round-01/resource-closure.json','sha256':sha(O/'resource-closure.json')},'files':files,'approval':False,'next':'Root seals exact candidate; original independent judge reviews. No self-approval.'}
write(D/'evidence-manifest.json',evidence)
print(json.dumps({'delivery':str(D/'delivery.json'),'deliverySHA256':sha(D/'delivery.json'),'sourceSHA256':sha(H/'round-01.blend'),'evidenceSHA256':sha(D/'evidence-manifest.json'),'resourceCount':len(files),'validationSHA256':sha(O/'validation.json'),'closureQualification':checks['closureQualification']},indent=2))
