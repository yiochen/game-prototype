import sys
sys.dont_write_bytecode=True
import json, math, hashlib
from pathlib import Path
from collections import Counter
B=Path(__file__).resolve().parents[1]
s=json.loads((B/'evidence/original-native-evaluated.json').read_text());a=json.loads((B/'evidence/canonical-native.json').read_text())
core=next(o for o in s['objects'] if 'continuous_core' in o['name']);can=next(o for o in a['geometry'] if 'continuous_core' in o['name'])
profile=[[-.38,0],[.38,0],[.38,.2],[.25,.4],[.08,.44],[-.14,.35],[-.30,.4],[-.38,.2]]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(p,q):return max(abs(x-y) for x,y in zip(p,q))<1e-5
sourceRing=[v for v in core['vertices_world'] if abs(v[0]+.5)<1e-6]
assert len(sourceRing)==8
assert all(close(v,[-.5,*p]) for v,p in zip(sourceRing,profile))
verts=core['vertices_world'];edges=Counter()
area=0;ground=[]
for f in core['faces']:
 for i,j in zip(f,f[1:]+f[:1]):edges[tuple(sorted((i,j)))]+=1
 vs=[verts[i] for i in f]
 if all(abs(v[2])<1e-6 for v in vs):
  ar=abs(sum(p[0]*q[1]-q[0]*p[1] for p,q in zip(vs,vs[1:]+vs[:1])))/2;area+=ar;ground.append({'vertices':vs,'area':ar})
assert all(v==2 for v in edges.values())
assert abs(area-.84*.76)<1e-6
mats={m['name']:m for m in a['materials']};fields=[]
for j,(p,q) in enumerate(zip(profile,profile[1:]+profile[:1])):
 dy=q[0]-p[0];dz=q[1]-p[1];length=math.hypot(dy,dz);normal=[0,dz/length,-dy/length]
 ts=[t for t in can['triangles'] if all(v[0]>=.42-1e-6 for v in t['vertices']) and not all(abs(v[0]-.5)<1e-6 for v in t['vertices']) and all(any(close([v[1],v[2]],r) for r in (p,q)) for v in t['vertices'])]
 assert len(ts)==2,(j,len(ts))
 names={t['material'] for t in ts};assert len(names)==1
 err=max(abs(n[k]-normal[k]) for t in ts for n in t['cornerNormals'] for k in range(3));assert err<1e-6
 name=next(iter(names));mat=mats[name];bsdf=next(n for n in mat['nodes'] if n['type']=='BSDF_PRINCIPLED');ramp=next(n['ramp'] for n in mat['nodes'] if 'ramp' in n)
 def rgba(z):
  l,r=ramp['elements'];f=(z-l['position'])/(r['position']-l['position']);f=min(1,max(0,f));return [x+(y-x)*f for x,y in zip(l['color'],r['color'])]
 fields.append({'edgeIndex':j,'startYZ':p,'endYZ':q,'normal':normal,'actualCanonicalAdjacentTriangleCount':len(ts),'actualCornerNormalMaxError':err,'material':name,'actualMaterialGraph':mat,'linearAlbedoSamples':[{'t':t,'z':p[1]+t*dz,'rgba':rgba(p[1]+t*dz)} for t in [0,.25,.5,.75,1]],'roughness':bsdf['inputs']['Roughness'],'specularIORLevel':bsdf['inputs']['Specular IOR Level']})
facings={}
for d,ang in [('S',0),('E',math.pi/2),('N',math.pi),('W',-math.pi/2)]:
 co=math.cos(ang);si=math.sin(ang)
 def rot(v):return [co*v[0]-si*v[1],si*v[0]+co*v[1],v[2]]
 def clean(v):return [0 if abs(x)<1e-12 else x for x in v]
 port=clean(rot([-.5,0,0]));normal=clean(rot([-1,0,0]));sections=[clean(rot([-.5,*p])) for p in profile];rel=[128*port[0],-128*port[1]]
 facings[d]={'rootAngleRadians':ang,'worldPortCenter':port,'worldPortOutwardNormal':normal,'orderedProfileXYZ':sections,'logicalPortRootRelativeXY':rel,'straightCanonicalMiddleRoot':clean(rot([-1,0,0])),'endRoot':[0,0,0],'finiteGroundCorners':[clean(rot([x,y,0])) for x,y in [(-.5,-.38),(.34,-.38),(.34,.38),(-.5,.38)]]}
report={'asset':'reef-end','authoritativeSource':'evidence/original-native-evaluated.json','invalidRawMeasurement':'evidence/original-native.json retains stale excluded-collection matrix_world; not an envelope measurement','sourcePort':{'direction':'W','planeX':-.5,'orderedYZ':profile,'actualXYZ':sourceRing,'normal':[-1,0,0],'capX':.34,'capIsNotConnector':True},'sourceGround':{'law':'Finite rectangle X[-.5,.34] x Y[-.38,.38] at Z0; not wholecell opaque floor. Exact support boundary and baseline retained.','area':area,'expectedArea':.6384,'bottomPolygons':ground,'closedCoreEdgeIncidence':dict(Counter(edges.values()))},'envelopes':{'nominalFootprintCells':[1,1],'coreMeasuredXYZ':[[-.5,.3400000035762787],[-.3799999952316284,.3799999952316284],[0,.4399999976158142]],'allVisibleMeasuredXYZ':[[-.5,.3400000035762787],[-.3799999952316284,.3799999952316284],[0,.6599999666213989]],'sourceDeclaredMaximumHeight':.68,'proposedPermittedEnvelopeXYZ':[[-.5,.34],[-.38,.38],[0,.68]],'elevatedDecorationBeyondNominalCell':False,'reconciliation':'reef-end has no out-of-cell original elevated decoration. Do not inherit reef-middle full X[-.5,.5] span or corner protrusion bounds. Useful interior/cap/coral improvements may use .68declared clearance without extending finite footprint or connector.'},'canonical':{'sourceSHA256':a['sourceSHA256'],'normalAlbedoEndpointAdoption':fields,'lighting':a['lights'],'render':a['render'],'camera':a['camera'],'canonicalCollarReference':'Canonical E surface band local X[.42,.5], mapped by X-1 to derivative W band[-.58,-.5]. Derivative interior approach X[-.5,-.42] must continue same ordered section/material/normal law at the cut; do not mirror width or swap profile winding. Mesh topology remains free.','materialsNotNames':'Use actual linked node graphs and numeric roughness/specular/ramp field in the saved audit; names/profile IDs alone insufficient.'},'facings':facings,'technicalLimits':['No derivative candidate exists; this is measurement/proposed contract only.','Source visual replay/float rounding do not prove style or mixed-asset seam continuity.','Core cap and source internal rings are observations, not topology/partcount locks; root must reconcile/freeze proposed ground/envelope limits.']}
(B/'technical-findings.json').write_text(json.dumps(report,indent=2)+'\n')
print('GROUND_AREA',area,'FIELDS',[(f['edgeIndex'],f['normal'],f['material']) for f in fields]);print('FACINGS',facings)
