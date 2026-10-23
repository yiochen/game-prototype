import bpy,json,math,hashlib
from pathlib import Path
out=Path(__file__).resolve().parent
root=bpy.data.objects['S33 production concept pink-coral root']
sc=next(s for s in bpy.data.scenes if root.name in s.objects)
col=next(c for c in sc.collection.children if root in list(c.all_objects))
bpy.context.window.scene=sc
for c in sc.collection.children:c.hide_render=c!=col
items=[]
for o in col.all_objects:
 d={'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'location':list(o.location),'rotation':list(o.rotation_euler),'scale':list(o.scale),'modifiers':[m.type for m in o.modifiers]}
 if o.type=='MESH':d.update(vertices=len(o.data.vertices),faces=len(o.data.polygons),smooth=sum(p.use_smooth for p in o.data.polygons),materials=[m.name for m in o.data.materials],bounds=[[min((o.matrix_world@v.co)[i] for v in o.data.vertices) for i in range(3)],[max((o.matrix_world@v.co)[i] for v in o.data.vertices) for i in range(3)]])
 items.append(d)
r={'blender':bpy.app.version_string,'scene':sc.name,'collection':col.name,'camera':{'name':sc.camera.name,'matrix':[list(x) for x in sc.camera.matrix_world],'orthoScale':sc.camera.data.ortho_scale,'shift':[sc.camera.data.shift_x,sc.camera.data.shift_y],'render':[sc.render.resolution_x,sc.render.resolution_y],'pixelAspect':[sc.render.pixel_aspect_x,sc.render.pixel_aspect_y]},'root':root.name,'objects':items}
(out/'original-native-inspection.json').write_text(json.dumps(r,indent=2)+'\n')
print(json.dumps(r))
