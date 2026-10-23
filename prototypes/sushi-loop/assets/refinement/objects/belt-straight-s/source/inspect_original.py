import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
b=json.loads((P/'brief.json').read_text()); src=(P/b['source']['project']).resolve()
bpy.ops.wm.open_mainfile(filepath=str(src)); sc=bpy.context.scene
for c in bpy.data.collections:c.hide_render=False;c.hide_viewport=False
for o in bpy.data.objects:o.hide_set(False)
def unhide(l):
 l.exclude=False;l.hide_viewport=False
 for x in l.children:unhide(x)
unhide(bpy.context.view_layer.layer_collection);bpy.context.view_layer.update(); dg=bpy.context.evaluated_depsgraph_get();dg.update()
cols=[c for c in bpy.data.collections if 'belt-straight-s' in c.name]
result={'source':str(src),'sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'collections':[]}
for c in cols:
 cd={'name':c.name,'objects':[]}
 for o in c.all_objects:
  od={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'matrixWorld':[list(r) for r in o.matrix_world]}
  if o.type=='MESH':
   me=o.evaluated_get(dg).to_mesh(); ps=[o.matrix_world@v.co for v in me.vertices]
   od.update({'vertices':len(me.vertices),'polygons':len(me.polygons),'bounds':[[min(p[i] for p in ps) for i in range(3)],[max(p[i] for p in ps) for i in range(3)]], 'materials':[x.name for x in o.data.materials], 'uv':[[list(v.uv) for v in u.data] for u in o.data.uv_layers], 'modifiers':[{'type':m.type,'name':m.name} for m in o.modifiers]})
   o.evaluated_get(dg).to_mesh_clear()
  cd['objects'].append(od)
 result['collections'].append(cd)
mats={m.name:m for c in cols for o in c.all_objects if o.type=='MESH' for m in o.data.materials if m}
result['materials']={}
for name,m in mats.items():
 nt=m.node_tree
 md={'nodes':[{'name':n.name,'type':n.bl_idname,'inputs':{s.name:list(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value for s in n.inputs if hasattr(s,'default_value')},'outputs':{s.name:list(s.default_value) if hasattr(s.default_value,'__len__') and not isinstance(s.default_value,str) else s.default_value for s in n.outputs if hasattr(s,'default_value')}} for n in nt.nodes] if nt else []}
 if nt:
  md['links']=[{'from':l.from_node.name+'.'+l.from_socket.name,'to':l.to_node.name+'.'+l.to_socket.name} for l in nt.links]
  ad=nt.animation_data
  if ad and ad.action:
   a=ad.action;md['action']={'name':a.name,'slots':[s.identifier for s in a.slots],'curves':[]}
   for layer in a.layers:
    for strip in layer.strips:
     for bag in strip.channelbags:
      for f in bag.fcurves:md['action']['curves'].append({'path':f.data_path,'index':f.array_index,'keys':[[k.co.x,k.co.y,k.interpolation] for k in f.keyframe_points]})
 result['materials'][name]=md
result['cameras']=[{'name':o.name,'matrix':[list(r) for r in o.matrix_world],'ortho':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y]} for o in bpy.data.objects if o.type=='CAMERA']
(P/'source/independent-source-inspection.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'collections':[{'name':x['name'],'objects':[(o['name'],o.get('rotation'),o.get('bounds')) for o in x['objects']]} for x in result['collections']], 'actions':{k:v.get('action') for k,v in result['materials'].items() if v.get('action')}},indent=2))
