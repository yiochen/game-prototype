import bpy,json
from pathlib import Path
sc=bpy.data.scenes[0]; print('CAM',sc.camera.name,'scale',sc.camera.data.ortho_scale,'shift',sc.camera.data.shift_y,'matrix',list(sc.camera.matrix_world))
for name in ['barrel-wood__bulging_stave_0','barrel-wood__lid','barrel-wood__iron_band_0.67']:
 o=bpy.data.objects[name];print(name,'LOC',list(o.location));print('vertices',[(v.index,list(v.co)) for v in o.data.vertices]);print('faces',[(list(p.vertices),list(p.normal)) for p in o.data.polygons]);print('modifiers',[(m.name,m.type) for m in o.modifiers])
print('compositor',sc.use_nodes)
print('render',sc.render.engine,sc.render.resolution_x,sc.render.resolution_y,sc.render.pixel_aspect_x)
