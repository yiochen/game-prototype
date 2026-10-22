"""Compact complete source/candidate semantic and192-phase physical parity validation."""
from pathlib import Path
import json,hashlib,math,numpy as np
P=Path(__file__).parent;B=P.parent;C=B/'candidates/round-02'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def diffs(a,b,path=''):
 out=[]
 if type(a)!=type(b):return [{'path':path,'source':a,'candidate':b}]
 if isinstance(a,dict):
  for k in sorted(set(a)|set(b)):
   if k not in a or k not in b:out.append({'path':path+'/'+k,'source':a.get(k),'candidate':b.get(k)})
   else:out+=diffs(a[k],b[k],path+'/'+k)
 elif isinstance(a,list):
  if len(a)!=len(b):out.append({'path':path+'/length','source':len(a),'candidate':len(b)})
  for i,(x,y) in enumerate(zip(a,b)):out+=diffs(x,y,path+'/'+str(i))
 elif a!=b:out.append({'path':path,'source':a,'candidate':b})
 return out
s=read(C/'source-shared.json');n=read(C/'candidate-shared.json');sp=read(C/'source-phases.json');np_=read(C/'candidate-phases.json');brief=read(B/'brief-v3-held-food-semantic-contact.json');plane='chef_noor__ground_root.001__held_dish-salmon__image_plane';delta=diffs(s['shared'],n['shared']);allowed=[];unexpected=[]
for d in delta:
 p=d['path'];permitted=any(p.startswith('/meshes/'+plane+'/'+key) for key in ['vertexCoordinates','cornerNormals','polygonNormals','uv/','rna/texspace_location/','rna/texspace_size/']) or p.startswith('/objects/'+plane+'/rna/dimensions/')
 (allowed if permitted else unexpected).append(d)
# Food material/transform/ray flags remain exact; allowed mesh is independently validated to frozen mapping.
food=n['food'];mapping=brief['constraints']['heldFoodSemanticMapping'];quad=np.array(food['quad']);expect=np.array(mapping['localVertices'])
foodok=food['packedSHA256']==brief['foodDependency']['sha256'] and food['size']==[731,505] and food['uv']==mapping['uvLoops'] and food['faces']==s['food']['faces']==[[0,1,2,3]] and np.max(abs(quad-expect))<1e-7 and all(food['rayFlags'].values()) and food['alphaMode']==s['food']['alphaMode'] and food['colorSpace']==s['food']['colorSpace'] and food['interpolation']==s['food']['interpolation'] and food['extension']==s['food']['extension']
lookup={(r['clip'],r['direction'],r['index']):r for r in sp};phase=[];failures=[];support=[];fields=['localCoordinates','worldCoordinates','vertexNormals','worldVertexNormals','cornerNormals','polygonNormals','vertices','polygons','loops'];boundsmax=matrixmax=0.;meshchecks=0
for r in np_:
 key=(r['clip'],r['direction'],r['index']);old=lookup[key];bad=[]
 if set(r['physicalMeshes'])!=set(old['physicalMeshes']):bad.append('physicalObjectCoverage')
 for name,g in r['physicalMeshes'].items():
  a=old['physicalMeshes'][name];meshchecks+=1
  for f in fields:
   if g[f]!=a[f]:bad.append(name+'/'+f)
  boundsmax=max(boundsmax,float(np.max(abs(np.array(g['bounds'])-a['bounds']))));matrixmax=max(matrixmax,float(np.max(abs(np.array(g['matrix'])-a['matrix']))))
  if not g['finite']:bad.append(name+'/nonfinite')
 for f in ['pose','nativeTransforms','cameraMatrix','rootMatrix','rootPixel','foodChannels']:
  if r[f]!=old[f]:bad.append(f)
 if abs(r['rootRotationDegrees']-{'S':0,'E':90,'N':180,'W':-90}[r['direction']])>1e-4:bad.append('cardinal')
 if bad:failures.append({'clip':key[0],'direction':key[1],'index':key[2],'paths':bad})
 phase.append({'clip':key[0],'direction':key[1],'index':key[2],'physicalMeshCount':len(r['physicalMeshes']),'allCoordinateNormalTopologyPoseVisibilityDigestsEqual':not bad,'maxBoundsDifference':max(float(np.max(abs(np.array(g['bounds'])-old['physicalMeshes'][name]['bounds']))) for name,g in r['physicalMeshes'].items()),'failurePaths':bad})
 if key[0] in ['hold','load']:
  for a,b in zip(old['semanticSupport'],r['semanticSupport']):
   support.append({'clip':key[0],'direction':key[1],'index':key[2],'alphaCutoff':b['cutoff'],'sourceRimWorld':a['world'],'candidateRimWorld':b['world'],'sourceRimNativePixels':a['projected'],'candidateRimNativePixels':b['projected'],'rimWorldError':float(np.linalg.norm(np.array(a['world'])-b['world'])),'rimNativePixelError':float(np.linalg.norm(np.array(a['projected'])-b['projected'])),'sourceOccupiedWidthWorld':a['occupiedWidthWorld'],'candidateOccupiedWidthWorld':b['occupiedWidthWorld'],'occupiedWidthDifferenceWorld':abs(a['occupiedWidthWorld']-b['occupiedWidthWorld']),'sourcePalmRelations':a['palmRelations'],'candidatePalmRelations':b['palmRelations'],'palmWorldRelationshipMaxError':max(float(np.max(abs(np.array(a['palmRelations'][k]['rimMinusPalmWorld'])-b['palmRelations'][k]['rimMinusPalmWorld']))) for k in a['palmRelations']),'palmProjectedRelationshipMaxError':max(float(np.max(abs(np.array(a['palmRelations'][k]['rimMinusPalmNativePixels'])-b['palmRelations'][k]['rimMinusPalmNativePixels']))) for k in a['palmRelations'])})
primary=[v for v in support if v['alphaCutoff']==128];sens={str(cut):{'frames':len([v for v in support if v['alphaCutoff']==cut]),'maxNativeRimShiftPixels':max(v['rimNativePixelError'] for v in support if v['alphaCutoff']==cut),'maxWorldRimShift':max(v['rimWorldError'] for v in support if v['alphaCutoff']==cut),'maxOccupiedWidthDeltaWorld':max(v['occupiedWidthDifferenceWorld'] for v in support if v['alphaCutoff']==cut)} for cut in [64,128,192]}
write(C/'phase-parity.json',{'method':'Every physical body/knife evaluated local/world coordinate buffer and vertex/world/corner/polygon normal buffer hashed in full at all192 phases, plus full pose/native transforms/visibility/camera; shared rest topology/UVs/smoothing/weights/materials/constraints/actions/drivers stored once. Equal full float-buffer hashes establish zero component maxima. Failure paths are explicit, never omitted.','count':len(phase),'physicalMeshComparisons':meshchecks,'phases':phase,'failures':failures})
write(C/'semantic-support-all96.json',{'method':'Actual evaluated original and candidate native food matrices acting on visible opaque plate bottom-rim alpha64/128/192 reference. All96 active poses retain source world/projected palm relationships; no literal3D zero gap asserted for the original camera-facing2D billboard. Source baseline is actual approved file, not old padded quad bottom.','referenceAlpha':128,'activePhaseCount':len(primary),'sensitivity':sens,'records':support})
write(C/'allowed-scene-differences.json',{'allowedOnlyFoodQuadUVAndDerivedGeometry':allowed,'unexpected':unexpected,'foodImage':{'source':s['food'],'candidate':food},'maxQuadCoordinateError':float(np.max(abs(quad-expect))),'note':'Changed food quad geometry naturally changes food-derived dimensions, texture-space bounds and computed floating normal bytes. No physical chef/knife normals are exempted.'})
ref=read(B/'reviews/held-food-v2-source-measurements.json')['evaluatedSamples'];rr={(r['clip'],r['direction'],r['index']):r for r in ref};loc=np.array([*read(P/'support-reference-round02.json')['references'][1]['sourceLocal']['pointLocal'],1]);refmax=max(float(np.linalg.norm(np.array(v['sourceRimWorld'])-(np.array(rr[v['clip'],v['direction'],v['index']]['planeEvaluatedWorldMatrix'])@loc)[:3])) for v in primary)
result={'asset':'chef-noor','round':'round-02','brief':'brief-v3-held-food-semantic-contact.json','briefSHA256':sha(B/'brief-v3-held-food-semantic-contact.json'),'sourceProjectSHA256':s['projectSHA256'],'candidateProjectSHA256':n['projectSHA256'],'phaseCount':len(phase),'physicalObjectsPerPhase':len(np_[0]['physicalMeshes']),'physicalMeshPhaseComparisons':meshchecks,'allFrozenPhysicalFloatBuffersExactlyEqual':not failures,'maximumPhysicalVertexNormalPoseComponentDifference':0 if not failures else None,'maximumPhysicalBoundsDifference':boundsmax,'maximumPhysicalObjectMatrixDifference':matrixmax,'staticUnexpectedDifferenceCount':len(unexpected),'staticAllowedFoodDifferenceCount':len(allowed),'canonicalExactAndMappingValid':foodok,'primary128Support':sens['128'],'sourceRimReferenceMaxWorldDifference':refmax,'sensitivity':sens,'sourceOriginalStillImmutable':sha((B/brief['source']['backup']).resolve())==brief['approvedBody']['sha256'] and sha(P/'round-01.blend')==brief['approvedBody']['sha256'],'sourceDefinition':'Exact approved native Noor body8225bd…; stored source metadata is evidence only, not authority for physical inputs.','semanticImageClosure':'Exact canonical packed2D image plus round-specific byte-for-byte external dependency; no target card.','parityManifest':'candidates/round-02/phase-parity.json','semanticManifest':'candidates/round-02/semantic-support-all96.json','allowedDifferences':'candidates/round-02/allowed-scene-differences.json','limits':['Physical input parity does not require old/new body RGB identity: the changed Emission1 food can change secondary radiance/denoising. Fresh replay and image residual evidence supplied separately.','Native visual and motion judgment remains independent.'],'ok':len(phase)==192 and len(primary)==96 and not failures and not unexpected and foodok and sens['128']['maxNativeRimShiftPixels']<1e-4 and refmax<1e-6}
write(C/'parity-validation.json',result);print(json.dumps({k:v for k,v in result.items() if k not in ['limits','sensitivity']},indent=2))
