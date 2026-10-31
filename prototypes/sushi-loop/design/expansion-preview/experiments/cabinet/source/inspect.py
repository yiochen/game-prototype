import bpy,json,hashlib
from pathlib import Path
p=Path('/Users/yiouchen/dev/game-prototype/prototypes/sushi-loop/design/expansion-preview/experiments/cabinet')
s=bpy.context.scene
D={'blender':bpy.app.version_string,'scene':s.name,'camera':{'name':s.camera.name,'matrix':[list(r) for r in s.camera.matrix_world],'ortho':s.camera.data.ortho_scale,'shift':[s.camera.data.shift_x,s.camera.data.shift_y],'sensor_fit':s.camera.data.sensor_fit},'render':{'engine':s.render.engine,'frame':[s.render.resolution_x,s.render.resolution_y],'percentage':s.render.resolution_percentage,'pixel_aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'transparent':s.render.film_transparent,'world':s.world.name,'view_transform':s.view_settings.view_transform,'look':s.view_settings.look,'exposure':s.view_settings.exposure,'gamma':s.view_settings.gamma},'objects':[{'name':o.name,'type':o.type,'parent':o.parent.name if o.parent else None,'loc':list(o.location),'rot':list(o.rotation_euler),'scale':list(o.scale)} for o in s.objects],'lights':[{'name':o.name,'energy':o.data.energy,'size':o.data.size,'shape':o.data.shape,'matrix':[list(r) for r in o.matrix_world]} for o in s.objects if o.type=='LIGHT'],'images':[{'name':im.name,'path':im.filepath,'packed':bool(im.packed_file)} for im in bpy.data.images]}
(p/'source/independent-inspection.json').write_text(json.dumps(D,indent=2))
print(json.dumps(D))
