"""Measured native contract and packet-ready delivery adapter; no art changes."""
import json,pathlib,hashlib,math
from PIL import Image,ImageChops
P=pathlib.Path(__file__).resolve().parent;OBJ=P.parent;OUT=OBJ/'candidates/round-02'
def read(p):return json.loads(pathlib.Path(p).read_text())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def write(p,v):pathlib.Path(p).write_text(json.dumps(v,indent=2)+'\n')
def rel(p):return str(pathlib.Path(p).relative_to(OBJ))
ledger=read(OUT/'candidate-phases.json');dense=read(OUT/'dense-native-measurements.json');raw=read(OUT/'raw-frame-manifest.json');atlases=read(OUT/'atlas-manifest.json');audit=read(OUT/'source-only-audit.json');reference=read(P/'resources/source-motion-reference.json');contexts=read(OUT/'context-registration.json');cam=read(OUT/'camera.json');previews=read(OUT/'preview-manifest.json')
# Translate actual measured points into conventional displacement calibration without changing measurements.
points=cam['calibration'];record={**cam,'measuredProjectionPoints':points,'calibration':{'root':points['root'],**{k:[points[k][i]-points['root'][i] for i in [0,1]] for k in ['unitX','unitDepth','unitHeight']}},'measurementSource':'candidates/round-02/camera.json','measurementSourceSHA256':sha(OUT/'camera.json')};write(OUT/'camera-record.json',record)
rig=read(OUT/'rig.json');rig['semanticDriverMap']='source/semantic-driver-map.json';rig['candidateProject']='source/round-02.blend';rig['candidateStatus']='Native source-preserving geometry revision awaiting independent review';write(OUT/'rig-record.json',rig)
# Compare every actual measured native driver, independently of geometry part counts.
src={(s['clip'],s['direction'],s['frame']):s for s in reference['samples']};maxerr={'location':0,'rotation':0,'scale':0};records=[]
for sample in ledger:
 s=src[(sample['clip'],sample['direction'],sample['frame'])];errs={k:0 for k in maxerr}
 for n,driver in sample['drivers'].items():
  original=s['drivers'][n]
  for k in maxerr:errs[k]=max(errs[k],max(abs(a-b) for a,b in zip(driver[k],original[k])))
 for k in maxerr:maxerr[k]=max(maxerr[k],errs[k])
 records.append({'clip':sample['clip'],'direction':sample['direction'],'frame':sample['frame'],'rootRotationZ':sample['rootRotationZ'],'rootMatrix':sample['rootMatrix'],'localBounds':sample['localBounds'],'driverErrors':errs,'rawFrame':sample['path']})
# Quarter-frame carrier trajectories against the actual original linear baked curves.
def evalcurve(curve,f):
 keys=curve['keys']
 if f<=keys[0]['co'][0]:return keys[0]['co'][1]
 if f>=keys[-1]['co'][0]:return keys[-1]['co'][1]
 for a,b in zip(keys,keys[1:]):
  x,y=a['co'];xx,yy=b['co']
  if x<=f<=xx:return y+(yy-y)*(f-x)/(xx-x)
curveMap={clip:{a['ownerName']:a['curves'] for a in acts} for clip,acts in reference['actions'].items()}
denseerr={'location':0,'rotation':0,'scale':0}
for s in dense['samples']:
 for n,driver in s['drivers'].items():
  for curve in curveMap[s['clip']][n]:
   key={'rotation_euler':'rotation','location':'location','scale':'scale'}.get(curve['path'])
   if key:denseerr[key]=max(denseerr[key],abs(driver[key][curve['index']]-evalcurve(curve,s['frame'])))
unions={}
for clip in ['idle','highlighted','clearance']:
 a=[s['localBounds'] for s in dense['samples'] if s['clip']==clip];unions[clip]={'min':[min(v['min'][i] for v in a) for i in range(3)],'max':[max(v['max'][i] for v in a) for i in range(3)]}
idle=next(s for s in ledger if s['clip']=='idle' and s['direction']=='S');body=[p['bounds'] for p in idle['parts'] if not p['name'].startswith('loose_debris_')];width=max(b['max'][0] for b in body)-min(b['min'][0] for b in body)
feet=[r for r in audit['contacts'] if r['name'].startswith('foot_')];rubbish=[r for r in audit['contacts'] if 'loose_debris_' in r['name']]
closure=max(abs(a-b) for n,r in dense['highlightedClosure']['drivers'].items() for k in ['location','rotation','scale'] for a,b in zip(r[k],dense['highlightedStart']['drivers'][n][k]))
# Read-back atlas crops must match all100 full native frames exactly, including transparent RGB.
exactAtlases=True
for a in atlases:
 im=Image.open(OBJ/a['path']).convert('RGBA')
 for r in [r for r in raw if r['clip']==a['clip'] and r['direction']==a['direction']]:
  x,y,w,h=a['rects'][r['index']];exactAtlases &= im.crop((x,y,x+w,y+h)).tobytes()==Image.open(OBJ/r['path']).convert('RGBA').tobytes()
replay=Image.open(OUT/'replay-idle-S.png').convert('RGBA');first=Image.open(OUT/'frames/idle-S/000.png').convert('RGBA');samePixels=replay.tobytes()==first.tobytes();diff=ImageChops.difference(replay,first);write(OUT/'reproduction-check.json',{'source':'source/round-02.blend','freshRender':'candidates/round-02/replay-idle-S.png','shippingNativeFrame':'candidates/round-02/frames/idle-S/000.png','identicalPixels':samePixels,'differenceExtrema':diff.getextrema(),'nativeRenderRecord':'candidates/round-02/replay-native-record.json'})
camExpected={'root':[448,704],'unitX':[256,0],'unitDepth':[0,256],'unitHeight':[0,-179.2]};calerr=max(abs(a-b) for k in camExpected for a,b in zip(record['calibration'][k],camExpected[k]));idleU=unions['idle'];hiU=unions['highlighted'];clU=unions['clearance'];sourceMin=[-1.5980126857757568,-1.2989999055862427,0];sourceMax=[1.5537077188491821,1.349632740020752,1.6430883407592773]
checks={'all100NativeFrames':len(raw)==100,'all12OriginalLayoutAtlases':len(atlases)==12,'exactAtlasPixelsAndRegions':exactAtlases,'actualDirections':[r['direction'] for r in records].count('S')==25 and all(abs(r['rootRotationZ']-{'S':0,'N':math.pi,'E':math.pi/2,'W':-math.pi/2}[r['direction']])<1e-6 for r in records),'cameraCalibrationWithin005NativePixels':calerr<.05,'idleEnvelope':all(idleU['min'][i]>=v for i,v in enumerate([-1,-1,-.002])) and all(idleU['max'][i]<=v for i,v in enumerate([1,1,1.0801])),'mainBodyWidth190to1999':1.90<=width<=1.999,'highlightedEnvelope':all(hiU['min'][i]>=v for i,v in enumerate([-1,-1,-.002])) and all(hiU['max'][i]<=v for i,v in enumerate([1,1,1.084])),'clearanceEnvelope':all(clU['min'][i]>=sourceMin[i]-.03 and clU['max'][i]<=sourceMax[i]+.03 for i in range(3)),'all60OriginalActionCurvesIdentical':audit['allSourceActionCurvesIdentical'],'perRoleTransformTolerances':maxerr['location']<=.002 and maxerr['rotation']<=.002 and maxerr['scale']<=.001,'quarterFrameTransformTolerances':denseerr['location']<=.002 and denseerr['rotation']<=.002 and denseerr['scale']<=.001,'highlightedExactClosure':closure<1e-6,'fourGroundSupportRegions':len(feet)==4 and all(abs(c['minZ'])<=.002 and c['groundPointsWithin002'] for c in feet),'threeRubbishFloorContacts':len(rubbish)==3 and all(abs(c['minZ'])<=.002 and c['groundPointsWithin002'] for c in rubbish),'opaqueMaterialsAndNoShaderAnimation':not any(m['animated'] for m in audit['materialRecords']) and read(OUT/'lighting.json')['materialsOpaque'],'sourceSelfContained':not audit['resources']['libraries'] and not audit['resources']['images'] and not audit['resources']['externalObjectData'],'excludedFloorsUnchanged':all(r['unchanged'] for r in contexts['excludedFloorIntegrity']),'freshReopenPixelsIdentical':samePixels,'unchangedOriginalBackup':sha(P/'resources/original-library.blend')=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'}
checks['terminalScalePointOneEverySemanticRole']=all(abs(v-.1)<1e-6 for s in ledger if s['clip']=='clearance' and s['frame']==12 for driver in s['drivers'].values() for v in driver['scale'])
checks['supportAnchorsWithin004']=all(min(math.hypot((c['bounds']['min'][0]+c['bounds']['max'][0])*.5-x,(c['bounds']['min'][1]+c['bounds']['max'][1])*.5-y) for x in [-.75,.75] for y in [-.39,.39])<=.04 for c in feet)
# Playback observation is a required distinct piece of evidence, filled only after actual viewing.
playback=read(OUT/'playback-observation.json') if (OUT/'playback-observation.json').exists() else {'status':'pending actual browser playback inspection'}
validation={'asset':'garbage-sofa','round':2,'status':'Technical measurements only; independent aesthetic verdict required','briefSHA256':'b1bda55dd329117ad02a0b6f8c8c8d390e3ba1775dcfd05351b90d592fb18d67','nativeProject':'source/round-02.blend','nativeProjectSHA256':sha(P/'round-02.blend'),'nativeCaptureScale':2,'publishedSourceScale':2,'logicalFrame':[448,576],'nativeFrame':[896,1152],'logicalRoot':[224,352],'nativeRoot':[448,704],'nativeCaptures':records,'nativePhaseLedger':'candidates/round-02/candidate-phases.json','denseNativeMeasurements':'candidates/round-02/dense-native-measurements.json','sourceOnlyAudit':'candidates/round-02/source-only-audit.json','sourceMotionReference':'source/resources/source-motion-reference.json','semanticDriverMap':'source/semantic-driver-map.json','driverErrors':maxerr,'quarterFrameDriverErrors':denseerr,'quarterFrameSamples':len(dense['samples']),'highlightedClosureMaxError':closure,'measuredUnions':unions,'mainBodyWidth':width,'cameraCalibrationMaxErrorNativePixels':calerr,'supportContacts':audit['contacts'],'lighting':read(OUT/'lighting.json'),'technicalChecks':checks,'allTechnicalChecksPassed':all(checks.values()),'playbackEvidence':playback,'topologyNotes':'Evaluated native curve tubes can retain coincident separate cap vertices; thin beveled native trim has zero-area corner facets. Full measured topology is retained in source-only-audit.json. Boolean inner-cut slot uses Blender default opaque surface; no external material is missing. These measurements do not substitute for visual inspection.','atlasPixelPolicy':'All complete896x1152 native canvases copied losslessly in exact original6x2 or1x1 layout. No paintover, warping, alpha fitting, resampling or color grading.','resourceAudit':'candidates/round-02/resource-audit.json','contextRegistration':'candidates/round-02/context-registration.json','nativeRecordAdapters':{'camera':'candidates/round-02/camera-record.json','assetRecord':'candidates/round-02/asset.json','rig':'candidates/round-02/rig-record.json'},'sourceUnchangedByAudit':audit['sourceUnchangedAfterAudit']}
write(OUT/'validation.json',validation)
resources={}
for folder in [OBJ/'source',OBJ/'candidates']:
 for p in sorted(folder.rglob('*')):
  if p.is_file() and '__pycache__' not in p.parts and p.name not in ['packet.json']:
   resources['resource%04d'%len(resources)]=rel(p)
delivery={'asset':'garbage-sofa','round':2,'status':'Candidate ready for coordinator seal and independent review; editor does not approve','pipeline':'native-3d','project':'source/round-02.blend','recipeScript':'source/recipe-round02.py','recipe':'source/recipe-round02.py','validation':'candidates/round-02/validation.json','nativeRecords':validation['nativeRecordAdapters'],'heroes':{d:'candidates/round-02/frames/idle-'+d+'/000.png' for d in ['N','E','S','W']},'previews':previews,'rawFrames':raw,'atlases':atlases,'resources':resources,'retainedDrafts':'source/retained-drafts.json','recipeCommands':['blender -b --python source/recipe-round02.py -- --round reproduced-round-02','blender -b --python source/audit-round02.py','blender -b --python source/replay-round02.py','python source/assemble-round02.py','python source/validate-round02.py'],'editorNotes':'Rebuilt soft upholstery, fitted piping, dimensional stitched patch and real seat aperture, cream inset, warm wood understructure, clean underside, repaired side/rear cues, grounded rubbish. All20 original semantic carriers and60 action curves preserved; child geometry changes within the frozen envelopes. Separate context demonstrates later removal after the actual opaque native terminal debris. No production or frozen input/review edits.'}
write(OBJ/'delivery-round02.json',delivery);write(OBJ/'delivery.json',delivery)
print('CHECKS',json.dumps(checks));print('ERRORS',maxerr,denseerr,'CHECKS_PASS',all(checks.values()),'RESOURCES',len(resources))
