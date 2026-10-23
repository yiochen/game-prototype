import bpy,json
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
HERE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(HERE/'resources/frozen-main-v1/project.blend'))
sc=bpy.context.scene;root=bpy.data.objects['submarine-yellow__root'];acts=json.loads(root['nativeActions'])
for owner,name in acts['upgraded-dock-ready'].items():
 o=bpy.data.objects[owner];a=bpy.data.actions[name];o.animation_data_create();o.animation_data.action=a;o.animation_data.action_slot=a.slots[0]
sc.frame_set(1);root.rotation_euler=(0,0,0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();o=bpy.data.objects['body__hull'];eo=o.evaluated_get(dg);me=eo.to_mesh();tree=BVHTree.FromPolygons([eo.matrix_world@v.co for v in me.vertices],[list(p.vertices) for p in me.polygons]);eo.to_mesh_clear()
rows=[]
for x in [.181,.186,.195,.205,.215,.225,.235,.244,.249]:
 for y in [.028,.034,.06,.1,.16,.22,.26,.286,.292]:
  p,n,face,d=tree.ray_cast(Vector((x,y,1)),Vector((0,0,-1)),2)
  rows.append({'mainXY':[x,y],'hullTop':p.z if p else None,'heightAboveSeat':p.z-.65 if p else None})
(HERE/'hull-clearance-samples.json').write_text(json.dumps(rows,indent=2))
print(json.dumps(rows,indent=2))
