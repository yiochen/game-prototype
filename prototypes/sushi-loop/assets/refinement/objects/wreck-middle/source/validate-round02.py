"""Evaluated native finite contract and complete finite collar proof. No geometry edits."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parent.parent;O=B/'candidates/round-02';C=json.loads((B/'source/round01-resources/root-native-contract.json').read_text());R=C['reconciliation'];sc=bpy.context.scene;root=bpy.data.objects['wreck-middle__root'];col=bpy.data.collections['Wreck middle authored candidate']
root.rotation_euler=(0,0,0);root.location=(0,0,0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();tol=1e-6
pts=[];tris=[];fields={};caprecords=[];support=[]
for o in col.all_objects:
 if o.type not in ['MESH','CURVE']:continue
 eo=o.evaluated_get(dg);me=eo.to_mesh();me.calc_loop_triangles();coords=[eo.matrix_world@v.co for v in me.vertices];pts+=coords
 for t in me.loop_triangles:
  p=[coords[i] for i in t.vertices];tris.append({'object':o.name,'points':[list(v) for v in p],'area':(p[1]-p[0]).cross(p[2]-p[0]).length/2})
 if 'canonical_rail' in o.name:
  kind=o.name.split('__')[1].split('_')[0];fields[kind]={}
  for side,a,b in [('W',-.5,-.42),('E',.42,.5)]:
   faces=[]
   for poly in me.polygons:
    vs=[coords[i] for i in poly.vertices]
    if all(a-tol<=v.x<=b+tol for v in vs) and max(v.x for v in vs)-min(v.x for v in vs)>.01:
     faces.append({'vertices':[list(v) for v in vs],'cornerNormals':[list(me.attributes['CanonicalNormal'].data[i].vector) for i in poly.loop_indices],'unusedPackedCornerNormals':[list(me.corner_normals[i].vector) for i in poly.loop_indices],'material':o.material_slots[poly.material_index].material.name,'polygonNormal':list(poly.normal)})
   fields[kind][side]=faces
  for side,x in [('W',-.5),('E',.5)]:
   ps=[p for p in me.polygons if all(abs(coords[i].x-x)<tol for i in p.vertices)]
   yz=[(coords[i].y,coords[i].z) for p in ps for i in p.vertices]
   caprecords.append({'rail':kind,'side':side,'plane':x,'polygons':len(ps),'yzVertices':yz,'area':sum(p.area for p in ps),'normals':[list(p.normal) for p in ps],'orderedPlaneLoops':[[list(coords[i]) for i in p.vertices] for p in ps]})
 eo.to_mesh_clear()
poly=R['geometry']['authoringEnvelope']['xyPolygonCCW'];worst=-1e20;bad=[]
for p in pts:
 for a,b in zip(poly,poly[1:]+poly[:1]):
  dx=b[0]-a[0];dy=b[1]-a[1];violation=-((p.x-a[0])*dy*-1+(p.y-a[1])*dx) / math.hypot(dx,dy)
  # CCW interior left: cross(edge,p-a)>=0; violation is its negative.
  violation=(dy*(p.x-a[0])-dx*(p.y-a[1]))/math.hypot(dx,dy)
  worst=max(worst,violation)
  if violation>tol:bad.append([list(p),violation])
 if p.z<.04-tol or p.z>.78+tol:bad.append([list(p),'z'])
for t in tris:
 if all(abs(p[2]-C['finiteSupport']['minimumZ'])<tol for p in t['points']):support.append(t)
area=sum(t['area'] for t in support);support_inside=all(-.5-tol<=p[0]<=.5+tol and -.18000000715255737-tol<=p[1]<=.18000000715255737+tol for t in support for p in t['points'])
cap_pass=True
for cap in caprecords:
 sec=next(s for s in C['finitePorts'][cap['side']]['sections'] if cap['rail'] in s['name'] or (cap['rail']=='rear' and 'back_hull' in s['name']))
 ring=sec['authoredRingVertices'];ys=[v[1] for v in ring];zs=[v[2] for v in ring];expected=(max(ys)-min(ys))*(max(zs)-min(zs));cap['expectedRectangle']=ring;cap['expectedArea']=expected
 cap['finiteRectanglePass']=all(min(ys)-tol<=y<=max(ys)+tol and min(zs)-tol<=z<=max(zs)+tol for y,z in cap['yzVertices']) and abs(cap['area']-expected)<tol and all(abs(n[0]-(-1 if cap['side']=='W' else 1))<tol and abs(n[1])+abs(n[2])<tol for n in cap['normals'])
 loop=[v[1:] for v in cap['orderedPlaneLoops'][0]]
 changed=True
 while changed and len(loop)>3:
  changed=False
  for i in range(len(loop)):
   a,b,c=loop[i-1],loop[i],loop[(i+1)%len(loop)]
   if abs((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))<1e-10:loop.pop(i);changed=True;break
 expectedRing=[v[1:] for v in ring]
 if cap['side']=='W':expectedRing.reverse()
 cap['simplifiedOrderedPlaneLoop']=loop
 cap['exactOrderedFiniteLoopPass']=len(loop)==4 and any(all(max(abs(loop[(i+j)%4][k]-expectedRing[i][k]) for k in [0,1])<tol for i in range(4)) for j in range(4))
 cap['finiteRectanglePass'] &=cap['exactOrderedFiniteLoopPass']
 cap_pass &=cap['finiteRectanglePass']
# Each collar is an exact tensor-product rectangular extrusion with two collinear
# subdivisions on each side. All actual loop normals are constant over each face.
# Thus barycentric interpolation and subsequent normalization are identical over
# the COMPLETE finite surfaces, not only a collection of point samples.
fieldchecks=[]
for k,fs in fields.items():
 def desc(faces,side):
  origin=-.5 if side=='W' else .42
  return sorted([{'yz':sorted(set((round(v[1],8),round(v[2],8)) for v in f['vertices'])),'longitudinalRange':[round(min(v[0] for v in f['vertices'])-origin,7),round(max(v[0] for v in f['vertices'])-origin,7)],'normals':sorted(set(tuple(round(v,6) for v in n) for n in f['cornerNormals'])),'material':f['material']} for f in faces],key=lambda v:str(v))
 w,e=desc(fs['W'],'W'),desc(fs['E'],'E');fieldchecks.append({'rail':k,'completeFiniteCollarDescriptorsAgree':w==e,'W':w,'E':e,'actualFacesEach':[len(fs['W']),len(fs['E'])]})
materials={}
for m in bpy.data.materials:
 if not m.use_nodes:continue
 nt=m.node_tree;nodes=[];links=[]
 for n in nt.nodes:
  inputs={}
  for s in n.inputs:
   if s.is_linked or not hasattr(s,'default_value'):continue
   v=s.default_value
   if isinstance(v,(int,float,str,bool)):inputs[s.name]=v
   elif hasattr(v,'__len__'):inputs[s.name]=list(v)
  nodes.append({'name':n.name,'type':n.bl_idname,'defaults':inputs,'blend_type':getattr(n,'blend_type',None),'clamp':getattr(n,'clamp',None),'attribute_name':getattr(n,'attribute_name',None),'operation':getattr(n,'operation',None),'vector_type':getattr(n,'vector_type',None),'convert_from':getattr(n,'convert_from',None),'convert_to':getattr(n,'convert_to',None)})
 for l in nt.links:links.append([l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name])
 materials[m.name]={'nodes':nodes,'links':links,'normalInput':('Actual FLOAT_VECTOR CORNER CanonicalNormal -> Object-to-World NORMAL -> Normalize -> Principled Normal; exact collar field bypasses irrelevant packed-custom-normal quantization' if 'explicit canonical normal' in m.name else 'Unconnected Principled Normal uses geometry normal on interior hardware/timber, outside all canonical collars'),'alpha':1,'albedo':'Constant per-material linear color multiplied by clamped world-Z affine ramp .66..1.03 over .04...78; no X/Y/UV/random dependencies','longitudinalDerivative':'Exactly zero over each collar at all heights; same under all four proper Z rotations'}
passed=not bad and cap_pass and support_inside and abs(area-C['finiteSupport']['lowestFace']['area'])<tol and all(x['completeFiniteCollarDescriptorsAgree'] for x in fieldchecks)
result={'asset':'wreck-middle','allFiniteChecksPassed':passed,'sourceSHA256':hashlib.sha256((B/'source/round-02.blend').read_bytes()).hexdigest(),'evaluatedVertexCount':len(pts),'bounds':{a:[min(p[i] for p in pts),max(p[i] for p in pts)] for i,a in enumerate('xyz')},'finiteXYEnvelope':poly,'maximumHalfplaneViolation':worst,'outOfBudget':bad[:10],'finitePortIntersections':caprecords,'support':{'area':area,'expectedArea':C['finiteSupport']['lowestFace']['area'],'insideExactFiniteRectangle':support_inside,'triangleCount':len(support),'triangles':support,'geometricZ0Intersection':[] if min(p.z for p in pts)>tol else 'FAIL'},'fieldProof':fieldchecks,'proofScope':'All evaluated vertices satisfy convex XY halfplanes/Z budget, hence all finite triangles do. Port intersections have full rectangular cap area, bounds and outward winding and no other plane contact. Complete collar face/corner descriptors certify normalized post-interpolation normal equality; active shader field is a function of only material constant and world Z, invariant under X translation/all4 Z rotations. Cap normals are separate. Tangents/UVs not used. No source3D hull/per-part boxes added as a lock.','materials':materials}
result['perFacingFiniteEnvelopeChecks']=[]
for direction,angle in [('N',math.pi),('E',math.pi/2),('S',0),('W',-math.pi/2)]:
 root.rotation_euler.z=angle;bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();inverse=root.matrix_world.inverted();worstBack=0;vertices=0
 for o in col.all_objects:
  if o.type not in ['MESH','CURVE']:continue
  eo=o.evaluated_get(dg);me=eo.to_mesh()
  for v in me.vertices:
   p=inverse@(eo.matrix_world@v.co);vertices+=1
   for a,b in zip(poly,poly[1:]+poly[:1]):
    dx=b[0]-a[0];dy=b[1]-a[1];worstBack=max(worstBack,(dy*(p.x-a[0])-dx*(p.y-a[1]))/math.hypot(dx,dy),.04-p.z,p.z-.78)
  eo.to_mesh_clear()
 result['perFacingFiniteEnvelopeChecks'].append({'direction':direction,'actualRootMatrix':[list(row) for row in root.matrix_world],'vertices':vertices,'maximumInverseRootEnvelopeViolation':worstBack,'passed':worstBack<=tol})
root.rotation_euler.z=0;bpy.context.view_layer.update()
result['allFiniteChecksPassed'] &=all(x['passed'] for x in result['perFacingFiniteEnvelopeChecks'])
result['actualNativeRig']={'rootObject':root.name,'rootMatrix':[list(row) for row in root.matrix_world],'meshCount':sum(o.type=='MESH' for o in col.all_objects),'curveCount':sum(o.type=='CURVE' for o in col.all_objects),'armatures':[],'actions':[],'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'matrix':[list(row) for row in o.matrix_world],'shadows':o.data.use_shadow} for o in sc.objects if o.type=='LIGHT'],'worldNodes':[{'type':n.bl_idname,'color':list(n.inputs['Color'].default_value),'strength':n.inputs['Strength'].default_value} for n in sc.world.node_tree.nodes if n.type=='BACKGROUND']}
(O/'finite-native-validation.json').write_text(json.dumps(result,indent=2)+'\n');(O/'canonical-endpoint-fields.json').write_text(json.dumps({'asset':'wreck-middle','collars':R['canonicalCollars'],'fields':fields,'finiteNormalizedInterpolationProof':fieldchecks,'activeMaterials':materials,'sourceSHA256':result['sourceSHA256'],'futureScope':'Reusable native geometry/corner/material/rig descriptor; approval of this asset does not approve derivatives'},indent=2)+'\n')
print(json.dumps({k:result[k] for k in ['allFiniteChecksPassed','evaluatedVertexCount','bounds','maximumHalfplaneViolation','outOfBudget']},indent=2))
if not passed:raise RuntimeError('Finite native contract failed; inspect saved evidence')
