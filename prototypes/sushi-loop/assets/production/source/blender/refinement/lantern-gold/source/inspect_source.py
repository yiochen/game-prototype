import bpy, json, pathlib
from mathutils import Matrix, Vector
HERE=pathlib.Path(__file__).resolve().parent.parent
brief=json.loads((HERE/'brief.json').read_text())
src=(HERE/brief['source']['project']).resolve()
bpy.ops.wm.open_mainfile(filepath=str(src))
cols=[c for c in bpy.data.collections if 'lantern' in c.name.lower()]
print('COLLECTIONS',[(c.name,len(c.all_objects)) for c in cols])
col=cols[0]
scene=bpy.data.scenes.new('Lantern independent inspection')
scene.collection.children.link(col)
col.hide_viewport=False
col.hide_render=False
bpy.context.window.scene=scene
for o in col.all_objects:
 o.hide_viewport=False
 o.hide_render=False
 o.hide_set(False)
rig=json.loads((HERE/'inputs/source-rig.json').read_text())
for t in rig['clips']['idle']['actions']:
 o=bpy.data.objects[t['ownerName']];o.animation_data_create();o.animation_data.action=bpy.data.actions[t['action']]
 if t.get('slotIdentifier'):
  o.animation_data.action_slot=next(s for s in o.animation_data.action.slots if s.identifier==t['slotIdentifier'])
scene.frame_set(1)
bpy.context.view_layer.update()
def vec(v): return [round(float(x),7) for x in v]
def mat(m): return [vec(v) for v in m]
records=[]
for o in col.all_objects:
 r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'loc':vec(o.location),'rot':vec(o.rotation_euler),'scale':vec(o.scale),'matrixWorld':mat(o.matrix_world),'dimensions':vec(o.dimensions),'modifiers':[{ 'name':m.name,'type':m.type,**({'width':m.width,'segments':m.segments} if m.type=='BEVEL' else {})} for m in o.modifiers],'action':o.animation_data.action.name if o.animation_data and o.animation_data.action else None}
 if o.type=='MESH':
  r.update(vertices=len(o.data.vertices),edges=len(o.data.edges),polygons=len(o.data.polygons),smooth=sum(p.use_smooth for p in o.data.polygons),bounds=[vec(o.matrix_world@Vector(c)) for c in o.bound_box],materials=[])
  for m in o.data.materials:
   r['materials'].append({'name':m.name,'diffuse':vec(m.diffuse_color),'nodes':[{'name':n.name,'type':n.type,'inputs':{s.name:vec(s.default_value) if hasattr(s.default_value,'__len__') else s.default_value for s in n.inputs if hasattr(s,'default_value') and (isinstance(s.default_value,(int,float)) or hasattr(s.default_value,'__len__'))}} for n in m.node_tree.nodes] if m.use_nodes else []})
 records.append(r)
print([(o['name'],o['matrixWorld'],o['action']) for o in records])
(HERE/'source/source-inspection.json').write_text(json.dumps({'source':str(src),'collection':col.name,'objects':records},indent=2,default=str))
