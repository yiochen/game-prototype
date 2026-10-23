"""Technical checks of measured saved native data; no aesthetic verdict."""
from pathlib import Path
import json,hashlib,math
from PIL import Image,ImageChops,ImageStat
HERE=Path(__file__).resolve().parent;OBJ=HERE.parents[1];OUT=OBJ/'candidates/round-04'
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,v):Path(p).write_text(json.dumps(v,indent=2)+'\n')
A=load(OUT/'native-audit.json');P=load(OUT/'candidate-phases.json');I=load(OUT/'candidate-inbetweens.json');R=load(OUT/'raster-audit.json');C=load(OUT/'contacts-and-native-meshes.json');rig=load(HERE/'resources/original-rig.json')
original=load(OBJ/'reviews/source-audit/native-phases.partial.json');old={(p['direction'],p['clip'],p['frame1']):p for p in original};parity=[];maxpar={'location':0,'rotation':0,'scale':0,'matrix':0}
for p in P:
 q=old[(p['direction'],p['clip'],p['frame1'])];om={o['name']:o for o in q['objects']}
 for o in p['objects']:
  b=om[o['name']]
  for key,k2 in [('location','location'),('rotation','rotationEuler'),('scale','scale')]:maxpar[key]=max(maxpar[key],max(abs(x-y) for x,y in zip(o[k2],b[k2])))
  maxpar['matrix']=max(maxpar['matrix'],max(abs(o['matrixWorld'][i][j]-b['matrixWorld'][i][j]) for i in range(4) for j in range(4)))
 parity.append({'clip':p['clip'],'direction':p['direction'],'frame1':p['frame1'],'sourceCarrierCount':len(om)-1,'candidateCarrierCount':len(p['objects'])})
# Inbetween transform channels are evaluated from immutable native source curves, piecewise linear source keys.
actions={a['name']:a for a in A['actions']};base={o['name']:o for o in old[('S','idle',1)]['objects']}
def evalkeys(keys,f):
 if f<=keys[0][0]:return keys[0][1]
 for a,b in zip(keys,keys[1:]):
  if a[0]<=f<=b[0]:return a[1]+(b[1]-a[1])*(f-a[0])/(b[0]-a[0])
 return keys[-1][1]
inbetweenMax=0
for p in I:
 objs={o['name']:o for o in p['objects']}
 for entry in rig['clips'][p['clip']]['actions']:
  o=objs[entry['ownerName']];b=base[o['name']];expected={'location':list(b['location']),'rotation_euler':list(b['rotationEuler']),'scale':list(b['scale'])}
  for c in actions[entry['action']]['curves']:expected[c['path']][c['index']]=evalkeys(c['keys'],p['frame1'])
  for key,k2 in [('location','location'),('rotation_euler','rotationEuler'),('scale','scale')]:inbetweenMax=max(inbetweenMax,max(abs(x-y) for x,y in zip(o[k2],expected[key])))
limits={'idle':([-1,-1,-.002],[1,1,1.6801]),'highlighted':([-1.008,-1.008,-.009],[1.008,1.008,1.694]),'clearance':([-1.566082864,-1.555552869,-.002],[1.563991098,1.250407248,2.277417688])};envelopes={};failures=[]
for clip,(lo,hi) in limits.items():
 qs=[p for p in P+I if p['clip']==clip];minimum=[min(p['rootLocalMin'][i] for p in qs) for i in range(3)];maximum=[max(p['rootLocalMax'][i] for p in qs) for i in range(3)];passed=all(lo[i]-1e-6<=minimum[i] and maximum[i]<=hi[i]+1e-6 for i in range(3));envelopes[clip]={'measuredMin':minimum,'measuredMax':maximum,'frozenMin':lo,'frozenMax':hi,'samples':len(qs),'pass':passed}
 if not passed:failures.append('envelope:'+clip)
# Ground support semantic regions use measured native vertices, not owner origins.
supports=[];sourceContacts=load(OBJ/'reviews/source-audit/contacts-shaders-resources.json')['physicalContactSamplesIdleS'];sourceContacts={x['object']:x for x in sourceContacts}
for c in C['idleContacts']:
 if 'old_upright' in c['owner']:
  expected=[-.91 if '_-0.88_' in c['owner'] else .85,-.36 if c['owner'].endswith('_-0.36') else .36];err=max(abs(c['bandCentroid'][i]-expected[i]) for i in range(2));supports.append({'owner':c['owner'],'expectedXY':expected,'measuredXY':c['bandCentroid'][:2],'maximumAxisError':err,'pass':err<=.03 and c['withinIdleGroundBand']})
 else:
  # Closest distance to the old ground-contact edge segment/rectangle measures a semantic region, not old topology.
  pts=sourceContacts[c['owner']]['lowestVerticesWithin005'];sx=[min(p[i] for p in pts) for i in range(2)];ex=[max(p[i] for p in pts) for i in range(2)];ds=[]
  for p in c['bandVerticesWorld']:ds.append(max(max(sx[i]-p[i],0,p[i]-ex[i]) for i in range(2)))
  supports.append({'owner':c['owner'],'sourceContactRegionXY':[sx,ex],'candidateContactBand':c['bandVerticesWorld'],'minimumOutsideRegionAxisDistance':min(ds),'pass':min(ds)<=.05 and c['withinIdleGroundBand']})
 if not supports[-1]['pass']:failures.append('contact:'+c['owner'])
# Fresh process reconstructs geometry, replays all phases and writes complete frames from immutable source resources.
repro=load(OUT/'reproduction/native-audit.json');RP=load(OUT/'reproduction/candidate-phases.json');RI=load(OUT/'reproduction/candidate-inbetweens.json');reprod=[];meanmax=0;exact=0
for p in load(OUT/'raw-frame-records.json'):
 a=Image.open(OBJ/p['path']);b=Image.open(OUT/'reproduction/frames'/f'{p["clip"]}-{p["direction"]}'/f'{p["index"]:03d}.png');same=a.tobytes()==b.tobytes();exact+=same;means=ImageStat.Stat(ImageChops.difference(a,b)).mean;meanmax=max(meanmax,max(means));reprod.append({'clip':p['clip'],'direction':p['direction'],'index':p['index'],'exactPixels':same,'meanAbsRGBA':means,'candidateSHA256':p['sha256'],'reproductionSHA256':sha(OUT/'reproduction/frames'/f'{p["clip"]}-{p["direction"]}'/f'{p["index"]:03d}.png')})
reproGeo=P==RP and I==RI and A['actions']==repro['actions'] and A['objects']==repro['objects']
if not reproGeo:failures.append('fresh native reconstruction measurement differs')
# Camera comparison is to actual immutable record, not an unrelated saved active camera.
cam=load(OUT/'camera.json');sourcecam=load(HERE/'resources/original-camera.json');cameraMax=max(abs(cam['camera']['worldMatrix'][i][j]-sourcecam['camera']['worldMatrix'][i][j]) for i in range(4) for j in range(4));projectionMax=max(abs(cam['camera']['projectionMatrix'][i][j]-sourcecam['camera']['projectionMatrix'][i][j]) for i in range(4) for j in range(4));cal=cam['calibration'];basis=cal['root']==[448,896]
rootMax=max(max(abs(v) for v in p['rootLocation']) for p in P+I);rootScaleMax=max(max(abs(v-1) for v in p['rootScale']) for p in P+I);sourceafter=sha(HERE/'resources/original-library.blend');actionEqual=A['actions']==A['actionsAfter'];alphaOpaque=all(n['inputs'].get('Alpha',1)==1 for m in A['materials'] for n in m['nodes'] if n['type']=='BSDF_PRINCIPLED');noShaderAnimation=all(not m['animation'] for m in A['materials']);vis=all(not o['hideRender'] and not o['hideViewport'] for p in P+I for o in p['objects']);closureMax=0
for d in ['S','E','N','W']:
 a=next(p for p in P if p['direction']==d and p['clip']=='highlighted' and p['frame1']==1);b=next(p for p in P if p['direction']==d and p['clip']=='highlighted' and p['frame1']==13)
 for x,y in zip(a['objects'],b['objects']):closureMax=max(closureMax,max(abs(x['matrixWorld'][i][j]-y['matrixWorld'][i][j]) for i in range(4) for j in range(4)))
assert len(P)==104 and len(I)==276 and len(load(OUT/'raw-frame-records.json'))==100
if max(maxpar.values())>1e-5:failures.append('carrier source parity')
if inbetweenMax>1e-5:failures.append('inbetween source parity')
if closureMax>1e-6:failures.append('native loop closure')
if not actionEqual:failures.append('source action edit')
if not alphaOpaque or not noShaderAnimation or not vis:failures.append('opacity or visibility')
if cameraMax>1e-5 or projectionMax>1e-6 or rootMax>1e-6 or rootScaleMax>1e-6:failures.append('registration')
if R['minimumNativeBorder']<8:failures.append('raster clipping')
if not all(v['RGBAExact'] for v in R['closure']):failures.append('rendered closure')
mainWidth=envelopes['idle']['measuredMax'][0]-envelopes['idle']['measuredMin'][0]
if not 1.90<=mainWidth<=1.999:failures.append('main body capacity')
# Preserve original excluded designs verbatim in reproduction resources; production design bytes are rechecked.
floorcheck=[]
for name in ['floor-cream','floor-blue-wave','floor-checker']:
 p=HERE/'resources/context'/f'{name}.png';prod=OBJ.parents[2]/'production/sprites'/name/'static-S.png';floorcheck.append({'name':name,'frozenReferenceSHA256':sha(p),'currentProductionSHA256':sha(prod),'bytesUnchanged':sha(p)==sha(prod)})
 if not floorcheck[-1]['bytesUnchanged']:failures.append('excluded floor changed:'+name)
summary={'asset':'garbage-shelving','round':'round-04','technicalPass':not failures,'visualVerdict':'pending independent judge; no editor approval','failures':failures,'nativeValidation':'candidates/round-04/native-audit.json','nativeCaptures':[{k:p[k] for k in ('clip','direction','frame1','rootRotationZ','rootMatrix')} for p in P],'frameCount':100,'nativeClosureDiagnostics':4,'inbetweenSamples':276,'allPhaseAndInbetweenEnvelopes':envelopes,'mainBodyWidth':mainWidth,'camera':{'path':'candidates/round-04/camera.json','scale':2,'matrixMaximumError':cameraMax,'projectionMaximumError':projectionMax,'calibration':cal,'fixedForAllFrames':True},'rootLocationMaximumError':rootMax,'rootScaleMaximumError':rootScaleMax,'sourcePrimaryCarrierTransformMaximumErrors':maxpar,'inbetweenSourceNativeCurveMaximumError':inbetweenMax,'sourceNativeActionCohortsExact':actionEqual,'sourceActionCount':len(A['actions']),'nativeClosureMaximumMatrixError':closureMax,'rasterClosureRGBAExactAllFour':all(v['RGBAExact'] for v in R['closure']),'minimumNativeBorder':R['minimumNativeBorder'],'groundContacts':supports,'allStaticOpaqueMaterials':alphaOpaque,'noShaderAnimation':noShaderAnimation,'allStaticAuthoredVisibility':vis,'noExternalImagesOrLibraries':not A['externalImages'] and not A['libraries'],'freshProcessReproduction':{'nativeMeasurementsIdentical':reproGeo,'fullNativeFrameCount':100,'exactPixelFrames':exact,'maximumMeanRGBA':meanmax,'note':'Pixel identity is measured for this reproduction, never assumed as a general requirement','records':'candidates/round-04/reproduction/native-audit.json','rasterComparison':'candidates/round-04/reproduction-comparison.json'},'excludedFloors':floorcheck,'sourceBlendSHA256AfterReproduction':sourceafter,'frozenBriefSHA256':sha(OBJ/'brief.json'),'geometryDeltaExplanation':'Four original shelf carriers now own independently beveled sagging planks, grain and rounded wear; four original supports are chunkier with floor-plane feet and seated pegs. Six exact parcel carrier paths retain phases but own wrapped native forms placed nearer the accessible shelf edge. Original fallen plank/debris carriers extend native low surfaces to ground. These are allowed native design differences inside frozen union bounds, not pose or camera changes. Discarded drafts are retained.','deliverySchemaCheckedAgainst':['tools/promote_object.py','tools/audit_directions.py','tools/save_runtime_variant_approval.py','godot/tools/refined_actor_variants.py'],'runtimeVariantReceipt':'Not applicable: garbage-shelving is not an actor with a supplemental runtime bundle','extraDiagnosticCameraViews':'previews underside/front/rear are explicitly additional geometry inspections and never replace the immutable registered exports; underside alone uses a diagnostic soft fill below the assembly.'}
dump(OUT/'validation.json',summary);dump(OUT/'reproduction-comparison.json',reprod)
print(json.dumps({'technicalPass':not failures,'failures':failures,'sourceParity':maxpar,'inbetweens':inbetweenMax,'reproductionExact':exact,'nativeGeometryReproduction':reproGeo,'contactCount':len(supports)},indent=2))
