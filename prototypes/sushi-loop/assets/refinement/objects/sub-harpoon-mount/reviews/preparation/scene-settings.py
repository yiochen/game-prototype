import bpy,json,pathlib
p=pathlib.Path(__file__).parent
rows=[]
for s in bpy.data.scenes:
 rows.append({'name':s.name,'camera':s.camera.name if s.camera else None,'engine':s.render.engine,'resolution':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage],'aspect':[s.render.pixel_aspect_x,s.render.pixel_aspect_y],'transparent':s.render.film_transparent,'filter':s.render.filter_size,'world':s.world.name if s.world else None,'view':[s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma],'compositing':s.use_nodes,'objects':len(s.objects)})
cams=[]
for o in bpy.data.objects:
 if o.type=='CAMERA':cams.append({'name':o.name,'loc':list(o.location),'matrix':[list(r) for r in o.matrix_world],'ortho':o.data.ortho_scale,'shift':[o.data.shift_x,o.data.shift_y]})
lights=[]
for o in bpy.data.objects:
 if o.type=='LIGHT':lights.append({'name':o.name,'loc':list(o.location),'rot':list(o.rotation_euler),'energy':o.data.energy,'size':o.data.size,'type':o.data.type,'color':list(o.data.color),'hidden':o.hide_render})
(p/'source-scene-settings.json').write_text(json.dumps({'scenes':rows,'cameras':cams,'lights':lights},indent=2)+'\n')
