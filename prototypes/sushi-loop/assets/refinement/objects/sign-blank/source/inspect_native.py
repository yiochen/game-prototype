import bpy,json,os
from mathutils import Vector
from pathlib import Path
P=Path(__file__).resolve().parents[1]
source=(P/'../../../production/source/blender/revisions/b1765262bfa897ad/sushi-loop-world-library.blend').resolve()
bpy.ops.wm.open_mainfile(filepath=str(source))
print('COLLECTIONS',[(c.name,len(c.all_objects)) for c in bpy.data.collections if 'sign' in c.name.lower()])
print('OBJ',[(o.name,o.type) for o in bpy.data.objects if 'sign-blank' in o.name])
col=next(c for c in bpy.data.collections if c.name=='S33_PROP_sign-blank')
s=bpy.data.scenes.new('sign-inspection');s.collection.children.link(col)
bpy.context.window.scene=s
col.hide_viewport=False;col.hide_render=False
for o in col.all_objects:o.hide_render=False;o.hide_viewport=False;o.hide_set(False)
bpy.context.view_layer.update()
def rec(o):
 d={'name':o.name,'type':o.type,'matrix':[[float(x) for x in row] for row in o.matrix_world],'location':list(o.location),'scale':list(o.scale),'rotation':list(o.rotation_euler),'materials': [m.name if m else None for m in o.data.materials] if o.type=='MESH' else [],'modifiers':[{p.identifier:str(getattr(m,p.identifier)) for p in m.bl_rna.properties if p.identifier in ['type','width','segments','affect','offset_type','limit_method','harden_normals']} for m in o.modifiers]}
 if o.type=='MESH':
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();points=[ev.matrix_world@v.co for v in me.vertices];d.update(vertices=len(me.vertices),faces=len(me.polygons),bounds=[[min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]],smooth=[sum(p.use_smooth for p in me.polygons),len(me.polygons)],sourceVertices=[list(v.co) for v in o.data.vertices]);ev.to_mesh_clear()
 return d
out={'objects':[rec(o) for o in col.all_objects],'allCameras':[{ 'name':o.name,'matrix': [list(row) for row in o.matrix_world],'orthoScale':o.data.ortho_scale,'shiftX':o.data.shift_x,'shiftY':o.data.shift_y} for o in bpy.data.objects if o.type=='CAMERA'],'materials':{m.name:[{'type':n.type,'name':n.name,'inputs':{i.name:list(i.default_value) if hasattr(i.default_value,'__len__') else i.default_value for i in n.inputs if hasattr(i,'default_value') and (isinstance(i.default_value,(float,int)) or hasattr(i.default_value,'__len__'))}} for n in m.node_tree.nodes] if m.node_tree else [] for m in {m for o in col.all_objects if o.type=='MESH' for m in o.data.materials if m}}}
(P/'candidates/inspection/native.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2)[:18000])
