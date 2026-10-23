import bpy,json,sys,math
from pathlib import Path
out=Path(__file__).resolve().parents[1]/'evidence'
scene=next((s for s in bpy.data.scenes if any('kelp' in o.name.lower() for o in s.objects)),bpy.context.scene)
bpy.context.window.scene=scene
collections=[c for c in bpy.data.collections if 'kelp' in c.name.lower()]
for lc in bpy.context.view_layer.layer_collection.children:
 if any('kelp' in o.name.lower() for o in lc.collection.all_objects): lc.exclude=False;lc.hide_viewport=False;lc.collection.hide_viewport=False
objects={o.name:o for c in collections for o in c.all_objects}
result={'blender':bpy.app.version_string,'scene':scene.name,'savedFrame':scene.frame_current,'savedCamera':scene.camera.name,'collections':[{'name':c.name,'hide_render':c.hide_render,'hide_viewport':c.hide_viewport,'custom':dict(c.items())} for c in collections], 'objects':[],'libraries':[{'name':x.name,'filepath':x.filepath}for x in bpy.data.libraries]}
for o in objects.values():
 r={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrix': [list(r) for r in o.matrix_world],'custom':dict(o.items()),'hide_render':o.hide_render,'hide_viewport':o.hide_viewport,'modifiers':[{'type':m.type,'name':m.name}for m in o.modifiers],'constraints':[x.type for x in o.constraints]}
 if o.type=='MESH':r.update(vertices=len(o.data.vertices),faces=len(o.data.polygons),uvs=[x.name for x in o.data.uv_layers],materials=[m.name for m in o.data.materials if m],bounds=[[min((o.matrix_world@v.co)[i]for v in o.data.vertices),max((o.matrix_world@v.co)[i]for v in o.data.vertices)]for i in range(3)])
 if o.animation_data and o.animation_data.action:
  a=o.animation_data.action;r['action']={'name':a.name,'slots':[s.identifier for s in a.slots],'range':list(a.frame_range),'curves':[]}
  for layer in a.layers:
   for strip in layer.strips:
    for slot in a.slots:
     bag=strip.channelbag(slot)
     if bag:
      for f in bag.fcurves:r['action']['curves'].append({'path':f.data_path,'index':f.array_index,'keys':[[*k.co,k.interpolation]for k in f.keyframe_points]})
 result['objects'].append(r)
(out/'native-inventory.json').write_text(json.dumps(result,indent=2,default=str)+'\n')
print(json.dumps({'scene':scene.name,'collections':[(c.name,len(c.all_objects))for c in collections],'objects':len(objects),'savedCamera':scene.camera.name}))
