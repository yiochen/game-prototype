import sys
sys.dont_write_bytecode=True
import json,math,hashlib
from pathlib import Path
BASE=Path(__file__).resolve().parent;E=BASE/'evidence'
d=json.loads((E/'native-inspection.json').read_text());out={'pathBase':'preparation-v1','measuredFrom':'resources/source/original.blend; enabled evaluated collection in evidence/native-inspection.json','family':{}}
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True).encode()).hexdigest()
for aid,rec in d['family'].items():
 o=next(o for o in rec['objects'] if 'continuous_core' in o['name']);vs=o['vertices'];r={'rootMatrix':rec['rootMatrix'],'coreBounds':o['bounds'],'endpointPorts':[],'actualGroundVertices':sorted({tuple(v) for v in vs if abs(v[2])<1e-6}),'decorBounds':{p['name']:p['bounds'] for p in rec['objects'] if p.get('bounds') and p!=o}}
 ports=json.loads(rec['rootProperties']['ports']);
 for port in ports:
  direct=port['direction'];axis=0 if direct in ['W','E'] else 1;plane=port['position'][axis];indices=[i for i,v in enumerate(vs) if abs(v[axis]-plane)<1e-6]
  # Stable native loft endpoint order, not AABB corners. N tangent+y implies cross-width=-x.
  profile=[[vs[i][1] if axis==0 else -vs[i][0],vs[i][2]] for i in indices]
  surfaces=[]
  for face in o['faces']:
   common=[i for i in face['vertices'] if i in indices]
   if len(common)==2 and len(face['vertices'])>2:
    material=o['materials'][face['material']];surfaces.append({'endpointVertexIndices':common,'crossSectionEdge':[profile[indices.index(i)] for i in common],'normalInCoreCoordinates':face['normal'],'flat':not face['smooth'],'materialSlot':face['material'],'materialName':material['name'],'materialGraphSHA256':digest(material)})
  r['endpointPorts'].append({'direction':direct,'normal':port['normal'],'position':port['position'],'nativeVertexIndices':indices,'orderedWidthZProfile':profile,'adjacentSurfaces':surfaces})
 r['materialCoordinateObservation']='Core source active BSDF uses world Z height ramp × constant albedo; normal-dependent view-tone exists in historical graph but is bypassed by current Faceted BSDF. No source core UVs or image textures.'
 out['family'][aid]=r
m=out['family']['reef-middle']['endpointPorts'];out['middleWEEquality']={'profileCoordinates':m[0]['orderedWidthZProfile']==m[1]['orderedWidthZProfile'],'surfaceNormals':[s['normalInCoreCoordinates'] for s in m[0]['adjacentSurfaces']]==[s['normalInCoreCoordinates'] for s in m[1]['adjacentSurfaces']],'surfaceMaterials':[s['materialGraphSHA256'] for s in m[0]['adjacentSurfaces']]==[s['materialGraphSHA256'] for s in m[1]['adjacentSurfaces']]}
# Same handed local cross-width at every true port. Actual source corner/end context only, no aesthetic judgment.
ref=m[0]['orderedWidthZProfile'];out['familyProfileEquality']={aid:{p['direction']:max(abs(a-b) for v,w in zip(p['orderedWidthZProfile'],ref) for a,b in zip(v,w)) for p in rec['endpointPorts']} for aid,rec in out['family'].items()}
(E/'finite-profile-audit.json').write_text(json.dumps(out,indent=2)+'\n');print(out['middleWEEquality']);print(out['familyProfileEquality'])
