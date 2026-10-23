"""Reproduce original native per-asset capture from immutable own snapshots.
Run Blender -b resources/original-source.blend --python baseline_source.py.
Writes evidence only; never saves a blend or changes production bytes.
"""
import bpy, json, math, importlib.util, hashlib, struct
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

OUT=Path(__file__).resolve().parent
RES=OUT/'resources'; BASELINE=OUT/'source-baseline'; BASELINE.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('own_capture',RES/'capture_runtime.py')
cap=importlib.util.module_from_spec(spec);spec.loader.exec_module(cap)
coll=bpy.data.collections.get('S33_PROP_rock-wall-end.001');assert coll
root=bpy.data.objects.get('rock-wall-end__root.001');assert root
sc=cap.scene();sc.name=cap.SCENE_NAME
sc.collection.children.link(coll);coll.hide_render=False;coll.hide_viewport=False
for ob in coll.all_objects:ob.hide_render=False;ob.hide_viewport=False;ob.hide_set(False)
record=cap.configure_camera('square-top-front-oblique',(192,352),(96,256),4)
sc.frame_set(1);root.location=(0,0,0);root.rotation_euler=(0,0,0);root.scale=(1,1,1)
bpy.context.view_layer.update()

def vv(v):return [float(x) for x in v]
def mesh_record(ob):
 ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
 points=[ev.matrix_world@v.co for v in me.vertices]
 rec={'name':ob.name,'location':vv(ob.location),'matrix':[list(row) for row in ob.matrix_world],'vertices':len(ob.data.vertices),'polygons':len(ob.data.polygons),'evaluatedVertices':len(me.vertices),'evaluatedPolygons':len(me.polygons),'bounds':{'min':[min(v[i] for v in points) for i in range(3)],'max':[max(v[i] for v in points) for i in range(3)]},'modifiers':[{'type':m.type,'name':m.name,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in ob.modifiers],'uvLayers':[u.name for u in ob.data.uv_layers],'smoothPolygons':sum(p.use_smooth for p in me.polygons),'materials':[{'name':m.name,'nodes':[n.type for n in m.node_tree.nodes] if m.use_nodes else []} for m in ob.data.materials if m]}
 ev.to_mesh_clear();return rec

meshes=[mesh_record(ob) for ob in coll.all_objects if ob.type=='MESH']
core=next(ob for ob in coll.all_objects if 'full_width_continuous_crag' in ob.name)
endpoint=[vv(v.co) for v in core.data.vertices if abs(v.co.x+.5)<1e-6]
profile=sorted(set(tuple(v[1:]) for v in endpoint))
audit={'purpose':'newly rendered diagnostic baseline from exact original source, original capture pipeline; not a candidate','sourceBlendSHA256':hashlib.sha256((RES/'original-source.blend').read_bytes()).hexdigest(),'sourceCaptureRuntimeSHA256':hashlib.sha256((RES/'capture_runtime.py').read_bytes()).hexdigest(),'collection':coll.name,'root':root.name,'rootMatrix':[list(row) for row in root.matrix_world],'capture':record,'meshes':meshes,'aggregateBounds':{'min':[min(m['bounds']['min'][i] for m in meshes) for i in range(3)],'max':[max(m['bounds']['max'][i] for m in meshes) for i in range(3)]},'westCoreCutVertices':endpoint,'westCoreProfileYThenZSorted':profile,'declaredPorts':json.loads(root['ports']),'timing':{'frame':1,'static':True,'frames':1,'fps':12,'loop':False},'resourceOwnership':{'usedImages':[],'libraries':[],'note':'Two packed food image resources exist elsewhere in b176 library but own stone meshes use no image textures or linked libraries.'},'views':{}}
for face,deg in {'S':0,'E':90,'N':180,'W':-90}.items():
 root.rotation_euler.z=math.radians(deg);bpy.context.view_layer.update()
 sc.render.filepath=str(BASELINE/f'native-{face}.png');bpy.ops.render.render(write_still=True)
 audit['views'][face]={'rotationDegrees':deg,'matrix':[list(row) for row in root.matrix_world],'file':f'source-baseline/native-{face}.png'}
(OUT/'source-baseline-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
print('SOURCE_BASELINE_DONE')
