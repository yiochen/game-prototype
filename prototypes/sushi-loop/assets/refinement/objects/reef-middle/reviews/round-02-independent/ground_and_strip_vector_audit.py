"""Independent saved-source finite ground and exact three-module capture; no file saves."""
import sys
sys.dont_write_bytecode=True
import bpy, math, json, hashlib, collections
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parent; E=B/'evidence'; SOURCE=B/'resources/source/round-02.blend'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE)); sc=bpy.context.scene
col=bpy.data.collections['reef-middle']; root=bpy.data.objects['reef-middle__root']; root.rotation_euler.z=0
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
core=next(o for o in col.all_objects if 'continuous_core' in o.name);ev=core.evaluated_get(dg);me=ev.to_mesh();me.calc_loop_triangles()
mat=root.matrix_world.inverted()@ev.matrix_world; pts=[mat@v.co for v in me.vertices]
bottom=[t for t in me.loop_triangles if all(abs(pts[i].z)<1e-6 for i in t.vertices)]
area=sum(abs((pts[t.vertices[1]]-pts[t.vertices[0]]).cross(pts[t.vertices[2]]-pts[t.vertices[0]]).z)/2 for t in bottom)
edgeuse=collections.Counter(tuple(sorted((p.vertices[i],p.vertices[(i+1)%len(p.vertices)]))) for p in me.polygons for i in range(len(p.vertices)))
bottomids={i for t in bottom for i in t.vertices}; bpts=[pts[i] for i in bottomids]
assert abs(area-.76)<1e-6
assert all(-.5-1e-6<=v.x<=.5+1e-6 and -.38-1e-6<=v.y<=.38+1e-6 and abs(v.z)<1e-6 for v in bpts)
assert all(n==2 for n in edgeuse.values()), dict(collections.Counter(edgeuse.values()))
for x in [-.5,.5]:
 for y in [-.38,.38]:assert any((v-Vector((x,y,0))).length<1e-6 for v in bpts)
report={'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
 'finiteGround':{'expectedRectangle':[-.5,-.38,.5,.38],'planeZ':0,'evaluatedBottomTriangleArea':area,'triangleCount':len(bottom),'triangles':[[list(pts[i]) for i in t.vertices] for t in bottom],'allFourCornersPresent':True,'allBottomVerticesInsideRectangle':True,'closedCoreEdgeIncidenceHistogram':dict(collections.Counter(edgeuse.values()))},
 'staticObjectResources':[{'name':o.name,'objectAnimation':bool(o.animation_data),'dataAnimation':bool(getattr(o.data,'animation_data',None))} for o in sc.objects],
 'materialAnimation':[{'name':m.name,'animation':bool(m.animation_data),'nodeTreeAnimation':bool(m.node_tree.animation_data) if m.node_tree else False} for m in bpy.data.materials],
 'worldAnimation':bool(sc.world.animation_data) or bool(sc.world.node_tree.animation_data),
 'sourceFrame':sc.frame_current,'strips':[],
 'method':'Only reopen saved source; ground evaluated before ephemeral exact module copies. No construction recipe, .blend save, art or production changes. Camera frame expands with same unit scale/projection and registered strip root.'}
assert not any(x['objectAnimation'] or x['dataAnimation'] for x in report['staticObjectResources'])
assert not any(x['animation'] or x['nodeTreeAnimation'] for x in report['materialAnimation']) and not report['worldAnimation']
ev.to_mesh_clear()
copies=[]
for offset in [-1,1]:
 cc=bpy.data.collections.new('independent exact source copy '+str(offset));sc.collection.children.link(cc);mapping={}
 for o in col.objects:
  n=o.copy();cc.objects.link(n);mapping[o]=n
 for o,n in mapping.items():
  if o.parent in mapping:n.parent=mapping[o.parent]
 copies.append((offset,mapping[root]))
cam=sc.camera;sc.render.resolution_x=896;sc.render.resolution_y=1216;sc.render.resolution_percentage=100
cam.data.ortho_scale=3.5;cam.data.shift_x=0;cam.data.shift_y=0;bpy.context.view_layer.update()
def px(v):
 p=world_to_camera_view(sc,cam,Vector(v));return Vector((p.x*sc.render.resolution_x,(1-p.y)*sc.render.resolution_y))
origin=px((0,0,0));cam.data.shift_y=1;bpy.context.view_layer.update();delta=px((0,0,0))[1]-origin[1];cam.data.shift_y=(752-origin[1])/delta;bpy.context.view_layer.update()
report['stripCamera']={'dimensions':[896,1216],'rootPixels':list(px((0,0,0))),'worldMatrix':[list(r) for r in cam.matrix_world],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'orthoScale':cam.data.ortho_scale,'shift':[cam.data.shift_x,cam.data.shift_y],'filterSize':sc.render.filter_size}
for d,angle in {'N':math.pi,'E':math.pi/2,'S':0,'W':-math.pi/2}.items():
 root.rotation_euler.z=angle
 for offset,r in copies:r.rotation_euler.z=angle;r.location=(offset*math.cos(angle),offset*math.sin(angle),0)
 sc.frame_set(1);bpy.context.view_layer.update();p=E/('independent-vector-three-joined-'+d+'.png');sc.render.filepath=str(p);bpy.ops.render.render(write_still=True)
 report['strips'].append({'direction':d,'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'actualRootMatrices':[{'offset':i,'matrix':[list(row) for row in r.matrix_world]} for i,r in [(0,root)]+copies]})
(E/'independent-ground-and-strip-vector-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print('INDEPENDENT_GROUND_AND_STRIPS_COMPLETE')
