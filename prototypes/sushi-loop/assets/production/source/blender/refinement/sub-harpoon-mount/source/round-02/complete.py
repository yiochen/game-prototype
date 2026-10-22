"""Verify published bytes, retain review surfaces, and prepare versioned handoff.
This script never creates packet/review/approval files or changes native geometry.
"""
from PIL import Image,ImageChops,ImageStat,ImageDraw
import pathlib,json,hashlib,copy,subprocess,shutil
P=pathlib.Path(__file__).resolve().parent;E=P.parent.parent;C=E/'candidates/round-02';D=E/'delivery/v1';D.mkdir(parents=True,exist_ok=True)
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
pub=json.loads((C/'publication.json').read_text());stand=json.loads((C/'standalone-audit.json').read_text());mounted=json.loads((C/'mounted-audit.json').read_text());exact=json.loads((C/'exact-native-surface-audit.json').read_text());consumer=json.loads((C/'consumer/evidence.json').read_text())
# Real registered repeated evidence, whole original complete cells, no alpha fitting.
sheet=Image.new('RGB',(860,510),'#dce1df');dr=ImageDraw.Draw(sheet)
for col,d in enumerate('NESW'):
 dr.text((col*215+8,8),d+' · repeated 3x3,32px cells',fill='#243645')
 # Compose to native grid2x at logical128 then reduce whole scene to32px pitch.
 tile=Image.new('RGBA',(832,1120))
 im=Image.open(C/'published'/f'idle-{d}'/'000.png')
 for y in range(3):
  for x in range(3):tile.alpha_composite(im,(32+x*256,y*256))
 small=tile.resize((208,280),Image.Resampling.LANCZOS);sheet.paste(small,(col*215+3,28),small)
 dr.text((col*215+8,320),'Whole frames share authored roots.',fill='#243645')
path=C/'previews/repeated.png';sheet.save(path);pub['previews']['repeated']=str(path.relative_to(E))
# A single timed all-four sheet provides actual12fps intended-size playback.
timed=C/'previews/timed-all4';timed.mkdir(exist_ok=True)
for i in range(12):
 im=Image.new('RGB',(768,378),'#dce1df');dr=ImageDraw.Draw(im)
 for j,d in enumerate('NESW'):
  dr.text((j*192+8,8),f'{d} source phase{i+1}/12',fill='#243645');fr=Image.open(C/'published'/f'active-{d}'/f'{i:03}.png').resize((192,352),Image.Resampling.LANCZOS);im.paste(fr,(j*192,26),fr)
 im.save(timed/f'{i:03}.png')
subprocess.run(['ffmpeg','-loglevel','error','-y','-framerate','12','-i',str(timed/'%03d.png'),'-frames:v','12','-vf','format=yuv420p','-c:v','libx264','-crf','18',str(C/'previews/all4-12fps.mp4')],check=True)
pub['previews']['playback-all4']=str((C/'previews/all4-12fps.mp4').relative_to(E))
pub['previews']['native-mounted-all4']='candidates/round-02/previews/mounted-all13-S.png'
pub['previews']['phone']='candidates/round-02/consumer/390-gray-S-06.png';pub['previews']['landscape']='candidates/round-02/consumer/1120-gray-S-06.png'
# Decoded RGBA equality distinguishes PNG container metadata from rendered pixels.
replay=json.loads((C/'replay-audit.json').read_text());replayrecords=[]
for r in replay['renders']:
 im=Image.open(E/r['path']).convert('RGBA');orig=Image.open(E/r['original']).convert('RGBA');dif=ImageChops.difference(im,orig)
 replayrecords.append({**r,'exactRGBA':im.tobytes()==orig.tobytes(),'differenceRMS':ImageStat.Stat(dif).rms,'alphaBoundsReplay':im.getbbox(),'alphaBoundsOriginal':orig.getbbox()})
dump(C/'decoded-replay-audit.json',{'method':'All52 independently reopened source replay images compared as decoded RGBA; PNG file metadata may differ while pixels remain equal. No image correction.','renders':replayrecords})
frames={(r['clip'],r['direction'],r['index']):r for r in pub['rawFrames']};atlaschecks=[]
for a in pub['atlases']:
 atlas=Image.open(E/a['path']).convert('RGBA');assert list(atlas.size)==a['size']
 for i,rect in enumerate(a['rects']):
  f=frames[a['clip'],a['direction'],i];x,y,w,h=rect;raw=Image.open(E/f['path']).convert('RGBA');assert atlas.crop((x,y,x+w,y+h)).tobytes()==raw.tobytes()
  native=Image.open(C/'native'/f"{a['clip']}-{a['direction']}"/f'{i:03}.png').convert('RGBA');assert native.resize((384,704),Image.Resampling.BOX).tobytes()==raw.tobytes()
  atlaschecks.append({'clip':a['clip'],'direction':a['direction'],'index':i,'publishedWholeBOXExact':True,'atlasCellExact':True,'alphaBounds':raw.getbbox(),'frameEdgeClear':raw.getbbox()[0]>0 and raw.getbbox()[1]>0 and raw.getbbox()[2]<384 and raw.getbbox()[3]<704})
camera=copy.deepcopy(json.loads((C/'camera-native.json').read_text()));camera['captureScale']=2;camera['calibration']={'root':[192,496],'unitX':[256,0],'unitDepth':[0,256],'unitHeight':[0,-179.2]};camera['originalNativeRecord']='candidates/round-02/camera-native.json';camera['measuredSourceAudit']='candidates/round-02/standalone-audit.json'
dump(D/'camera.json',camera)
asset=copy.deepcopy(json.loads((E/'inputs/source-assetRecord.json').read_text()));asset['scale']=2;asset['artStyle']={'revision':'warm-soft-native-harpoon-round02','lighting':'Centered broad overhead plus four equal cardinal fills and uniform world; no ground receiver','roughness':'Material-specific native enamel, gunmetal and silver','nativeSourceScale':4,'publication':'whole-frame BOX to2x'}
dump(D/'assetRecord.json',asset)
rig={'assetId':'sub-harpoon-mount','fps':12,'source':'source/round-02/project.blend','static':False,'groundRootObject':'harpoon__root','projection':'square-top-front-oblique','footprint':[1,1],'nominalHeight':.55,'clips':{'idle':{'frames':1,'fps':12,'loop':False,'static':True,'firstFrame':1,'lastUniqueFrame':1,'closingKeyFrame':None,'neutralActionSample':1},'active':{'frames':12,'fps':12,'loop':False,'static':False,'firstFrame':1,'lastUniqueFrame':12,'closingKeyFrame':None,'action':'Harpoon exact source nonloop recoil 12 phases','owner':'harpoon__recoil_carriage','nativeCurve':'location.Y','interpolation':'LINEAR','activeDeltaLocalYBySourceFrame':[r['deltaY'] for r in stand['phases']]}},'nativeOwnership':{'movingEmpty':'harpoon__recoil_carriage','movingMeshNames':['harpoon__barrel','harpoon__barrel_rear_collar','harpoon__barrel_top_inlay','harpoon__silver_muzzle','harpoon__bore_recess'],'static':'All other native construction is rooted directly to harpoon__root.','sourceMapping':'Old barrel+muzzle coherent +Y offsets about redesigned neutral geometry, same exact12 source phases.','mainImport':'Only exact neutral local resources; no active-main mapping.'},'armatures':[],'sockets':{},'evidence':{'standalone':'candidates/round-02/standalone-audit.json','all52Replay':'candidates/round-02/decoded-replay-audit.json','mounted':'candidates/round-02/mounted-audit.json','nativeResourceIdentity':'candidates/round-02/canonical-neutral-identity.json'}}
dump(D/'rig.json',rig)
delta_expected=json.loads((E/'inputs/root-native-contract.json').read_text())['nativeMotion']['activeDeltaLocalYBySourceFrame'];delta_actual=[r['deltaY'] for r in stand['phases']]
validation={'asset':'sub-harpoon-mount','status':'native-evidence-complete-pending-independent-judge','approval':False,'nativeValidation':'candidates/round-02/standalone-audit.json','exactSurfaceAudit':'candidates/round-02/exact-native-surface-audit.json','mountedAudit':'candidates/round-02/mounted-audit.json','resourceIdentity':'candidates/round-02/canonical-neutral-identity.json','replayAudit':'candidates/round-02/decoded-replay-audit.json','consumerEvidence':'candidates/round-02/consumer/evidence.json','renders':stand['renders'],'nativeFrame':[768,1408],'publishedFrame':[384,704],'frame':[192,352],'anchor':[96,248],'nativeCaptureScale':4,'publishedSourceScale':2,'fps':12,'camera':camera,'counts':{'nativeStandalone':len(stand['renders']),'nativeReplay':len(replayrecords),'nativeMounted':len(mounted['renders']),'publishedFrames':len(pub['rawFrames']),'atlases':len(pub['atlases']),'consumerScreens':len(consumer['cases'])},'checks':{'allPhasesInLocalReserve':all(r['withinReserve'] for r in stand['phases']),'sourceRecoilMaximumError':max(abs(a-b) for a,b in zip(delta_expected,delta_actual)),'nonloopSourceFrame6Peak':delta_actual[5],'nonloopSourceFrame12Residual':delta_actual[11],'noFrame13':len(delta_actual)==12,'all52ReplaysDecodedRGBAExact':all(r['exactRGBA'] for r in replayrecords),'all52PublishedWholeBOXAndAtlasCellsExact':len(atlaschecks)==52,'allFramesEdgeClear':all(r['frameEdgeClear'] for r in atlaschecks),'finiteBearingActualNativePolygonContained':all(r['fullyContainedByActualEvaluatedNativeSeatPolygon'] and r['intendedCenterInsideBearing'] for r in exact['bearingPolygons']),'onlyIntendedSeatSurfaceIntersections':all(all(r['intendedCoplanarSeat'] for r in phase['nativeTriangleOverlaps']) for phase in mounted['phases']),'canonicalNeutralPersistentResourcesExact':exact['canonicalResourceIdentity']['exactNeutralPersistentResourceIdentity'],'bodyResourcesUnchanged':mounted['bodyResourcesUnchanged'],'mainLocalMatricesUnchanged':mounted['mainLocalMatricesUnchanged'],'mainActionAssignmentsUnchanged':mounted['mainActionAssignmentsUnchanged'],'inverseMountMaximumError':max(r['inverseMountLocalVertexMaxError'] for r in mounted['inverseMountExtraction']),'actualMinimumHullSurfaceClearance':min(r['minimumHullSurfaceDistance'] for r in exact['phases']),'actualMinimumFocalSurfaceClearance':min(r['minimumFocalSurfaceDistance'] for r in exact['phases']),'browserErrors':consumer['errors'],'nearestSamplerReassertedAfterResize':all(c['samplerAfterResize'] is False for case in consumer['cases'] for c in case['cases'])},'publicationChecks':atlaschecks,'mouth':mounted['mouth'],'limitations':['Independent judge approval is pending. No approval is asserted by this editor.','Frozen main body and other gear are preliminary technical context; final main family review remains pending.','Earlier mounted-audit resource flag includes derived matrix_local inverse-parent roundoff. Correct persistent native resource identity is proved separately and is exact; inverse-mounted evaluated vertex error is measured.','Native local geometry is narrower than the literal target composition to honor the finite attachment reservation.','At32px cell pitch the source recoil displacement projects to about1.43pixels; small fasteners are subordinate to barrel/red/gold masses.','Round01 is retained as failed geometry with real foot/hull intersections; it is not the delivered candidate.']}
dump(D/'validation.json',validation)
dump(D/'native-audit.json',{'camera':'delivery/v1/camera.json','assetRecord':'delivery/v1/assetRecord.json','rig':'delivery/v1/rig.json','validation':'delivery/v1/validation.json','nativeAudit':'candidates/round-02/standalone-audit.json','exactSurfaceAudit':'candidates/round-02/exact-native-surface-audit.json','identityAudit':'candidates/round-02/canonical-neutral-identity.json','projectSHA256':sha(P/'project.blend')})
# Explicit complete portable closure includes retained draft files and all inputs read.
resource_paths=[]
for folder in [E/'source',E/'candidates',E/'inputs']:
 for f in folder.rglob('*'):
  if f.is_file() and '__pycache__' not in f.parts and f.name not in ['packet.json','delivery.snapshot.json']:
   assert f.stat().st_size<100_000_000,f
   resource_paths.append(f)
for f in [E/'brief.json',E/'reviews/initial.json',E/'reviews/proposedcriteria.json',E/'reviews/source-contract-proposal.json',E/'reviews/preparation-review.json']:
 resource_paths.append(f)
for f in (E/'reviews/preparation').rglob('*'):
 if f.is_file() and '__pycache__' not in f.parts:resource_paths.append(f)
resource_paths += [D/n for n in ['camera.json','assetRecord.json','rig.json','validation.json','native-audit.json']]
resources=[{'path':str(f.relative_to(E)),'sha256':sha(f)} for f in sorted(set(resource_paths))]
delivery={'asset':'sub-harpoon-mount','version':1,'candidateRound':'round-02','status':'complete-native-handoff-awaiting-root-seal-and-independent-judge','project':'source/round-02/project.blend','recipeScript':'source/round-02/build.py','recipe':'source/round-02/settings.json','captureRecipeScript':'source/round-02/evidence.py','validation':'delivery/v1/validation.json','nativeRecords':{'camera':'delivery/v1/camera.json','assetRecord':'delivery/v1/assetRecord.json','rig':'delivery/v1/rig.json','audit':'delivery/v1/native-audit.json'},'heroes':{d:f'candidates/round-02/published/idle-{d}/000.png' for d in 'NESW'},'previews':pub['previews'],'rawFrames':pub['rawFrames'],'nativeRawFrames':pub['nativeRawFrames'],'atlases':pub['atlases'],'resources':resources,'publishedSourceScale':2,'nativeCaptureScale':4,'mainAdoption':{'canonicalNeutralResourceFingerprint':exact['canonicalResourceIdentity']['canonicalSHA256'],'neutralResources':'candidates/round-02/canonical-neutral-persistent-resources.json','translation':[.31,-.24,.5685],'positiveUniformScale':.35,'rotationZ':0,'clip':'idle','mainActions':'unchanged; no active mapping','frozenMainSHA256':'c8462a4072c8ce12f2afcc6907a02d705dcd7df6858f7d790bb2a1dcc5d7fb0e'},'approval':False,'limitations':validation['limitations']}
dump(D/'delivery.json',delivery)
manifest={'asset':'sub-harpoon-mount','round':'round-02','project':{'path':delivery['project'],'sha256':sha(E/delivery['project'])},'delivery':{'path':'delivery/v1/delivery.json','sha256':sha(D/'delivery.json')},'validation':{'path':'delivery/v1/validation.json','sha256':sha(D/'validation.json')},'canonicalNeutralResourceSHA256':exact['canonicalResourceIdentity']['canonicalSHA256'],'resourceCount':len(resources),'resources':resources,'approval':False,'nextStep':'Root copies this exact versioned delivery JSON to the root-owned filename accepted by seal_object, seals exact candidate, and original independent judge reviews. No helper delivery.snapshot.json precreated.'}
dump(D/'handoff-manifest.json',manifest)
print(json.dumps({'handoff':'delivery/v1/delivery.json','projectSHA256':manifest['project']['sha256'],'deliverySHA256':manifest['delivery']['sha256'],'validationSHA256':manifest['validation']['sha256'],'handoffManifestSHA256':sha(D/'handoff-manifest.json'),'resourceCount':len(resources),'checks':validation['checks']},indent=2))
