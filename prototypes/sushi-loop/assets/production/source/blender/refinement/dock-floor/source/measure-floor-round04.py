"""Measure evaluated candidate and shared contact; never saves source geometry."""
import bpy,json,math,hashlib,bmesh
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent;OBJ=HERE.parent;OUT=OBJ/'candidates/round-04';root=bpy.data.objects['dock-floor__root'];root.location=(0,0,0);root.rotation_euler=(0,0,0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
meshes=[];vs=[];faces=[];records=[];zall=[];bbs={}
for o in bpy.data.collections['WarmSoft_dock-floor'].all_objects:
 if o.type!='MESH':continue
 e=o.evaluated_get(dg);m=e.to_mesh();points=[e.matrix_world@v.co for v in m.vertices];start=len(vs);vs+=points;faces += [tuple(start+i for i in p.vertices) for p in m.polygons];bm=bmesh.new();bm.from_mesh(m)
 bounds=[[min(v[i] for v in points) for i in range(3)],[max(v[i] for v in points) for i in range(3)]];bbs[o.name]=bounds
 records.append({'name':o.name,'matrixWorld':[list(r) for r in o.matrix_world],'evaluatedVertices':len(points),'evaluatedPolygons':len(m.polygons),'bounds':bounds,'nonmanifoldEdges':sum(not e.is_manifold for e in bm.edges),'looseVertices':sum(not v.link_edges for v in bm.verts),'zeroAreaFaces':sum(p.area<1e-12 for p in m.polygons),'materialSlots':[x.name for x in o.data.materials],'visible':not o.hide_render,'modifiers':[x.type for x in o.modifiers]});bm.free();e.to_mesh_clear()
bvh=BVHTree.FromPolygons(vs,faces,all_triangles=False,epsilon=1e-10)
def top(x,y):
 p,n,f,d=bvh.ray_cast(Vector((x,y,1)),Vector((0,0,-1)),2);return {'x':x,'y':y,'z':p.z if p else None,'normal':list(n) if n else None,'face':f}
# Evaluate dense exact seam, adjacent rows and nine occupancy support centers.
sections=[top(-.48+.96*i/192,y) for y in [-1.5+1e-7,-1.495,-1.49,-1.480001] for i in range(193)]
seam=[p for p in sections if p['y']==-1.5+1e-7]
actual_face=[]
for face in faces:
 ps=[vs[i] for i in face]
 if all(abs(v.y+1.5)<1e-6 for v in ps) and min(v.x for v in ps)<.48 and max(v.x for v in ps)>-.48:
  a=ps[1]-ps[0];b=ps[2]-ps[0];n=a.cross(b).normalized();actual_face.append({'vertices':[list(v) for v in ps],'normal':list(n)})
# Check actual boundary top edge segments cover all X of centered .96 flight.
segments=[]
for face in faces:
 for a,b in zip(face,face[1:]+face[:1]):
  p,q=vs[a],vs[b]
  if abs(p.y+1.5)<1e-6 and abs(q.y+1.5)<1e-6 and abs(p.z-.22)<1e-6 and abs(q.z-.22)<1e-6:segments.append(sorted([p.x,q.x]))
cover=sorted(x for x in segments if x[1]>-.48001 and x[0]<.48001);cursor=-.48;gaps=[]
for a,b in cover:
 if a>cursor+1e-5:gaps.append([cursor,a])
 cursor=max(cursor,b)
if cursor<.48-1e-5:gaps.append([cursor,.48])
resources=[{'name':i.name,'source':i.source,'packed':bool(i.packed_file),'filepath':i.filepath,'size':list(i.size)} for i in bpy.data.images if i.type!='RENDER_RESULT']
report={'asset':'dock-floor','project':str(Path(bpy.data.filepath).relative_to(OBJ)),'projectSHA256':sha(bpy.data.filepath),'measurement':'actual evaluated native mesh BVH and boundary-edge/face extraction; no raster/AABB substitute for shared boundary','rootObject':root.name,'rootMatrix':[list(r) for r in root.matrix_world],'nativeGeometry':records,'meshBounds':[[min(v[i] for v in vs) for i in range(3)],[max(v[i] for v in vs) for i in range(3)]],'contactSections':sections,'sharedBoundary':{'Y':-1.5,'Z':.22,'requiredSupportX':[-.48,.48],'actualEdges':segments,'facePolygons':actual_face,'coverageGaps':gaps,'maxTopError':max(abs(p['z']-.22) for p in seam if p['z'] is not None),'missingSamples':sum(p['z'] is None for p in sections),'maxTopNormalError':max(abs(p['normal'][2]-1) for p in seam if p['normal'])},'supportCellCenters':[top(x,y) for x in [-1,0,1] for y in [-1,0,1]],'materialIntegrity':{'images':resources,'allMaterialsUseNodes':all(m.use_nodes for m in bpy.data.materials),'targetImageUsedAsResource':False,'noGroundPlane':True},'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':o.data.size,'location':list(o.location)} for o in bpy.data.objects if o.type=='LIGHT'],'colorManagement':{'viewTransform':bpy.context.scene.view_settings.view_transform,'look':bpy.context.scene.view_settings.look,'exposure':bpy.context.scene.view_settings.exposure},'nativeCaptures':json.loads((OUT/'candidate-phases.json').read_text()),'preExistingNeighborSupportGaps':{'workshop-hut':.035,'submarine-yellow':.055,'scope':'Roots retained; later per-object repair, no contact certification'}}
(OUT/'native-validation.json').write_text(json.dumps(report,indent=2))
print(json.dumps({'bounds':report['meshBounds'],'sharedBoundary':{k:v for k,v in report['sharedBoundary'].items() if k not in ['actualEdges','facePolygons']},'meshIssues':[{k:r[k] for k in ['name','nonmanifoldEdges','looseVertices','zeroAreaFaces']} for r in records]},indent=2))
