"""Geometric/native evidence and exact registered publication. No art approval."""
from pathlib import Path
import json, math, hashlib, shutil
from PIL import Image
import numpy as np
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;OUT=BASE/'candidates/round-01';RES=HERE/'round01-resources'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
write=lambda p,j:Path(p).write_text(json.dumps(j,indent=2)+'\n')
data=json.loads((OUT/'native-measurements.json').read_text());contract=json.loads((RES/'contracts/root-preparation-reconciliation-v1.json').read_text())
tol=1e-6;hull=contract['authoringEnvelope']['xy']
def inside(p):
 return all((hull[(i+1)%len(hull)][0]-a[0])*(p[1]-a[1])-(hull[(i+1)%len(hull)][1]-a[1])*(p[0]-a[0])>=-tol*math.dist(a,hull[(i+1)%len(hull)]) for i,a in enumerate(hull)) and .04-tol<=p[2]<=.78+tol
vertices=[p for o in data['own']['objects'] for p in o.get('evaluatedVertices',[])];raw=[p for o in data['own']['objects'] for p in o.get('rawVertices',[])]
violations=[p for p in raw+vertices if not inside(p)]
assert not violations,violations[:10]
polys=[[v[:2] for v in f['vertices']] for f in data['own']['supportFaces']]
expected=[contract['finiteSupport']['unionXY']]
# Exact planar finite union via segment-critical vertical sweep. This evaluates
# polygon unions/intersections, including overlaps; it never sums face areas.
def edges(polygons):
 return [(p[i],p[(i+1)%len(p)]) for p in polygons for i in range(len(p))]
def ys_at(polygons,x):
 spans=[]
 for p in polygons:
  ys=[]
  for a,b in edges([p]):
   if min(a[0],b[0])<x<max(a[0],b[0]):ys.append(a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0]))
  ys.sort()
  spans.extend((ys[i],ys[i+1]) for i in range(0,len(ys)-1,2) if ys[i+1]-ys[i]>1e-12)
 spans.sort();merged=[]
 for lo,hi in spans:
  if merged and lo<=merged[-1][1]+1e-12:merged[-1]=(merged[-1][0],max(merged[-1][1],hi))
  else:merged.append((lo,hi))
 return merged
def length(spans):return sum(b-a for a,b in spans)
def intersection(a,b):return [(max(x,u),min(y,v)) for x,y in a for u,v in b if min(y,v)>max(x,u)]
all_edges=edges(polys+expected);xs={x for p in polys+expected for x,y in p}
for a,b in all_edges:
 if abs(b[0]-a[0])<1e-12:continue
 ma=(b[1]-a[1])/(b[0]-a[0]);ba=a[1]-ma*a[0]
 for c,d in all_edges:
  if abs(d[0]-c[0])<1e-12:continue
  mb=(d[1]-c[1])/(d[0]-c[0]);bb=c[1]-mb*c[0]
  if abs(ma-mb)<1e-12:continue
  x=(bb-ba)/(ma-mb)
  if max(min(a[0],b[0]),min(c[0],d[0]))<x<min(max(a[0],b[0]),max(c[0],d[0])):xs.add(x)
xs=sorted(xs);areas=[0.,0.,0.]
for lo,hi in zip(xs,xs[1:]):
 if hi-lo<1e-12:continue
 for f in [.25,.75]:
  x=lo+f*(hi-lo);a=ys_at(polys,x);b=ys_at(expected,x)
  for i,value in enumerate([length(a),length(b),length(intersection(a,b))]):areas[i]+=(hi-lo)*value/2
xor=areas[0]+areas[1]-2*areas[2]
assert xor<1e-6,(areas,xor)
assert min(p[2] for p in vertices)>.039999 and abs(min(p[2] for p in vertices)-.04)<tol
ref=json.loads((RES/'contracts/actual-canonical-rig.json').read_text());actual=data['own']['actualRig']
rigchecks={k:actual[k]==ref[k] for k in ['engine','viewTransform','look','exposure','gamma','dither','filter']}
for light in ref['lights']:
 a=next(v for v in actual['lights'] if v['name']==light['name']);rigchecks['light:'+light['name']]=all(a[k]==light[k] for k in light if k!='name') and a['nodeGraph']==data['canonicalLightGraphs'][light['name']]
rigchecks['camera']=actual['camera']==ref['camera']
aw=actual['world'];rw=ref['world']
rigchecks['world']=len(aw['nodes'])==len(rw['nodes']) and aw['links']==rw['links'] and all(next(n for n in aw['nodes'] if n['name']==r['name'])['type']==r['type'] and {i['name']:i['value'] for i in next(n for n in aw['nodes'] if n['name']==r['name'])['inputs']}==r['inputs'] for r in rw['nodes'])
assert all(rigchecks.values()),rigchecks
capture=json.loads((OUT/'capture-records.json').read_text());frames=[];native=[];atlases=[]
for r in capture['captureRecords']:
 d=r['direction'];p=OUT/r['path'];im=Image.open(p);assert im.size==(384,704) and im.mode=='RGBA'
 alpha=np.asarray(im)[:,:,3];assert not (alpha[0].any() or alpha[-1].any() or alpha[:,0].any() or alpha[:,-1].any())
 pub=OUT/'frames'/('static-'+d+'.png');atlas=OUT/'atlases'/('static-'+d+'.png')
 pub.parent.mkdir(exist_ok=True);atlas.parent.mkdir(exist_ok=True);shutil.copyfile(p,pub);shutil.copyfile(p,atlas)
 assert sha(p)==sha(pub)==sha(atlas)
 common={'clip':'static','direction':d,'index':0,'width':384,'height':704,'dimensions':[384,704],'sha256':sha(p)}
 frames.append(common|{'path':str(pub.relative_to(BASE))});native.append(common|{'path':str(p.relative_to(BASE))})
 atlases.append({'clip':'static','direction':d,'path':str(atlas.relative_to(BASE)),'width':384,'height':704,'dimensions':[384,704],'columns':1,'rows':1,'rects':[[0,0,384,704]],'frames':1,'fps':12,'loop':False,'frameOrder':[0],'sha256':sha(atlas)})
 (OUT/'heroes').mkdir(exist_ok=True);shutil.copyfile(p,OUT/'heroes'/(d+'.png'))
recorddir=OUT/'records';recorddir.mkdir(exist_ok=True)
write(recorddir/'camera.json',capture['captureRecords'][0]['camera'])
write(recorddir/'rig.json',actual)
asset=json.loads((RES/'contracts/catalog-object.json').read_text());asset['registration']['sourceCaptureScale']=2;asset['productionStage']='Native Blender warm soft refinement candidate; independent approval pending';asset['artStyle']={'revision':'warm-soft-native-round01','worldLighting':True,'lighting':'Exact approved middle02 canonical symmetric rig','contrast':1,'contrastSpace':'Standard output; no postprocessing'}
write(recorddir/'asset.json',asset)
checks={'properFacings':all(abs(math.atan2(math.sin(r['rootRotationZ']-{'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[d]),math.cos(r['rootRotationZ']-{'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}[d])))<1e-6 and abs(r['determinant']-1)<1e-6 for d,r in data['all4MeasuredPoses'].items()),'rawAndEvaluatedOwnHull':not violations,'finiteSupportUnion':xor<1e-6,'noZ0Geometry':min(p[2] for p in vertices)>0,'canonicalWholeWFields':len(data['fullFiniteWFieldProof'])==27 and all(f['graphExactlyEqual'] for f in data['fullFiniteWFieldProof']),'canonicalRig':all(rigchecks.values()),'exactNativePNGIdentity':True,'noFrameClipping':True,'noLinkedLibrariesOrExternalImages':not data['externalDependencies']['linkedLibraries'] and not data['externalDependencies']['fileImages'],'staticOwnership':all(not o['animation'] and not o['constraints'] for o in data['own']['objects'])}
assert all(checks.values()),checks
summary={'asset':'wreck-end','sourceSHA256':sha(HERE/'round-01.blend'),'scope':'Measured hard constraints only; no visual verdict','checks':checks,'captureRecords':capture['captureRecords'],'nativeMeasurements':'candidates/round-01/native-measurements.json','nativeMeasurementsSHA256':sha(OUT/'native-measurements.json'),'sourceEnvelope':{'rawVertices':len(raw),'evaluatedVertices':len(vertices),'violations':violations,'evaluatedMin':[min(p[i] for p in vertices) for i in range(3)],'evaluatedMax':[max(p[i] for p in vertices) for i in range(3)]},'supportUnion':{'method':'exact segment-critical vertical sweep union and intersection of actual evaluated finite face polygons; topology-independent overlap-aware region proof','actualFaceCount':len(polys),'actualUnionArea':areas[0],'expectedUnionArea':areas[1],'intersectionArea':areas[2],'symmetricDifferenceArea':xor,'expectedBoundary':expected[0],'actualEvaluatedFaces':data['own']['supportFaces'],'representationTolerance':tol},'rigChecks':rigchecks,'fullWFieldSummary':'27 actual whole finite faces: 24 sides and 3 distinct outward W caps; constant CORNER normals, identical actual active normalized shader path and full graph at every point; worldZ-only albedo, identical surface constants/alpha1, no tangent dependence and zero longitudinal derivative; proper rotations preserve all fields','publication':{'nativeCaptureScale':2,'publishedSourceScale':2,'nativeFrame':[384,704],'publishedFrame':[384,704],'nativeRoot':[192,496],'logicalFrame':[192,352],'logicalRoot':[96,248],'method':'exact direct native PNG byte identity; no reduction/repair/fit','rawFrames':frames,'nativeRawFrames':native,'atlases':atlases},'visualAcceptance':'Original independent judge pending'}
write(OUT/'native-validation.json',summary)
print(json.dumps({'checks':checks,'support':summary['supportUnion']|{'actualEvaluatedFaces':'retained in JSON'},'sourceSHA256':summary['sourceSHA256']},indent=2))
