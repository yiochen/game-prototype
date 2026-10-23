import bpy,json,math
from pathlib import Path
from mathutils import Matrix
BASE=Path(__file__).resolve().parents[1]
col=bpy.data.collections['S33_PROP_garbage-shelving']; root=bpy.data.objects['garbage-shelving__root']
scene=bpy.context.scene
for o in scene.objects:o.hide_render=o.name not in {x.name for x in col.all_objects}
for o in col.all_objects:o.hide_render=False
record={'collection':col.name,'root':root.name,'rootMatrix':[list(x) for x in root.matrix_world],'objects':[],'cameras':[]}
for o in col.all_objects:
 if o.type!='MESH':continue
 record['objects'].append({'name':o.name,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'dimensions':list(o.dimensions),'parent':o.parent.name if o.parent else None,'vertices':[list(v.co) for v in o.data.vertices],'materials':[m.name for m in o.data.materials],'animation':o.animation_data.action.name if o.animation_data and o.animation_data.action else None})
for o in bpy.data.objects:
 if o.type=='CAMERA':record['cameras'].append({'name':o.name,'matrix':[list(x) for x in o.matrix_world],'ortho':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y]})
record['actions']=[{'name':a.name,'slots':[s.identifier for s in a.slots]} for a in bpy.data.actions if 'garbage-shelving__' in a.name]
(BASE/'source/independent-native-observation.json').write_text(json.dumps(record,indent=2))
print('NATIVE_INSPECT',json.dumps(record['objects'],indent=2))
