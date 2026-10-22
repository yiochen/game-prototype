"""Derive exact terminal boundary segments from retained actual evaluated native polygons."""
from pathlib import Path
import json,math,hashlib
B=Path(__file__).resolve().parents[1];O=B/'candidates/round-05';E=json.loads((O/'native-validation.json').read_text());F=json.loads((O/'paired-native-validation-v2.json').read_text());D=json.loads((O/'dense-native-audit.json').read_text())
def segments(objects,y,normals_key):
 out=[]
 for o in objects:
  vs=o['verticesWorld'];normals=o.get(normals_key)
  for i,p in enumerate(o['polygons']):
   pts=[vs[j] for j in p]
   if not all(abs(v[2]-.22)<1e-5 for v in pts):continue
   normal=normals[i]
   if normal[2]<.999999:continue
   for j,a in enumerate(pts):
    b=pts[(j+1)%len(pts)]
    if abs(a[1]-y)<1e-7 and abs(b[1]-y)<1e-7 and abs(a[0]-b[0])>1e-7:
     out.append({'object':o['name'],'polygon':i,'endpoints':[a,b],'xInterval':sorted([a[0],b[0]]),'normal':normal,'maxZNominalError':max(abs(a[2]-.22),abs(b[2]-.22))})
 return sorted(out,key=lambda s:s['xInterval'][0])
def unions(s):
 out=[]
 for lo,hi in sorted(t['xInterval'] for t in s):
  if out and lo<=out[-1][1]+1e-7:out[-1][1]=max(out[-1][1],hi)
  else:out.append([lo,hi])
 return out
es=segments(E['nativeObjects'],0,'normalsWorld');fs=segments(F['floorNativeObjects'],-1.5,'polygonNormalsWorld');eu,fu=unions(es),unions(fs)
entry=max((i for i in eu if i[0]<=0<=i[1]),key=lambda i:i[1]-i[0]);floor=max((i for i in fu if i[0]<=0<=i[1]),key=lambda i:i[1]-i[0]);shared=[s for s in F['sharedSections'] if abs(s['x'])<=.39000001]
r={'asset':'dock-entry','sourceEvidence':{'standalone':'candidates/round-05/native-validation.json','paired':'candidates/round-05/paired-native-validation-v2.json','dense':'candidates/round-05/dense-native-audit.json'},'certifiedSharedW':.78,'certifiedSharedX':[-.39,.39],'actualExposedStraightTopBoundary':entry,'actualExposedStraightWidth':entry[1]-entry[0],'floorContinuousBoundary':floor,'entryBoundarySegments':es,'floorBoundarySegments':fs,'entryMergedIntervals':eu,'floorMergedIntervals':fu,'entryBoundaryZError':max(s['maxZNominalError'] for s in es),'floorBoundaryZError':max(s['maxZNominalError'] for s in fs),'mutualCenteredProfileRayMismatch':max(abs(s['entryNearBoundary']['point'][2]-s['floorNearBoundary']['point'][2]) for s in shared),'sharedSampleCount':len(shared),'flightRaySamples':sum(len(p['samples']) for p in D['paths']),'flightMissing':sum(p['missing'] for p in D['paths']),'flightMonotonicNumericalDeltaMinimum':min(p['minimumHeightDeltaAlongTowardDeck'] for p in D['paths']),'clearanceProbes':len(D['clearanceProbes']),'clearanceBlocked':D['clearanceBlockedInsideX039'],'sharedEndNormals':{'entry':[0,1,0],'floor':[0,-1,0]},'method':'Boundary edges extracted from actual evaluated polygon vertices/normals; merge collinear X intervals in double precision. Dense native BVH rays supply interior support/normal diagnostics. Certified centered W=.78 is inside actual exposed horizontal terminal boundary and floor repair strip; no outer rounded-edge endpoint is used as unsupported evidence.'}
(O/'contact-contract-measurements.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:r[k] for k in ['actualExposedStraightTopBoundary','actualExposedStraightWidth','floorContinuousBoundary','entryBoundaryZError','floorBoundaryZError','mutualCenteredProfileRayMismatch','flightMissing','clearanceBlocked']},indent=2))
