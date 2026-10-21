import bpy,json,hashlib
from pathlib import Path
from mathutils import Matrix
B=Path(__file__).resolve().parents[1]
source=(B/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
bpy.ops.wm.open_mainfile(filepath=str(source))
cs=[c for c in bpy.data.collections if 'wall-middle' in c.name]
print('COLLECTIONS',[(c.name,len(c.all_objects)) for c in cs])
c=next(c for c in cs if any('wall_panel' in o.name for o in c.all_objects))
s=bpy.data.scenes.new('Wall middle source inspection');s.collection.children.link(c);bpy.context.window.scene=s;bpy.context.view_layer.update()
objs=[]
for o in c.all_objects:
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'matrix':[list(r) for r in o.matrix_world],'custom':dict(o.items())}
 if o.type=='MESH':
  pts=[o.matrix_world@v.co for v in o.data.vertices];d.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),bounds=[[min(p[i] for p in pts),max(p[i] for p in pts)]for i in range(3)],verts=[list(v.co) for v in o.data.vertices],faces=[list(p.vertices)for p in o.data.polygons],materials=[m.name for m in o.data.materials],modifiers=[{'name':m.name,'type':m.type}for m in o.modifiers])
 objs.append(d)
report={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'collection':c.name,'objects':objs,'cameras':[{'name':o.name,'matrix':[list(r)for r in o.matrix_world],'ortho_scale':o.data.ortho_scale,'shift_y':o.data.shift_y}for o in bpy.data.objects if o.type=='CAMERA'],'materials':{m.name:{'use_nodes':m.use_nodes,'nodes':[{'name':n.name,'type':n.type}for n in m.node_tree.nodes]if m.node_tree else []}for o in c.all_objects if o.type=='MESH' for m in o.data.materials}}
(B/'candidates/inspection/source.json').write_text(json.dumps(report,indent=2,default=str))
print('PARTS',[(o['name'],o.get('bounds'))for o in objs]);print('SOURCE',report['sha256'])
