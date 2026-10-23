import bpy,json,sys
from pathlib import Path
O=Path(__file__).parent
rows=[]
for o in bpy.data.objects:
 if 'samir' in o.name.lower() or o.type in {'CAMERA','LIGHT'}:
  rows.append({'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'parentBone':o.parent_bone,'loc':list(o.location),'rot':list(o.rotation_euler),'scale':list(o.scale),'dimensions':list(o.dimensions),'materials':[m.name for m in getattr(o.data,'materials',[])], 'modifiers':[(m.name,m.type) for m in o.modifiers], 'hide':o.hide_render,'verts':len(o.data.vertices) if o.type=='MESH' else None})
scene=bpy.context.scene
out={'blender':bpy.app.version_string,'objects':rows,'camera':scene.camera.name if scene.camera else None,'render':[scene.render.resolution_x,scene.render.resolution_y,scene.render.resolution_percentage],'sceneProps':dict(scene.items())}
(O/'editor-source-inspection.json').write_text(json.dumps(out,indent=2,default=str))
print('INSPECTED',len(rows))
