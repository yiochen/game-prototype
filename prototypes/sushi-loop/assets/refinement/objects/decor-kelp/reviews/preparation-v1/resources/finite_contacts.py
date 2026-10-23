import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
BASE=Path(__file__).resolve().parent;OUT=BASE.parent/'evidence';data=json.loads((OUT/'native-sampling.json').read_text());samples=[s for s in data['samples']if s['direction']=='S'];base=[g for g in samples[0]['geometry']if 'reef rubble'in g['name']]
def bvh(g):return BVHTree.FromPolygons([Vector(v)for v in g['verticesWorld']],g['polygons'])
def signed(tree,p):
 co,n,index,d=tree.find_nearest(Vector(p));return {'distance':d,'signedNormalDistance':(Vector(p)-co).dot(n),'nearest':list(co)}
def center(g):return sum((Vector(v)for v in g['verticesWorld'][:7]),Vector())/7
polys=[]
for g in base:
 for p in g['polygons']:
  vs=[g['verticesWorld'][i]for i in p]
  if all(abs(v[2])<1e-8 for v in vs):polys.append({'owner':g['name'],'points':[v[:2]for v in vs]})
def inside(p,poly):
 c=False;x,y=p
 for a,b in zip(poly,poly[1:]+poly[:1]):
  if(a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:c=not c
 return c
n=512;covered=sum(any(inside((-.5+(x+.5)/n,-.5+(y+.5)/n),p['points'])for p in polys)for y in range(n)for x in range(n))
contacts=[]
for s in samples:
 geo={g['name']:g for g in s['geometry']};trees=[bvh(g)for g in base]
 for g in s['geometry']:
  if 'ribbon'not in g['name']:continue
  c=center(g)
  if g['name'].endswith(' fork'):
   own=g['name'][:-5];nearest=signed(bvh(geo[own]),c);record={'kind':'branch-to-own-primary','interfaceCenter':list(c),'primary':own,**nearest}
  else:
   nearest=[signed(t,c)for t in trees];record={'kind':'primary-root-in-finite-rubble','interfaceCenter':list(c),'nearestPerRubble':nearest,'insideAtLeastOne':any(x['signedNormalDistance']<=0 for x in nearest)}
  contacts.append({'nativeFrame':s['nativeFrame'],'owner':g['name'],**record})
closure=[]
first,last=samples[0],samples[-1]
for a,b in zip(first['geometry'],last['geometry']):closure.append({'owner':a['name'],'maxWorldVertexDelta':max((Vector(x)-Vector(y)).length for x,y in zip(a['verticesWorld'],b['verticesWorld']))})
(OUT/'finite-contact-and-closure.json').write_text(json.dumps({'scope':'Unadapted logical native geometry, actual finite bottom faces and interface cap centroids; adapter changes screen projection and is audited separately. No full opaque1x1 rule.','groundFaces':polys,'sampledUnionArea':covered/(n*n),'areaMethod':'512x512 center-sampled union of actual finite z=0 mesh faces over1x1 logical cell, resolution error approx perimeter/512; not AABB.','contacts':contacts,'closureFrame1to13':closure,'limits':'Signed nearest-face-normal test at interface center establishes embedding for this simple closed source geometry, not all-surface manifold overlap certification. Future redesigned roots/branches require native intersection or equivalent actual finite-contact evidence.'},indent=2)+'\n')
print(json.dumps({'groundUnionArea':covered/(n*n),'primaryContactFailures':sum(not c['insideAtLeastOne']for c in contacts if c['kind']=='primary-root-in-finite-rubble'),'branchCentersOutside':sum(c['signedNormalDistance']>0 for c in contacts if c['kind']=='branch-to-own-primary'),'closureMax':max(x['maxWorldVertexDelta']for x in closure)}))
