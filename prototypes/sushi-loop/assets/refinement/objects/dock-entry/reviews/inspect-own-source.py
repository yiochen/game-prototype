import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path('/Users/yiouchen/.codex/worktrees/warm-soft-catalog/game-prototype')
OUT=ROOT/'prototypes/sushi-loop/assets/refinement/objects/dock-entry/reviews'
def plain(v):
 if isinstance(v,(str,int,float,bool)) or v is None:return v
 try:return list(v)
 except:return str(v)
def bounds(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get())
 if o.type!='MESH':return None
 me=ev.to_mesh();vs=[ev.matrix_world@v.co for v in me.vertices];r={'min':[min(v[i] for v in vs) for i in range(3)],'max':[max(v[i] for v in vs) for i in range(3)],'verts':len(vs),'faces':len(me.polygons)};ev.to_mesh_clear();return r
sc=bpy.data.scenes.get('Sushi33 Production') or bpy.context.scene
if sc:bpy.context.window.scene=sc

for vl in sc.view_layers:
 def enable(lc):
  lc.exclude=False;lc.hide_viewport=False
  for child in lc.children:enable(child)
 enable(vl.layer_collection)
for c in bpy.data.collections:c.hide_viewport=False
bpy.context.view_layer.update()
r={'blend':bpy.data.filepath,'blenderVersion':bpy.app.version_string,'scenes':[{'name':s.name,'camera':s.camera.name if s.camera else None} for s in bpy.data.scenes],'scene':sc.name if sc else None,'collections':[],'cameras':[],'resources':[]}
for c in bpy.data.collections:
 if 'dock-entry' in c.name.lower() or 'dock-floor' in c.name.lower():
  c.hide_render=False;c.hide_viewport=False
  for o in c.all_objects:o.hide_set(False)
  bpy.context.view_layer.update()
  r['collections'].append({'name':c.name,'hideRender':c.hide_render,'hideViewport':c.hide_viewport,'props':{k:plain(c[k]) for k in c.keys()},'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'loc':list(o.location),'rotation':list(o.rotation_euler),'matrix':[list(row) for row in o.matrix_world],'hideRender':o.hide_render,'hideViewport':o.hide_viewport,'props':{k:plain(o[k]) for k in o.keys()},'modifiers':[{'name':m.name,'type':m.type,'width':getattr(m,'width',None),'segments':getattr(m,'segments',None)} for m in o.modifiers],'materials':[m.name if m else None for m in getattr(o.data,'materials',[])],'bounds':bounds(o)} for o in c.all_objects]})
for o in bpy.data.objects:
 if o.type=='CAMERA':r['cameras'].append({'name':o.name,'matrix':[list(row) for row in o.matrix_world],'type':o.data.type,'orthoScale':o.data.ortho_scale,'sensorFit':o.data.sensor_fit,'shift':[o.data.shift_x,o.data.shift_y],'props':{k:plain(o[k]) for k in o.keys()}})
r['render']={'size':[sc.render.resolution_x,sc.render.resolution_y],'percent':sc.render.resolution_percentage,'aspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y],'engine':sc.render.engine,'transparent':sc.render.film_transparent,'viewTransform':sc.view_settings.view_transform,'look':sc.view_settings.look,'compositor':sc.use_nodes}
mats=set(m for c in r['collections'] for o in c['objects'] for m in o['materials'] if m)
r['materials']=[{'name':m.name,'diffuseColor':list(m.diffuse_color),'useNodes':m.use_nodes,'nodes':[{'name':n.name,'type':n.type,'inputs':{i.name:plain(i.default_value) for i in n.inputs if hasattr(i,'default_value')}} for n in m.node_tree.nodes] if m.use_nodes else [],'links':[{'from':[l.from_node.name,l.from_socket.name],'to':[l.to_node.name,l.to_socket.name]} for l in m.node_tree.links] if m.use_nodes else []} for m in bpy.data.materials if m.name in mats]
r['resources']={'libraries':[{'name':x.name,'path':x.filepath} for x in bpy.data.libraries],'images':[{'name':i.name,'path':i.filepath,'packed':bool(i.packed_file),'source':i.source} for i in bpy.data.images],'lights':[{'name':o.name,'type':o.data.type,'energy':o.data.energy,'size':getattr(o.data,'size',None),'loc':list(o.location),'hideRender':o.hide_render} for o in sc.objects if o.type=='LIGHT']}
(OUT/'own-native-inspection.json').write_text(json.dumps(r,indent=2)+'\n')
print('OWN_SOURCE_AUDIT',OUT/'own-native-inspection.json')
