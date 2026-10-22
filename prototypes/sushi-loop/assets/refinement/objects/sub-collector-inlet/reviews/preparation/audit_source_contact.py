import bpy,json,pathlib
from mathutils import Vector
O=pathlib.Path(__file__).resolve().parent;s=bpy.context.scene;root=bpy.data.objects['submarine-yellow__root'];root.rotation_euler.z=0;s.frame_set(1);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();y=-.45399999618530273
seat=next(x for x in json.loads((O/'frozen-main-native-audit.json').read_text())['parts'] if x['name']=='body__collector_contact_seat')['finiteFaces'][0];sb=seat['bounds']
def hull(points):
 p=sorted(set((round(v[0],9),round(v[1],9)) for v in points))
 def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
 lo=[]
 for v in p:
  while len(lo)>=2 and cross(lo[-2],lo[-1],v)<=0:lo.pop()
  lo.append(v)
 hi=[]
 for v in reversed(p):
  while len(hi)>=2 and cross(hi[-2],hi[-1],v)<=0:hi.pop()
  hi.append(v)
 return lo[:-1]+hi[:-1]
def clip(poly,axis,k,sign):
 out=[]
 for a,b in zip(poly,poly[1:]+poly[:1]):
  ai=sign*(a[axis]-k)>=-1e-10;bi=sign*(b[axis]-k)>=-1e-10
  if ai:out.append(a)
  if ai!=bi:
   t=(k-a[axis])/(b[axis]-a[axis]);out.append(tuple(a[i]+t*(b[i]-a[i]) for i in range(2)))
 return out
def area(poly):return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(poly,poly[1:]+poly[:1])))/2 if len(poly)>=3 else 0
records=[]
for o in bpy.data.collections['S33_PROP_collector_inlet.001'].all_objects:
 if o.type!='MESH':continue
 eo=o.evaluated_get(dg);me=eo.to_mesh();ps=[eo.matrix_world@v.co for v in me.vertices];ints=[]
 for e in me.edges:
  a,b=[ps[i] for i in e.vertices];aa=a.y-y;bb=b.y-y
  if abs(aa)<1e-8:ints.append((a.x,a.z))
  if aa*bb<0:
   p=a+(b-a)*(-aa/(bb-aa));ints.append((p.x,p.z))
 if len(ints)>=3:
  h=hull(ints);p=h
  for axis,k,sign in [(0,sb[0][0],1),(0,sb[1][0],-1),(1,sb[0][2],1),(1,sb[1][2],-1)]:p=clip(p,axis,k,sign)
  records.append({'name':o.name,'finiteNativePlaneSectionXZ':h,'intersectionWithActualSeatFaceXZ':p,'finiteIntersectionAreaWorld':area(p),'qualifier':'Convex native inlet-frame section; hull is valid for original convex beveled box, not a generic candidate nonconvex contact method.'})
 eo.to_mesh_clear()
(O/'source-finite-contact-audit.json').write_text(json.dumps({'authority':seat,'planeMainY':y,'method':'Intersect evaluated native mesh edges with actual finite seat front plane, then clip convex source section to the real native finite face. Actual geometry/plane sections, not AABB overlap.','records':records,'qualification':'Source preparation only. Original source has purposeful finite insertion but fails forward/top reservation. Candidate must provide its own finite surface/section proof, including any nonconvex/curved contact geometry.'},indent=2)+'\n');print(json.dumps(records,indent=2))
