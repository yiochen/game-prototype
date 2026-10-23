import bpy,json,math,pathlib
from mathutils import Vector
out=pathlib.Path(__file__).parent
D={'blender':bpy.app.version_string,'scenes':[],'collections':[],'objects':[],'actions':[]}
for s in bpy.data.scenes:
 D['scenes'].append({'name':s.name,'camera':s.camera.name if s.camera else None,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'frameStart':s.frame_start,'frameEnd':s.frame_end,'fps':s.render.fps,'world':s.world.name if s.world else None})
for c in bpy.data.collections:
 if any(t in c.name.lower() for t in ['coin','pop','spark']): D['collections'].append({'name':c.name,'objects':[o.name for o in c.all_objects]})
for o in bpy.data.objects:
 if o.type=='CAMERA' or any(t in o.name.lower() for t in ['coin','pop','spark']):
  a={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'matrix':list(map(list,o.matrix_world)),'dimensions':list(o.dimensions),'collections':[c.name for c in o.users_collection],'materials':[m.name for m in o.data.materials] if o.type=='MESH' else [],'custom':{k:str(v) for k,v in o.items()}}
  if o.type=='CAMERA':a['camera']={'type':o.data.type,'orthoScale':o.data.ortho_scale,'shiftX':o.data.shift_x,'shiftY':o.data.shift_y,'lens':o.data.lens}
  if o.animation_data: a['animation']=str(o.animation_data.action)
  D['objects'].append(a)
for a in bpy.data.actions:
 if any(t in a.name.lower() for t in ['coin','pop','spark']):D['actions'].append({'name':a.name,'range':list(a.frame_range)})
(out/'source-inspection.json').write_text(json.dumps(D,indent=2))
print(json.dumps(D,indent=2))
