import bpy,json,hashlib
from pathlib import Path
B=Path(__file__).resolve().parents[1]
source=(B/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
bpy.ops.wm.open_mainfile(filepath=str(source))
cs=[c for c in bpy.data.collections if 'wall-inner-corner' in c.name]
print('COLLECTIONS',[(c.name,len(c.all_objects)) for c in cs])
c=max(cs,key=lambda c:len(c.all_objects))
s=bpy.data.scenes.new('Inner corner source inspection');s.collection.children.link(c);bpy.context.window.scene=s;bpy.context.view_layer.update()
objs=[]
for o in c.all_objects:
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrix':[list(r) for r in o.matrix_world],'custom':dict(o.items())}
 if o.type=='MESH':
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();pts=[ev.matrix_world@v.co for v in me.vertices]
  d.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),bounds=[[min(p[i] for p in pts),max(p[i] for p in pts)]for i in range(3)],verts=[list(v.co) for v in o.data.vertices],faces=[list(p.vertices)for p in o.data.polygons],materials=[m.name for m in o.data.materials],modifiers=[{'name':m.name,'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)}for m in o.modifiers]);ev.to_mesh_clear()
 objs.append(d)
report={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'collection':c.name,'objects':objs}
(B/'candidates/inspection/source.json').write_text(json.dumps(report,indent=2,default=str))
print('PARTS',[(o['name'],o.get('bounds'),o.get('materials'))for o in objs])
