from pathlib import Path
import json,hashlib,math,collections
O=Path(__file__).resolve().parents[1];R=O/'reviews';P=O/'candidates/round-02'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
a=read(R/'round02-judge-native-audit.json');f=read(R/'round02-judge-file-audit.json');b=read(O/'brief.json');m=read(R/'round02-judge-material-bindings.json');contract=b['constraints']['measuredNativeContract']['nativeContract']
out={'packetSHA256':sha(P/'packet.json'),'selectedDelivery':{'path':'delivery-round02.json','sha256':sha(O/'delivery-round02.json'),'snapshotSHA256':sha(P/'delivery.snapshot.json'),'validationSHA256':sha(P/'validation.json')},'sealedProjectSHA256':sha(O/'source/round-02.blend'),'frozenBriefSHA256':sha(O/'brief.json'),'packetReferenceRecheck':{'count':len(f['hashChecks']),'allMatch':all(sha((P/x['path']).resolve())==x['expected']for x in f['hashChecks'])},'unions':{}}
def union(bs):return {'min':[min(b['min'][i]for b in bs)for i in range(3)],'max':[max(b['max'][i]for b in bs)for i in range(3)]}
for clip in ['idle','highlighted','clearance']:
 bs=[s['localBounds']for s in a['samples']if s['clip']==clip]+[s['bounds']for s in a['fractionalSamples']if s['clip']==clip]
 u=union(bs)
 if clip=='idle':lo,hi=[-1,-1,-.002],[1,1,1.0801]
 elif clip=='highlighted':lo,hi=[-1,-1,-.002],[1,1,1.084]
 else:
  source=contract['animation']['clearance']['sourceLocalTransientUnion'];lo=[v-.03 for v in source['min']];hi=[v+.03 for v in source['max']]
 out['unions'][clip]={'measured':u,'allowedMin':lo,'allowedMax':hi,'pass':all(lo[i]<=u['min'][i]<=u['max'][i]<=hi[i]for i in range(3)),'integerFacingSamples':sum(s['clip']==clip for s in a['samples']),'fractionalLocalSamples':sum(s['clip']==clip for s in a['fractionalSamples'])}
body=[x for x in a['idleParts']if x['name']in ['old_arm_-0.84__arm','old_arm_0.84__arm','old_back__soft_back','base__wooden_understructure']]
u=union([x['bounds']for x in body]);width=u['max'][0]-u['min'][0];out['mainBodyWidth']={'value':width,'allowed':[1.9,1.999],'pass':1.9<=width<=1.999,'parts':[x['name']for x in body]}
out['supports']=[]
for x in a['idleParts']:
 if '__tapered_wood_support'not in x['name']:continue
 pts=x['groundPoints'];center=[sum(p[i]for p in pts)/len(pts)for i in range(3)];source=min(contract['placementAndContact']['loadBearingFeet']['centersXY'],key=lambda v:math.dist(v,center[:2]));out['supports'].append({'part':x['name'],'groundPatchCenter':center,'sourceSupportRegion':source,'distanceXY':math.dist(source,center[:2]),'pass':math.dist(source,center[:2])<=.04 and abs(center[2])<=.002})
out['rubbishGround']=[{'part':x['name'],'minZ':x['bounds']['min'][2],'pass':abs(x['bounds']['min'][2])<=.002}for x in a['idleParts']if '__grounded_rubbish'in x['name']]
out['rasterClipCheck']={'count':len(f['nativeFrames']),'minimumMarginsNative':[min(x['alphaBounds'][0]for x in f['nativeFrames']),min(x['alphaBounds'][1]for x in f['nativeFrames']),min(896-x['alphaBounds'][2]for x in f['nativeFrames']),min(1152-x['alphaBounds'][3]for x in f['nativeFrames'])],'allNonempty':all(not x['empty']for x in f['nativeFrames']),'exactNativeDimensions':all(x['size']==[896,1152]for x in f['nativeFrames'])}
out['rasterClipCheck']['pass']=min(out['rasterClipCheck']['minimumMarginsNative'])>0 and out['rasterClipCheck']['allNonempty']and out['rasterClipCheck']['exactNativeDimensions']
errors=[]
for s in a['samples']:
 ang={'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[s['direction']];co,si=math.cos(ang),math.sin(ang);ex=[[co,-si,0,0],[si,co,0,0],[0,0,1,0],[0,0,0,1]];errors.append(max(abs(s['root'][i][j]-ex[i][j])for i in range(4)for j in range(4)))
out['rootMatrices']={'count':len(errors),'maxAbsError':max(errors),'pass':max(errors)<=1e-6}
cam=a['camera'];frozen=contract['immutableCapture'];materr=max(abs(cam['matrix'][i][j]-frozen['cameraWorldMatrix'][i][j])for i in range(4)for j in range(4));rooterr=max(abs(cam['rootPx'][i]-[448,704][i])for i in range(2));calerr=max(abs(cam[key][i]-want[i])for key,want in [('XPx',[704,704]),('DPx',[448,960]),('HPx',[448,524.8])]for i in range(2));out['capture']={'cameraMatrixMaxAbsError':materr,'rootNativeMaxAbsError':rooterr,'calibrationNativeMaxAbsError':calerr,'pass':materr<=1e-6 and rooterr<=.05 and calerr<=.05 and cam['resolution']==[896,1152]and cam['percentage']==100 and cam['pixelAspect']==frozen['pixelAspect']and cam['ortho']==frozen['orthoScale']and cam['shift']==frozen['cameraShift']}
bindings=m['geometryMaterialBindings'];out['materialClosure']={'geometryObjects':len(bindings),'allTextureCoordinateObjectsMatchSemanticCarrier':all(n['object']==ob['parent']for ob in bindings for slot in ob['materialSlots']for n in slot['coordinates']),'allPrincipledAlphaOne':all(alpha==1 for ob in bindings for slot in ob['materialSlots']for alpha in slot['principledAlpha']),'externalLibrariesImagesFonts':a['resources'],'noGeometryOutsideAsset':all(x['type']in ['CAMERA','LIGHT']for x in m['sceneObjectsOutsideAsset']),'allMaterialAnimationAbsent':all(not x['animated']for x in a['materials'])}
ci=read(O/'source/resources/context-inputs.json');out['excludedFloorIntegrity']=[{'path':x['path'],'expectedSHA256':x['sha256'],'actualSHA256':sha(Path(x['path'])),'pass':sha(Path(x['path']))==x['sha256']}for x in ci['excludedFloorIntegrity']]
out['contextInputsMatchOriginal']={key:{'resourceSHA256':sha(O/v['path']),'sourceSHA256':sha(Path(v['source'])),'pass':sha(O/v['path'])==sha(Path(v['source']))}for key,v in ci.items()if key in ['floor','human']}
out['allChecksPassed']=all(x['pass']for x in out['unions'].values())and out['mainBodyWidth']['pass']and all(x['pass']for x in out['supports']+out['rubbishGround'])and out['rasterClipCheck']['pass']and out['rootMatrices']['pass']and out['capture']['pass']and out['packetReferenceRecheck']['allMatch']and all(x['pass']for x in out['excludedFloorIntegrity'])and all(x['pass']for x in out['contextInputsMatchOriginal'].values())and out['materialClosure']['allTextureCoordinateObjectsMatchSemanticCarrier']and out['materialClosure']['allPrincipledAlphaOne']and out['materialClosure']['noGeometryOutsideAsset']and out['materialClosure']['allMaterialAnimationAbsent']
(R/'round02-judge-final-checks.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps({k:out[k]for k in ['packetReferenceRecheck','unions','mainBodyWidth','rasterClipCheck','rootMatrices','capture','contextInputsMatchOriginal','allChecksPassed']},indent=2))
