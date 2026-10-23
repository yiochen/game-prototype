import bpy,json
from mathutils import Vector
from pathlib import Path
p=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype/prototypes/sushi-loop/assets/refinement/objects/wall-outer-corner')
s=(p/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
bpy.ops.wm.open_mainfile(filepath=str(s))
cs=[c for c in bpy.data.collections if 'wall-outer-corner' in c.name]
c=cs[0];print('COLLECTION',c.name)
c.hide_render=False;c.hide_viewport=False
scene=bpy.data.scenes.new('Inspect outer corner');scene.collection.children.link(c);bpy.context.window.scene=scene
root=next(o for o in c.all_objects if o.type=='EMPTY');root.rotation_euler=(0,0,0);bpy.context.view_layer.update()
rec={'collection':c.name,'root':root.name,'objects':[]}
for o in c.all_objects:
 if o.type!='MESH':continue
 pts=[o.matrix_world@v.co for v in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).data.vertices]
 item={'name':o.name,'matrix':[list(r)for r in o.matrix_world],'vertices':[list(v.co)for v in o.data.vertices],'faces':[list(f.vertices)for f in o.data.polygons],'bounds':[[min(v[i]for v in pts),max(v[i]for v in pts)]for i in range(3)],'materials':[m.name for m in o.data.materials],'modifiers':[m.type for m in o.modifiers]}
 rec['objects'].append(item)
 print(o.name,item['bounds'],len(o.data.vertices),len(o.data.polygons),item['materials'],item['modifiers'])
(p/'source/source-inspection.json').write_text(json.dumps(rec,indent=2))

