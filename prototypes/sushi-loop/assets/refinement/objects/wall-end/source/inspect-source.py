import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1]
source=(B/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
bpy.ops.wm.open_mainfile(filepath=str(source))
c=bpy.data.collections['S33_PROP_wall-end.001']
c.hide_render=False;c.hide_viewport=False
s=bpy.data.scenes.new('Inspect wall-end isolated');s.collection.children.link(c);bpy.context.window.scene=s
root=next(o for o in c.all_objects if o.type=='EMPTY');root.rotation_euler=(0,0,0);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
a=[]
for o in c.all_objects:
 r={'name':o.name,'type':o.type,'location':list(o.location),'matrix':list(map(list,o.matrix_world)),'custom':dict(o.items())}
 if o.type=='MESH':
  ev=o.evaluated_get(dg);v=[o.matrix_world@v.co for v in ev.data.vertices];r.update(vertices=[list(v.co)for v in o.data.vertices],faces=[list(p.vertices)for p in o.data.polygons],materials=[m.name for m in o.data.materials],bounds=[[min(p[i]for p in v),max(p[i]for p in v)]for i in range(3)],modifiers=[m.type for m in o.modifiers])
 a.append(r)
(B/'candidates/inspection/source.json').write_text(json.dumps({'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'collection':c.name,'root':root.name,'objects':a},indent=2))
print(json.dumps({'collection':c.name,'root':root.name,'objects':[{k:v for k,v in o.items()if k not in ['vertices','faces']}for o in a]},indent=2))
