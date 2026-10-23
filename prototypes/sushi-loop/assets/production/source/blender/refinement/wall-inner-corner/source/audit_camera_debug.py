import bpy
from pathlib import Path
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
B=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(B/'source/round-01.blend'));s=bpy.context.scene
print('USE COMPOSITING',s.render.use_compositing,'use_nodes',s.use_nodes,'border',s.render.use_border,s.render.use_crop_to_border)
print('cam',s.camera.matrix_world[:],s.camera.data.type,s.camera.data.sensor_fit,s.camera.data.ortho_scale,s.camera.data.shift_x,s.camera.data.shift_y)
print('render',s.render.resolution_x,s.render.resolution_y,s.render.pixel_aspect_x,s.render.pixel_aspect_y)
for p in [(-.5,0,0),(0,0,0),(.5,0,0)]:print('pixel',p,world_to_camera_view(s,s.camera,Vector(p)))
for o in s.objects:
 if o.type=='MESH':
  pts=[o.matrix_world@v.co for v in o.data.vertices];print(o.name,[[min(p[i]for p in pts),max(p[i]for p in pts)]for i in range(3)])
