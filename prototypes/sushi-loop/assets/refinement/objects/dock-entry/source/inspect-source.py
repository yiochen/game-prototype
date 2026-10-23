import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
B=Path(__file__).resolve().parents[1]
source=B.parents[1]/'backups/b1765262bfa897ad-sushi-loop-world-library.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
cols=[c for c in bpy.data.collections if 'dock-entry' in c.name]
for c in cols:
 c.hide_viewport=False;c.hide_render=False
 for o in c.all_objects:o.hide_viewport=False;o.hide_set(False)
sc=bpy.data.scenes.new('Entry independent source inspection')
for c in cols:sc.collection.children.link(c)
bpy.context.window.scene=sc
bpy.context.view_layer.update()
r={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'collections':[],'activeCamera':None}
for c in cols:
 o=[]
 for x in c.all_objects:
  rec={'name':x.name,'type':x.type,'location':list(x.location),'scale':list(x.scale),'rotation':list(x.rotation_euler),'matrix': [list(a) for a in x.matrix_world],'parent':x.parent.name if x.parent else None,'custom':dict(x.items())}
  if x.type=='MESH':
   pts=[x.matrix_world@Vector(p) for p in x.bound_box]
   rec.update(vertices=len(x.data.vertices),polygons=len(x.data.polygons),bounds=[[min(p[i] for p in pts) for i in range(3)],[max(p[i] for p in pts) for i in range(3)]],materials=[m.name for m in x.data.materials])
  o.append(rec)
 r['collections'].append({'name':c.name,'objects':o})
if bpy.context.scene.camera:r['activeCamera']={'name':bpy.context.scene.camera.name,'matrix':[list(a) for a in bpy.context.scene.camera.matrix_world],'data':bpy.context.scene.camera.data.ortho_scale}
(B/'source/initial-native-inspection.json').write_text(json.dumps(r,indent=2,default=str))
print(json.dumps(r,indent=2,default=str))
