import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parent;SOURCE=P/'original-library.blend'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='b1765262bfa897adf7e5de4f2b866cfc939430cf18539f3f7063859b9cff31c6'
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(SOURCE),link=False) as (a,b):
 b.collections=['S33_PROP_chef-blackboard'];b.actions=[x for x in a.actions if x.startswith('S33_NATIVE__chef-blackboard__')]
c=b.collections[0];s=bpy.context.scene;s.collection.children.link(c);c.hide_render=False;c.hide_viewport=False
for o in c.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
rig=json.loads((P/'resources/original-rig.json').read_text())
def pts(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
 try:return [ev.matrix_world@v.co for v in m.vertices]
 finally:ev.to_mesh_clear()
def bounds(v):return [list(map(min,zip(*v))),list(map(max,zip(*v)))]
records=[]
for clip,rec in rig['clips'].items():
 for a in rec['actions']:
  o=bpy.data.objects[a['ownerName']];act=bpy.data.actions[a['action']];o.animation_data_create();o.animation_data.action=act;o.animation_data.action_slot=next(t for t in act.slots if t.identifier==a['slotIdentifier'])
 for frame in range(1,rec['frames']+1):
  s.frame_set(frame);bpy.context.view_layer.update();v=[]
  for o in c.all_objects:
   if o.type=='MESH':v+=pts(o)
  face=bpy.data.objects['chef-blackboard__blank_dynamic_face'];fv=pts(face)
  records.append({'clip':clip,'frame':frame,'bounds':bounds(v),'rootMatrix':[list(r) for r in bpy.data.objects['chef-blackboard__root'].matrix_world],'faceMatrix':[list(r) for r in face.matrix_world],'faceFrontY':min(p.y for p in fv)})
(P/'source-animation-bounds.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'measurement':'Actual evaluated original mesh vertices from visible isolated original collection; all original action bindings','records':records},indent=2)+'\n')
print('ORIGINAL_MEASURED',len(records),records[0])
