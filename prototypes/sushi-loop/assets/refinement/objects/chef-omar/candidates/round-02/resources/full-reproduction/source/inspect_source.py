import bpy,json
from pathlib import Path
p=Path(__file__).parent
root=bpy.data.objects['chef_omar__ground_root.001']
coll=min([c for c in bpy.data.collections if root in list(c.all_objects)],key=lambda c:len(c.all_objects))
sc=bpy.data.scenes.new('Omar independent source inspection');bpy.context.window.scene=sc;sc.collection.children.link(coll);coll.hide_render=False;coll.hide_viewport=False;bpy.context.view_layer.update()
rows=[]
for o in coll.all_objects:
 row={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'loc':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'hide':o.hide_render,'matrix':[list(r) for r in o.matrix_world]}
 if o.type=='MESH':
  row.update(vertices=len(o.data.vertices),polygons=len(o.data.polygons),boundsLocal=[[min(v.co[i] for v in o.data.vertices),max(v.co[i] for v in o.data.vertices)] for i in range(3)],groups=[g.name for g in o.vertex_groups],modifiers=[{'name':m.name,'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers],materials=[m.name if m else None for m in o.data.materials])
 rows.append(row)
x={'blender':bpy.app.version_string,'collection':coll.name,'objects':rows,'rootProperties':dict(root.items()),'scenes':[(s.name,s.camera.name if s.camera else None) for s in bpy.data.scenes]}
(p/'source-inspection.json').write_text(json.dumps(x,indent=2,default=str));print('INSPECTED',coll.name,len(rows))
